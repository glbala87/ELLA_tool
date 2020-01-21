from typing import List, Optional, Set, Dict
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.elements import BooleanClauseList, BinaryExpression
from sqlalchemy.sql.schema import Table
from sqlalchemy.sql.selectable import Alias
from sqlalchemy import or_, and_, text, func

from vardb.datamodel import sample, annotationshadow

from datalayer.allelefilter.denovo_probability import denovo_probability
from datalayer.allelefilter.genotypetable import (
    get_genotype_temp_table,
    extend_genotype_table_with_allele,
)

# X chromosome PAR regions for GRCh37 (1-based)
PAR1_START = 60001
PAR1_END = 2_699_520
PAR2_START = 154_931_044
PAR2_END = 155_260_560


class SegregationFilter(object):
    def __init__(self, session: Session, config):
        self.session = session
        self.config = config

    def denovo_p_value(
        self, allele_ids, genotype_table, proband_sample_id, father_sample_id, mother_sample_id
    ):
        assert all(
            [
                f"{sample_id}_gl" in genotype_table.columns.keys()
                for sample_id in [proband_sample_id, father_sample_id, mother_sample_id]
            ]
        ), "get_genotype_temp_table needs to be created with genotypesampledata_extra={'gl': 'genotype_likelihood'} for this function"

        genotype_with_allele_table = extend_genotype_table_with_allele(self.session, genotype_table)
        genotype_with_allele_table = genotype_with_allele_table.subquery()
        x_minus_par_filter = self.get_x_minus_par_filter(genotype_with_allele_table)

        denovo_mode_map = {
            "Xmale": {"Reference": 0, "Homozygous": 1},
            "default": {"Reference": 0, "Heterozygous": 1, "Homozygous": 2},
        }

        def _compute_denovo_probabilities(genotype_with_allele_table, x_minus_par=False):
            dp = dict()
            for row in genotype_with_allele_table:
                if not all(
                    [
                        getattr(row, f"{proband_sample_id}_gl"),
                        getattr(row, f"{father_sample_id}_gl"),
                        getattr(row, f"{mother_sample_id}_gl"),
                    ]
                ):
                    dp[row.allele_id] = "-"
                    continue

                if x_minus_par and getattr(row, f"{proband_sample_id}_sex") == "Male":
                    denovo_mode = [
                        denovo_mode_map["Xmale"][getattr(row, f"{father_sample_id}_type")],
                        denovo_mode_map["Xmale"][getattr(row, f"{mother_sample_id}_type")],
                        denovo_mode_map["Xmale"][getattr(row, f"{proband_sample_id}_type")],
                    ]
                else:
                    denovo_mode = [
                        denovo_mode_map["default"][getattr(row, f"{father_sample_id}_type")],
                        denovo_mode_map["default"][getattr(row, f"{mother_sample_id}_type")],
                        denovo_mode_map["default"][getattr(row, f"{proband_sample_id}_type")],
                    ]

                # It should not come up as a denovo candidate if either mother or father has the same called genotype
                assert denovo_mode.count(denovo_mode[2]) == 1

                p = denovo_probability(
                    getattr(row, f"{proband_sample_id}_gl"),
                    getattr(row, f"{father_sample_id}_gl"),
                    getattr(row, f"{mother_sample_id}_gl"),
                    x_minus_par,
                    getattr(row, f"{proband_sample_id}_sex") == "Male",
                    denovo_mode,
                )
                dp[row.allele_id] = p
            return dp

        genotype_with_denovo_allele_table = self.session.query(*genotype_with_allele_table.c)

        # Compute denovo probabilities for autosomal and x-linked regions separately
        denovo_probabilities = dict()
        denovo_probabilities.update(
            _compute_denovo_probabilities(
                genotype_with_denovo_allele_table.filter(~x_minus_par_filter), False
            )
        )
        denovo_probabilities.update(
            _compute_denovo_probabilities(
                genotype_with_denovo_allele_table.filter(x_minus_par_filter), True
            )
        )

        return denovo_probabilities

    def get_x_minus_par_filter(self, genotype_with_allele_table: Alias) -> BooleanClauseList:
        """
        PAR1 X:60001-2699520 (GRCh37)
        PAR2 X:154931044-155260560 (GRCh37)
        """

        # Only GRCh37 is supported for now
        assert (
            not self.session.query(genotype_with_allele_table.c.allele_id)
            .filter(genotype_with_allele_table.c.genome_reference != "GRCh37")
            .first()
        )

        x_minus_par_filter = and_(
            genotype_with_allele_table.c.chromosome == "X",
            # Allele table has 0-indexed positions
            or_(
                # Before PAR1
                genotype_with_allele_table.c.open_end_position <= PAR1_START,
                # Between PAR1 and PAR2
                and_(
                    genotype_with_allele_table.c.start_position > PAR1_END,
                    genotype_with_allele_table.c.open_end_position <= PAR2_START,
                ),
                # After PAR2
                genotype_with_allele_table.c.start_position > PAR2_END,
            ),
        )

        return x_minus_par_filter

    def denovo(
        self,
        genotype_table: Table,
        proband_sample_id: int,
        father_sample_id: int,
        mother_sample_id: int,
    ) -> Set[int]:
        """
        Denovo mutations

        Based on denovo classification from FILTUS (M. Vigeland et al):
        https://academic.oup.com/bioinformatics/article/32/10/1592/1743466

        Denovo patterns:
        Autosomal:
            - 0/0 + 0/0 = 0/1
            - 0/0 + 0/0 = 1/1
            - 0/0 + 0/1 = 1/1
            - 0/1 + 0/0 = 1/1
        X-linked, child is boy:
            - 0 + 0/0 = 1
        X-linked, child is girl:
            - 0 + 0/0 = 0/1
            - 0 + 0/0 = 1/1
            - 0 + 0/1 = 1/1

        A variant is treated as X-linked in this context only if it is
        located outside of the pseudoautosomal regions PAR1 and PAR2 on the X chromosome.

        Note followig special conditions, which are _not included_ in the results:
        - Missing genotype in father or mother (i.e. no coverage).
        - A male member is given as heterozygous for an X-linked variant.

        If configured, the denovo results are filtered on allele count to remove technical
        artifacts or likely non-pathogenic variants.

        """

        if not mother_sample_id or not father_sample_id:
            return set()

        genotype_with_allele_table = extend_genotype_table_with_allele(self.session, genotype_table)
        genotype_with_allele_table = genotype_with_allele_table.subquery(
            "genotype_with_allele_table"
        )
        x_minus_par_filter = self.get_x_minus_par_filter(genotype_with_allele_table)

        denovo_allele_ids = self.session.query(genotype_with_allele_table.c.allele_id).filter(
            # Exclude no coverage
            getattr(genotype_with_allele_table.c, f"{father_sample_id}_type") != "No coverage",
            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_type") != "No coverage",
            or_(
                # Autosomal
                and_(
                    ~x_minus_par_filter,
                    or_(
                        # 0/0 + 0/0 = 0/1
                        # 0/0 + 0/0 = 1/1
                        and_(
                            or_(
                                getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type")
                                == "Homozygous",
                                getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type")
                                == "Heterozygous",
                            ),
                            getattr(genotype_with_allele_table.c, f"{father_sample_id}_type")
                            == "Reference",
                            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_type")
                            == "Reference",
                        ),
                        # 0/0 + 0/1 = 1/1
                        # 0/1 + 0/0 = 1/1
                        and_(
                            getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type")
                            == "Homozygous",
                            or_(
                                and_(
                                    getattr(
                                        genotype_with_allele_table.c, f"{father_sample_id}_type"
                                    )
                                    == "Heterozygous",
                                    getattr(
                                        genotype_with_allele_table.c, f"{mother_sample_id}_type"
                                    )
                                    == "Reference",
                                ),
                                and_(
                                    getattr(
                                        genotype_with_allele_table.c, f"{father_sample_id}_type"
                                    )
                                    == "Reference",
                                    getattr(
                                        genotype_with_allele_table.c, f"{mother_sample_id}_type"
                                    )
                                    == "Heterozygous",
                                ),
                            ),
                        ),
                    ),
                ),
                # X-linked
                and_(
                    x_minus_par_filter,
                    or_(
                        # Male proband
                        and_(
                            # 0 + 0/0 = 1
                            getattr(genotype_with_allele_table.c, f"{proband_sample_id}_sex")
                            == "Male",
                            getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type")
                            == "Homozygous",
                            getattr(genotype_with_allele_table.c, f"{father_sample_id}_type")
                            == "Reference",
                            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_type")
                            == "Reference",
                        ),
                        # Female proband
                        and_(
                            getattr(genotype_with_allele_table.c, f"{proband_sample_id}_sex")
                            == "Female",
                            or_(
                                # 0 + 0/0 = 0/1
                                # 0 + 0/0 = 1/1
                                and_(
                                    or_(
                                        getattr(
                                            genotype_with_allele_table.c,
                                            f"{proband_sample_id}_type",
                                        )
                                        == "Homozygous",
                                        getattr(
                                            genotype_with_allele_table.c,
                                            f"{proband_sample_id}_type",
                                        )
                                        == "Heterozygous",
                                    ),
                                    getattr(
                                        genotype_with_allele_table.c, f"{father_sample_id}_type"
                                    )
                                    == "Reference",
                                    getattr(
                                        genotype_with_allele_table.c, f"{mother_sample_id}_type"
                                    )
                                    == "Reference",
                                ),
                                # 0 + 0/1 = 1/1
                                and_(
                                    getattr(
                                        genotype_with_allele_table.c, f"{proband_sample_id}_type"
                                    )
                                    == "Homozygous",
                                    getattr(
                                        genotype_with_allele_table.c, f"{father_sample_id}_type"
                                    )
                                    == "Reference",
                                    getattr(
                                        genotype_with_allele_table.c, f"{mother_sample_id}_type"
                                    )
                                    == "Heterozygous",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

        denovo_result = set([a[0] for a in denovo_allele_ids.all()])
        return denovo_result

    def inherited_mosaicism(
        self,
        genotype_table: Table,
        proband_sample_id: int,
        father_sample_id: int,
        mother_sample_id: int,
    ) -> Set[int]:
        """
        Inherited mosaicism

        Checks whether there are variants that is inherited from a parent with possible mosasicm.

        - In autosomal regions:
            - Proband has variant
            - Father or mother has allele_ratio between given heterozygous thresholds
        - In X:
            - Proband has variant
            - Father or mother has allele_ratio between given (mother: heterozygous, father: homozygous) thresholds
        """

        assert all(
            [
                f"{sample_id}_ar" in genotype_table.columns.keys()
                for sample_id in [proband_sample_id, father_sample_id, mother_sample_id]
            ]
        ), "get_genotype_temp_table needs to be created with genotypesampledata_extra={'ar': 'allele_ratio'} for this function"

        MOSAICISM_HETEROZYGOUS_THRESHOLD = [0, 0.3]  # (start, end]
        MOSAICISM_HOMOZYGOUS_THRESHOLD = [0, 0.8]  # (start, end]

        NON_MOSAICISM_THRESHOLD = 0.3

        if not mother_sample_id or not father_sample_id:
            return set()

        genotype_with_allele_table = extend_genotype_table_with_allele(self.session, genotype_table)
        genotype_with_allele_table = genotype_with_allele_table.subquery(
            "genotype_with_allele_table"
        )
        x_minus_par_filter = self.get_x_minus_par_filter(genotype_with_allele_table)

        inherited_mosacism_allele_ids = self.session.query(
            genotype_with_allele_table.c.allele_id
        ).filter(
            # Exclude no coverage
            func.coalesce(
                getattr(genotype_with_allele_table.c, f"{father_sample_id}_type"), "No coverage"
            )
            != "No coverage",
            func.coalesce(
                getattr(genotype_with_allele_table.c, f"{mother_sample_id}_type"), "No coverage"
            )
            != "No coverage",
            or_(
                # Autosomal
                # Proband heterozygous, parent with mosaicism ratio
                and_(
                    ~x_minus_par_filter,
                    getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type")
                    == "Heterozygous",
                    getattr(genotype_with_allele_table.c, f"{proband_sample_id}_ar")
                    > NON_MOSAICISM_THRESHOLD,
                    # We don't check the genotype for the parents,
                    # as in this case we care more about the ratio than the called result
                    or_(
                        # Father mosaicism
                        and_(
                            getattr(genotype_with_allele_table.c, f"{father_sample_id}_ar")
                            > MOSAICISM_HETEROZYGOUS_THRESHOLD[0],
                            getattr(genotype_with_allele_table.c, f"{father_sample_id}_ar")
                            <= MOSAICISM_HETEROZYGOUS_THRESHOLD[1],
                        ),
                        # Mother mosaicism
                        and_(
                            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_ar")
                            > MOSAICISM_HETEROZYGOUS_THRESHOLD[0],
                            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_ar")
                            <= MOSAICISM_HETEROZYGOUS_THRESHOLD[1],
                        ),
                    ),
                ),
                # X-linked
                # Treat father mosacism different than mothers
                and_(
                    x_minus_par_filter,
                    or_(
                        getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type")
                        == "Heterozygous",
                        getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type")
                        == "Homozygous",
                    ),
                    getattr(genotype_with_allele_table.c, f"{proband_sample_id}_ar")
                    > NON_MOSAICISM_THRESHOLD,
                    or_(
                        # Father mosaicism
                        and_(
                            getattr(genotype_with_allele_table.c, f"{father_sample_id}_ar")
                            > MOSAICISM_HOMOZYGOUS_THRESHOLD[0],
                            getattr(genotype_with_allele_table.c, f"{father_sample_id}_ar")
                            <= MOSAICISM_HOMOZYGOUS_THRESHOLD[1],
                        ),
                        # Mother mosaicism
                        and_(
                            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_ar")
                            > MOSAICISM_HETEROZYGOUS_THRESHOLD[0],
                            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_ar")
                            <= MOSAICISM_HETEROZYGOUS_THRESHOLD[1],
                        ),
                    ),
                ),
            ),
        )

        inherited_mosaicism_result = set([a[0] for a in inherited_mosacism_allele_ids.all()])
        return inherited_mosaicism_result

    def autosomal_recessive_homozygous(
        self,
        genotype_table: Table,
        proband_sample_id: int,
        father_sample_id: Optional[int],
        mother_sample_id: Optional[int],
        affected_sibling_sample_ids: Optional[List[int]] = None,
        unaffected_sibling_sample_ids: Optional[List[int]] = None,
    ) -> Set[int]:
        """
        Autosomal recessive transmission

        Autosomal recessive:
        A variant must be:
        - Homozygous in proband
        - Heterozygous in both parents
        - Not homozygous in unaffected siblings
        - Homozygous in affected siblings
        - In chromosome 1-22 or X pseudoautosomal region (PAR1, PAR2)
        """

        if not father_sample_id or not mother_sample_id:
            return set()

        genotype_with_allele_table = extend_genotype_table_with_allele(self.session, genotype_table)
        genotype_with_allele_table = genotype_with_allele_table.subquery(
            "genotype_with_allele_table"
        )
        x_minus_par_filter = self.get_x_minus_par_filter(genotype_with_allele_table)

        filters = [
            getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type") == "Homozygous",
            getattr(genotype_with_allele_table.c, f"{father_sample_id}_type") == "Heterozygous",
            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_type") == "Heterozygous",
            ~x_minus_par_filter,  # In chromosome 1-22 or in X PAR
        ]
        if unaffected_sibling_sample_ids:
            filters += [
                func.coalesce(getattr(genotype_with_allele_table.c, f"{s}_type"), "Reference")
                != "Homozygous"
                for s in unaffected_sibling_sample_ids
            ]

        if affected_sibling_sample_ids:
            filters += [
                getattr(genotype_with_allele_table.c, f"{s}_type") == "Homozygous"
                for s in affected_sibling_sample_ids
            ]

        autosomal_allele_ids = self.session.query(genotype_with_allele_table.c.allele_id).filter(
            *filters
        )

        return set([a[0] for a in autosomal_allele_ids])

    def xlinked_recessive_homozygous(
        self,
        genotype_table: Table,
        proband_sample_id: int,
        father_sample_id: Optional[int],
        mother_sample_id: Optional[int],
        affected_sibling_sample_ids: Optional[List[int]] = None,
        unaffected_sibling_sample_ids: Optional[List[int]] = None,
    ) -> Set[int]:
        """
        X-linked recessive

        A variant must be:
        - Homozygous in proband (for girls this requires a denovo, but still valid case)
        - Heterozygous in mother
        - Not present in father
        - Not homozygous in unaffected siblings
        - Homozygous in affected siblings
        - In chromosome X, but not pseudoautosomal region (PAR1, PAR2)
        """

        if not father_sample_id or not mother_sample_id:
            return set()

        genotype_with_allele_table = extend_genotype_table_with_allele(self.session, genotype_table)
        genotype_with_allele_table = genotype_with_allele_table.subquery(
            "genotype_with_allele_table"
        )
        x_minus_par_filter = self.get_x_minus_par_filter(genotype_with_allele_table)

        filters = [
            getattr(genotype_with_allele_table.c, f"{proband_sample_id}_type") == "Homozygous",
            getattr(genotype_with_allele_table.c, f"{father_sample_id}_type") == "Reference",
            getattr(genotype_with_allele_table.c, f"{mother_sample_id}_type") == "Heterozygous",
            x_minus_par_filter,  # In X chromosome (minus PAR)
        ]
        if unaffected_sibling_sample_ids:
            filters += [
                func.coalesce(getattr(genotype_with_allele_table.c, f"{s}_type"), "Reference")
                != "Homozygous"
                for s in unaffected_sibling_sample_ids
            ]

        if affected_sibling_sample_ids:
            filters += [
                getattr(genotype_with_allele_table.c, f"{s}_type") == "Homozygous"
                for s in affected_sibling_sample_ids
            ]

        xlinked_allele_ids = self.session.query(genotype_with_allele_table.c.allele_id).filter(
            *filters
        )

        return set([a[0] for a in xlinked_allele_ids])

    def compound_heterozygous(
        self,
        genotype_table: Table,
        proband_sample_id: int,
        father_sample_id: Optional[int] = None,
        mother_sample_id: Optional[int] = None,
        affected_sibling_sample_ids: Optional[List[int]] = None,
        unaffected_sibling_sample_ids: Optional[List[int]] = None,
    ) -> Set[int]:
        """
        Autosomal recessive transmission: Compound heterozygous

        Based on rule set from:
        Filtering for compound heterozygous sequence variant in non-consanguineous pedigrees.
        (Kamphans T et al. (2013), PLoS ONE: 8(8), e70151)

        1. A variant has to be in a heterozygous state in all affected individuals.

        2. A variant must not occur in a homozygous state in any of the unaffected
        individuals.

        3. A variant that is heterozygous in an affected child must be heterozygous
        in exactly one of the parents.

        4. A gene must have two or more heterozygous variants in each of the
        affected individuals.

        5. There must be at least one variant transmitted from the paternal side
        and one transmitted from the maternal side.

        For the second part of the third rule - "in exactly one of the parents" - note
        this excerpt from article:
        "Rule 3b is applicable only if we assume that no de novo mutations occurred.
        The number of de novo mutations is estimated to be below five per exome per generation [2], [3],
        thus, the likelihood that an individual is compound heterozygous and at least one
        of these mutations arose de novo is low.
        If more than one family member is affected, de novo mutations are even orders
        of magnitudes less likely as a recessive disease cause.
        On the other hand, excluding these variants from the further analysis helps to
        remove many sequencing artifacts. In linkage analysis for example it is common practice
        of data cleaning to exclude variants as Mendelian errors if they cannot be explained
        by Mendelian inheritance."

        :note: Alleles with 'No coverage' in either parent are not included.
        """

        assert proband_sample_id

        sample_ids = [proband_sample_id]
        affected_sample_ids = [proband_sample_id]
        unaffected_sample_ids = []
        if father_sample_id:
            sample_ids.append(father_sample_id)
            unaffected_sample_ids.append(father_sample_id)
        if mother_sample_id:
            sample_ids.append(mother_sample_id)
            unaffected_sample_ids.append(mother_sample_id)
        if affected_sibling_sample_ids:
            sample_ids += affected_sibling_sample_ids
            affected_sample_ids += affected_sibling_sample_ids
        if unaffected_sibling_sample_ids:
            sample_ids += unaffected_sibling_sample_ids
            unaffected_sample_ids += unaffected_sibling_sample_ids

        # If only proband, we are not able to compute compound heterozygous candidate alleles.
        if len(sample_ids) == 1:
            return set()

        # Get candidates for compound heterozygosity. Covers the following rules:
        # 1. A variant has to be in a heterozygous state in all affected individuals.
        # 2. A variant must not occur in a homozygous state in any of the unaffected individuals.
        # 3. A variant that is heterozygous in an affected child must be
        #    heterozygous in exactly one of the parents.

        compound_candidates_filters: List[BinaryExpression] = []
        # Heterozygous in affected
        compound_candidates_filters += [
            getattr(genotype_table.c, f"{s}_type") == "Heterozygous" for s in affected_sample_ids
        ]
        # Not homozygous in unaffected
        compound_candidates_filters += [
            # Normally null would be included in below filter,
            # set as Reference to make comparison work
            func.coalesce(getattr(genotype_table.c, f"{s}_type"), "Reference") != "Homozygous"
            for s in unaffected_sample_ids
        ]
        if father_sample_id and mother_sample_id:
            # Heterozygous in _exactly one_ parent.
            # Note: This will also exclude any alleles with 'No coverage' in either parent.
            compound_candidates_filters.append(
                or_(
                    and_(
                        getattr(genotype_table.c, f"{father_sample_id}_type") == "Heterozygous",
                        getattr(genotype_table.c, f"{mother_sample_id}_type") == "Reference",
                    ),
                    and_(
                        getattr(genotype_table.c, f"{father_sample_id}_type") == "Reference",
                        getattr(genotype_table.c, f"{mother_sample_id}_type") == "Heterozygous",
                    ),
                )
            )

        compound_candidates = (
            self.session.query(
                genotype_table.c.allele_id,
                *[getattr(genotype_table.c, f"{s}_type") for s in sample_ids],
            )
            .filter(*compound_candidates_filters)
            .subquery("compound_candidates")
        )

        # Group per gene and get the gene symbols with >= 2 candidates.
        #
        # Covers the following rules:
        # 4. A gene must have two or more heterozygous variants in each of the affected individuals.
        # 5. There must be at least one variant transmitted from the paternal side
        #    and one transmitted from the maternal side.
        #
        # Note: We use symbols instead of HGNC id since some
        #  symbols have no id in the annotation data
        #  One allele can be in several genes, and the gene symbol set is more extensive than only
        #  the symbols having HGNC ids so it should be safer to user.
        #
        # candidates_with_genes example:
        # ----------------------------------------------------------------------
        # | allele_id | Proband_type | Father_type  | Mother_type   | symbol   |
        # ----------------------------------------------------------------------
        # | 6006      | Heterozygous | Heterozygous | Reference     | KIAA0586 |
        # | 6005      | Heterozygous | Reference    | Heterozygous  | KIAA0586 |
        # | 6004      | Heterozygous | Reference    | Heterozygous  | KIAA0586 |
        # | 5528      | Heterozygous | Heterozygous | Reference     | TUBA1A   |
        # | 5529      | Heterozygous | Heterozygous | Reference     | TUBA1A   |
        #
        # In the above example, 6004, 6005 and 6006 satisfy the rules.

        filters = []
        if "inclusion_regex" in self.config["transcripts"]:
            filters.append(
                text("annotationshadowtranscript.transcript ~ :reg").params(
                    reg=self.config["transcripts"]["inclusion_regex"]
                )
            )
        candidates_with_genes_columns = [
            compound_candidates.c.allele_id,
            annotationshadow.AnnotationShadowTranscript.symbol,
        ]
        if father_sample_id and mother_sample_id:
            candidates_with_genes_columns += [
                getattr(compound_candidates.c, f"{father_sample_id}_type"),
                getattr(compound_candidates.c, f"{mother_sample_id}_type"),
            ]
        candidates_with_genes = (
            self.session.query(*candidates_with_genes_columns)
            .join(
                annotationshadow.AnnotationShadowTranscript,
                compound_candidates.c.allele_id
                == annotationshadow.AnnotationShadowTranscript.allele_id,
            )
            .filter(*filters)
            .distinct()
        )

        candidates_with_genes = candidates_with_genes.subquery("candidates_with_genes")

        # General criteria, 2 or more alleles in this gene
        # (rule 1 above covered that they are heterozygous in affected)
        compound_heterozygous_symbols_having = [func.count(candidates_with_genes.c.allele_id) > 1]

        # If parents, heterozygous in both
        if father_sample_id and mother_sample_id:
            compound_heterozygous_symbols_having += [
                # bool_or: at least one allele in this gene is 'Heterozygous'
                func.bool_or(
                    getattr(candidates_with_genes.c, f"{father_sample_id}_type") == "Heterozygous"
                ),
                func.bool_or(
                    getattr(candidates_with_genes.c, f"{mother_sample_id}_type") == "Heterozygous"
                ),
            ]
        compound_heterozygous_symbols = (
            self.session.query(candidates_with_genes.c.symbol)
            .group_by(candidates_with_genes.c.symbol)
            .having(and_(*compound_heterozygous_symbols_having))
        )

        compound_heterozygous_allele_ids = (
            self.session.query(candidates_with_genes.c.allele_id)
            .filter(candidates_with_genes.c.symbol.in_(compound_heterozygous_symbols))
            .distinct()
        )

        return set([a[0] for a in compound_heterozygous_allele_ids.all()])

    def no_coverage_father_mother(self, genotype_table, father_sample_id, mother_sample_id):

        if not father_sample_id or not mother_sample_id:
            return set()

        no_coverage_allele_ids = self.session.query(genotype_table.c.allele_id).filter(
            or_(
                getattr(genotype_table.c, f"{father_sample_id}_type") == "No coverage",
                getattr(genotype_table.c, f"{mother_sample_id}_type") == "No coverage",
            )
        )

        return set([a[0] for a in no_coverage_allele_ids])

    def homozygous_unaffected_siblings(
        self, genotype_table: Table, proband_sample: str, unaffected_sibling_sample_ids: List[str]
    ) -> Set[int]:
        """
        Checks whether a homozygous variant in proband is also homozgyous in unaffected sibling.

        Returns all variants that are also homozygous in unaffected siblings.
        """

        # If no unaffected, we'll have no alleles in the result
        if not unaffected_sibling_sample_ids:
            return set()

        filters = list()
        for s in [proband_sample] + unaffected_sibling_sample_ids:
            filters.append(getattr(genotype_table.c, f"{s}_type") == "Homozygous")

        homozygous_unaffected_result = self.session.query(genotype_table.c.allele_id).filter(
            *filters
        )

        return set([a[0] for a in homozygous_unaffected_result.all()])

    def get_family_ids(self, analysis_id):
        family_ids = (
            self.session.query(sample.Sample.family_id)
            .filter(
                sample.Sample.analysis_id == analysis_id,
                sample.Sample.proband.is_(True),
                ~sample.Sample.family_id.is_(None),
            )
            .all()
        )

        return [fid[0] for fid in family_ids]

    def get_family_sample_ids(self, analysis_id, family_id):
        sample_ids = (
            self.session.query(sample.Sample.id)
            .filter(sample.Sample.analysis_id == analysis_id, sample.Sample.family_id == family_id)
            .all()
        )

        return [sid[0] for sid in sample_ids]

    def get_proband_sample(self, analysis_id, sample_family_id):
        proband_sample = (
            self.session.query(sample.Sample)
            .filter(
                sample.Sample.proband.is_(True),
                sample.Sample.affected.is_(True),
                sample.Sample.analysis_id == analysis_id,
                sample.Sample.family_id == sample_family_id,
            )
            .one()
        )

        return proband_sample

    def get_father_sample(self, proband_sample):

        father_sample = (
            self.session.query(sample.Sample)
            .filter(sample.Sample.id == proband_sample.father_id)
            .one_or_none()
        )

        return father_sample

    def get_mother_sample(self, proband_sample):

        mother_sample = (
            self.session.query(sample.Sample)
            .filter(sample.Sample.id == proband_sample.mother_id)
            .one_or_none()
        )

        return mother_sample

    def get_siblings_samples(self, proband_sample, affected=False):

        siblings_samples = (
            self.session.query(sample.Sample)
            .filter(
                sample.Sample.family_id == proband_sample.family_id,
                sample.Sample.sibling_id == proband_sample.id,
                sample.Sample.affected.is_(affected),
            )
            .all()
        )

        return siblings_samples

    def get_segregation_results(self, analysis_allele_ids: Dict[int, List[int]]):

        result: Dict[int, Dict[str, Set[int]]] = dict()
        for analysis_id, allele_ids in analysis_allele_ids.items():

            family_ids = self.get_family_ids(analysis_id)

            # All filters below need a family data set to work on
            if not family_ids:
                continue

            # Only one family id (i.e. data set) is supported at the moment
            assert len(family_ids) == 1

            result[analysis_id] = dict()

            proband_sample = self.get_proband_sample(analysis_id, family_ids[0])
            father_sample = self.get_father_sample(proband_sample)
            mother_sample = self.get_mother_sample(proband_sample)
            affected_sibling_sample_ids = self.get_siblings_samples(proband_sample, affected=True)
            unaffected_sibling_sample_ids = self.get_siblings_samples(
                proband_sample, affected=False
            )
            affected_sibling_sample_ids = [s.id for s in affected_sibling_sample_ids]
            unaffected_sibling_sample_ids = [s.id for s in unaffected_sibling_sample_ids]
            family_sample_ids = self.get_family_sample_ids(analysis_id, family_ids[0])

            genotype_table = get_genotype_temp_table(
                self.session,
                allele_ids,
                family_sample_ids,
                genotypesampledata_extras={"ar": "allele_ratio", "gl": "genotype_likelihood"},
            )

            result[analysis_id]["no_coverage_parents"] = self.no_coverage_father_mother(
                genotype_table, father_sample.id, mother_sample.id
            )

            result[analysis_id]["denovo"] = self.denovo(
                genotype_table, proband_sample.id, father_sample.id, mother_sample.id
            )

            result[analysis_id]["inherited_mosaicism"] = self.inherited_mosaicism(
                genotype_table, proband_sample.id, father_sample.id, mother_sample.id
            )

            result[analysis_id]["compound_heterozygous"] = self.compound_heterozygous(
                genotype_table,
                proband_sample.id,
                father_sample.id,
                mother_sample.id,
                affected_sibling_sample_ids=affected_sibling_sample_ids,
                unaffected_sibling_sample_ids=unaffected_sibling_sample_ids,
            )

            result[analysis_id][
                "autosomal_recessive_homozygous"
            ] = self.autosomal_recessive_homozygous(
                genotype_table,
                proband_sample.id,
                father_sample.id,
                mother_sample.id,
                affected_sibling_sample_ids=affected_sibling_sample_ids,
                unaffected_sibling_sample_ids=unaffected_sibling_sample_ids,
            )

            result[analysis_id]["xlinked_recessive_homozygous"] = self.xlinked_recessive_homozygous(
                genotype_table,
                proband_sample.id,
                father_sample.id,
                mother_sample.id,
                affected_sibling_sample_ids=affected_sibling_sample_ids,
                unaffected_sibling_sample_ids=unaffected_sibling_sample_ids,
            )

            result[analysis_id][
                "homozygous_unaffected_siblings"
            ] = self.homozygous_unaffected_siblings(
                genotype_table, proband_sample.id, unaffected_sibling_sample_ids
            )

        return result

    def filter_alleles(self, analysis_allele_ids, filter_config):
        """
        Returns allele_ids that can be filtered _out_ from an analysis.
        """

        segregation_results = self.get_segregation_results(analysis_allele_ids)

        result = dict()
        for analysis_id, allele_ids in analysis_allele_ids.items():
            if analysis_id not in segregation_results:
                result[analysis_id] = set()
                continue

            family_ids = self.get_family_ids(analysis_id)
            assert len(family_ids) == 1, "Multiple family ids are not supported yet"

            filtered: Set[int] = set()
            # Most filtering needs a trio
            proband_sample = self.get_proband_sample(analysis_id, family_ids[0])
            has_parents = proband_sample.father_id and proband_sample.mother_id
            if has_parents:
                non_filtered = (
                    segregation_results[analysis_id]["denovo"]
                    | segregation_results[analysis_id]["inherited_mosaicism"]
                    | segregation_results[analysis_id]["compound_heterozygous"]
                    | segregation_results[analysis_id]["autosomal_recessive_homozygous"]
                    | segregation_results[analysis_id]["xlinked_recessive_homozygous"]
                    | segregation_results[analysis_id]["no_coverage_parents"]
                )

                filtered = set(allele_ids) - non_filtered

            # Following can always be added to filtered (is empty when no siblings)
            filtered = filtered | segregation_results[analysis_id]["homozygous_unaffected_siblings"]

            result[analysis_id] = filtered

        return result
