from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm.session import Session
from sqlalchemy import func
from api.util.queries import annotation_transcripts_genepanel


class GeneFilter(object):
    MODES_OPERATOR = {
        "one": "&&",  # Postgres overlap operator
        "all": "<@",  # Postgres 'is contained by' operator
    }

    def __init__(self, session: Session, config: Optional[Dict[str, Any]]) -> None:
        self.session = session
        self.config = config

    def filter_alleles(
        self, gp_allele_ids: Dict[Tuple[str, str], List[int]], filter_config: Dict[str, Any]
    ) -> Dict[Tuple[str, str], Set[int]]:
        """
        Return the allele ids, among the provided allele_ids,
        that matches the genes given in filter_config. The filter uses annotation on the genepanel only,
        meaning

        1. If the genes are not in the gene panel, they will have no effect
        2. The annotation transcripts are matched on gene panel transcripts (excl version), meaning that for an allele to be filtered,
           it must be annotated with a transcript present in the gene panel.

        The filter can be configured with the following settings:

        - genes (required):
            List of hgnc ids
        - mode (optional, 'one' or 'all', default 'all'):
            If 'all': variant must be annotated with genes from the 'genes' list only. Useful for filtering out.
            If 'one', variant annotation must include at least one gene from the gene list (but could be annotated with other genes). Useful for exceptions.
        - inverse (optional, default False):
            If True, run the filter in inverse.
        """
        filter_genes = filter_config["genes"]
        inverse = filter_config.get("inverse", False)
        mode = filter_config.get("mode", "all")  # 'one' or 'all'
        assert (
            mode in GeneFilter.MODES_OPERATOR
        ), "Mode {} for GeneFilter not supported. Supported values are {}.".format(
            mode, GeneFilter.MODES_OPERATOR.keys()
        )

        operator = GeneFilter.MODES_OPERATOR[mode]

        result: Dict[Tuple[str, str], Set[int]] = dict()

        for gp_key, allele_ids in gp_allele_ids.items():
            # We rely on the annotation of the variants, and only consider annotation from the genepanel transcripts
            allele_ids_annotation_genepanel = annotation_transcripts_genepanel(
                self.session, [gp_key], allele_ids
            ).subquery()

            # Group HGNC ids per allele, excluding alleles without any hgnc ids to avoid empty arrays
            # -----------------------------
            # | allele_id | hgnc_ids       |
            # -----------------------------
            # | 1         | [329]          |
            # | 2         | [3084]         |
            # | 3         | [25567]        |
            # | 4         | [25186, 25567] |
            # | 5         | [25186, 25567] |
            # | 6         | [19104]        |
            # | 7         | [13281]        |
            # | 8         | [18806]        |
            # | 9         | [18806]        |
            # | 10        | [18806]        |
            allele_id_genes = (
                self.session.query(
                    allele_ids_annotation_genepanel.c.allele_id,
                    func.array_agg(allele_ids_annotation_genepanel.c.genepanel_hgnc_id).label(
                        "hgnc_ids"
                    ),
                )
                .filter(
                    ~allele_ids_annotation_genepanel.c.genepanel_hgnc_id.is_(None)
                )  # IMPORTANT! Avoid empty arrays, as empty arrays always overlap or is contained within another
                .group_by(allele_ids_annotation_genepanel.c.allele_id)
                .subquery()
            )

            filtered_allele_ids = self.session.query(allele_id_genes.c.allele_id).filter(
                allele_id_genes.c.hgnc_ids.op(operator)(filter_genes)
            )

            if inverse:
                result[gp_key] = set(allele_ids) - set(filtered_allele_ids.scalar_all())
            else:
                result[gp_key] = set(filtered_allele_ids.scalar_all())

        return result
