import operator
from typing import Any, Dict, List, Set, Union, Tuple
from sqlalchemy import and_, or_, literal_column, func
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.selectable import Alias

from vardb.datamodel import annotation

OPERATORS = {
    "==": operator.eq,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}

HGMD_TAGS = set([None, "FP", "DM", "DFP", "R", "DP", "DM?"])


class ExternalFilter(object):
    def __init__(self, session: Session, config: Dict[str, Any]) -> None:
        self.session = session
        self.config = config

    def _build_clinvar_filters(
        self, clinsig_counts: Alias, combinations: List[Tuple[str, str, Union[str, int]]]
    ) -> List[BinaryExpression]:
        """
        Combinations is given as a list of lists, like

            [["benign", ">", 5], # More than 5 benign submissions
            ["pathogenic", "==", 0], # No pathogenic submissions
            ["benign", ">", "uncertain"]] # More benign than uncertain submissions

        """

        def get_filter_count(v: Union[str, int]):
            if isinstance(v, str):
                assert v in ["benign", "pathogenic", "uncertain"]
                return getattr(clinsig_counts.c, v)
            else:
                assert isinstance(v, (int, float))
                return v

        filters = []
        for c in combinations:
            clinsig, op, count = c[0], OPERATORS[c[1]], get_filter_count(c[2])
            filters.append(op(getattr(clinsig_counts.c, clinsig), count))
        return filters

    def _filter_clinvar(self, allele_ids: List[int], clinvar_config: Dict[str, Any]) -> Set[int]:
        # Use this to evaluate the number of stars
        star_op, num_stars = clinvar_config.get("num_stars", (">=", 0))
        star_op = OPERATORS[star_op]

        # Extract clinical_significance_status that matches the num_stars criteria
        # The clinical_significance_status to stars mapping is given in the config
        filter_signifiance_descr = [
            k
            for k, v in list(
                self.config["annotation"]["clinvar"]["clinical_significance_status"].items()
            )
            if star_op(v, num_stars)
        ]

        combinations = clinvar_config.get("combinations", [])

        # Expand clinvar submissions, where clinical_significance_status satisfies
        clinvar_entries = (
            self.session.query(
                annotation.Annotation.allele_id,
                literal_column(
                    "jsonb_array_elements(annotations->'external'->'CLINVAR'->'items')"
                ).label("entry"),
            )
            .filter(
                annotation.Annotation.allele_id.in_(allele_ids),
                annotation.Annotation.date_superceeded.is_(None),
                annotation.Annotation.annotations.op("->")("external")
                .op("->")("CLINVAR")
                .op("->>")("variant_description")
                .in_(filter_signifiance_descr),
            )
            .subquery()
        )

        # Extract clinical significance for all SCVs
        clinvar_clinsigs = (
            self.session.query(
                clinvar_entries.c.allele_id,
                clinvar_entries.c.entry.op("->>")("clinical_significance_descr").label("clinsig"),
            )
            .filter(clinvar_entries.c.entry.op("->>")("rcv").op("ILIKE")("SCV%"))
            .subquery()
        )

        def count_matches(pattern):
            return func.count(clinvar_clinsigs.c.clinsig).filter(
                clinvar_clinsigs.c.clinsig.op("ILIKE")(pattern)
            )

        # Count the number of Pathogenic/Likely pathogenic, Uncertain significance, and Benign/Likely benign
        # Note: This does not match any clinsig with e.g. Drug response or similar
        clinsig_counts = (
            self.session.query(
                clinvar_clinsigs.c.allele_id,
                count_matches("%pathogenic%").label("pathogenic"),
                count_matches("%uncertain%").label("uncertain"),
                count_matches("%benign%").label("benign"),
            )
            .group_by(clinvar_clinsigs.c.allele_id)
            .order_by(clinvar_clinsigs.c.allele_id)
            .subquery()
        )

        filters = self._build_clinvar_filters(clinsig_counts, combinations)

        # Extract allele ids that matches the config rules
        filtered_allele_ids = self.session.query(clinsig_counts.c.allele_id).filter(and_(*filters))

        inverse = clinvar_config.get("inverse", False)
        if inverse:
            return set(allele_ids) - set([a[0] for a in filtered_allele_ids])
        else:
            return set([a[0] for a in filtered_allele_ids])

    def _filter_hgmd(self, allele_ids: List[int], hgmd_config: Dict[str, Any]) -> Set[int]:

        hgmd_tags = hgmd_config["tags"]
        assert hgmd_tags, "No tags provided to hgmd filter, even though config is defined"
        assert (
            not set(hgmd_tags) - HGMD_TAGS
        ), "Invalid tag(s) to filter on in {}. Available tags are {}.".format(hgmd_tags, HGMD_TAGS)

        # Need to separate check for specific tag and check for no HGMD data (tag is None)
        filters = []
        if None in hgmd_tags:
            hgmd_tags.pop(hgmd_tags.index(None))
            filters.append(
                annotation.Annotation.annotations.op("->")("external")
                .op("->")("HGMD")
                .op("->>")("tag")
                .is_(None)
            )

        if hgmd_tags:
            filters.append(
                annotation.Annotation.annotations.op("->")("external")
                .op("->")("HGMD")
                .op("->>")("tag")
                .in_(hgmd_tags)
            )

        filtered_allele_ids = self.session.query(annotation.Annotation.allele_id).filter(
            annotation.Annotation.date_superceeded.is_(None),
            annotation.Annotation.allele_id.in_(allele_ids),
            or_(*filters),
        )

        inverse = hgmd_config.get("inverse", False)
        if inverse:
            return set(allele_ids) - set([a[0] for a in filtered_allele_ids])
        else:
            return set([a[0] for a in filtered_allele_ids])

    def filter_alleles(
        self, gp_allele_ids: Dict[Tuple[str, str], List[int]], filter_config: Dict[str, Any]
    ) -> Dict[Tuple[str, str], Set[int]]:
        """
        Filter alleles on external annotations. Supported external databases are clinvar and hgmd.
        Filters only alleles which satisify *both* clinvar and hgmd configurations.
        If only one of clinvar or hgmd is specified, filters on this alone.

        filter_config is specified like
        {
            "clinvar": {
                "combinations": [
                    ["benign", ">", 5], # More than 5 benign submissions
                    ["pathogenic", "==", 0], # No pathogenic submissions
                    ["benign", ">", "uncertain"] # More benign than uncertain submissions
                ],
                "num_stars": [">=", 2] # Only include variants with 2 or more stars
            },
            "hgmd": {
                "tags": [None], # Not in HGMD
            }
        }

        """
        result: Dict[Tuple[str, str], Set[int]] = dict()
        for gp_key, allele_ids in gp_allele_ids.items():
            if not allele_ids:
                result[gp_key] = set()
                continue

            clinvar_config = filter_config.get("clinvar")
            if clinvar_config:
                clinvar_filtered_allele_ids = self._filter_clinvar(allele_ids, clinvar_config)

            hgmd_config = filter_config.get("hgmd")
            if hgmd_config:
                hgmd_filtered_allele_ids = self._filter_hgmd(allele_ids, hgmd_config)

            # Union hgmd filtered and clinvar filtered if both have been run, otherwise return the result of the run one
            if clinvar_config and hgmd_config:
                result[gp_key] = clinvar_filtered_allele_ids & hgmd_filtered_allele_ids
            elif clinvar_config:
                result[gp_key] = clinvar_filtered_allele_ids
            elif hgmd_config:
                result[gp_key] = hgmd_filtered_allele_ids
            else:
                result[gp_key] = set()

        return result
