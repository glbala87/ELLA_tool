import itertools
from typing import Dict, Sequence, Tuple, Union

from api.util.types import FilteredAlleleCategories
from sqlalchemy.orm.session import Session
from vardb.datamodel import Base, annotation, assessment, workflow


class SnapshotCreator(object):
    def __init__(self, session: Session):
        self.session = session

    def _allele_id_model_id(self, model: Base, model_ids: Sequence[int]):
        allele_ids_model_ids: Sequence[Tuple[int, int]] = (
            self.session.query(getattr(model, "allele_id"), getattr(model, "id"))
            .filter(getattr(model, "id").in_(model_ids))
            .all()
        )
        assert len(allele_ids_model_ids) == len(model_ids)

        return {a[0]: a[1] for a in allele_ids_model_ids}

    def insert_from_data(
        self,
        allele_ids: Sequence[int],
        interpretation_snapshot_model: str,  # 'allele' or 'analysis'
        interpretation: Union[workflow.AnalysisInterpretation, workflow.AlleleInterpretation],
        annotation_ids: Sequence[int],
        custom_annotation_ids: Sequence[int],
        alleleassessment_ids: Sequence[int],
        allelereport_ids: Sequence[int],
        excluded_allele_ids: Dict = None,
    ) -> Sequence[Dict]:
        excluded: Dict = {}

        if interpretation_snapshot_model == "analysis":
            assert excluded_allele_ids is not None
            excluded = excluded_allele_ids

            all_allele_ids = list(
                set(allele_ids).union(set(itertools.chain(*list(excluded.values()))))
            )

        # 'excluded' is not a concept for alleleinterpretation
        elif interpretation_snapshot_model == "allele":
            all_allele_ids = [interpretation.allele_id]

        allele_ids_annotation_ids = self._allele_id_model_id(annotation.Annotation, annotation_ids)
        allele_ids_custom_annotation_ids = self._allele_id_model_id(
            annotation.CustomAnnotation, custom_annotation_ids
        )
        allele_ids_alleleassessment_ids = self._allele_id_model_id(
            assessment.AlleleAssessment, alleleassessment_ids
        )
        allele_ids_allelereport_ids = self._allele_id_model_id(
            assessment.AlleleReport, allelereport_ids
        )

        snapshot_items = list()
        for allele_id in all_allele_ids:
            # Check if allele_id is in any of the excluded categories
            excluded_category = next((k for k, v in excluded.items() if allele_id in v), None)

            snapshot_item = {
                "allele_id": allele_id,
                "annotation_id": allele_ids_annotation_ids.get(allele_id),
                "customannotation_id": allele_ids_custom_annotation_ids.get(allele_id),
                "alleleassessment_id": allele_ids_alleleassessment_ids.get(allele_id),
                "allelereport_id": allele_ids_allelereport_ids.get(allele_id),
            }

            if interpretation_snapshot_model == "analysis":
                snapshot_item["analysisinterpretation_id"] = interpretation.id
                snapshot_item["filtered"] = (
                    FilteredAlleleCategories(excluded_category).name
                    if excluded_category is not None
                    else None
                )
            elif interpretation_snapshot_model == "allele":
                snapshot_item["alleleinterpretation_id"] = interpretation.id

            snapshot_items.append(snapshot_item)

        if interpretation_snapshot_model == "analysis":
            self.session.bulk_insert_mappings(
                workflow.AnalysisInterpretationSnapshot, snapshot_items
            )
        elif interpretation_snapshot_model == "allele":
            self.session.bulk_insert_mappings(workflow.AlleleInterpretationSnapshot, snapshot_items)

        return snapshot_items
