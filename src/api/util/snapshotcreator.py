import itertools

from vardb.datamodel import allele, workflow
from api.config import config


class SnapshotCreator(object):

    EXCLUDED_FLAG = {
        "frequency": "FREQUENCY",
        "region": "REGION",
        "ppy": "POLYPYRIMIDINE",
        "gene": "GENE",
        "quality": "QUALITY",
        "consequence": "CONSEQUENCE",
        "segregation": "SEGREGATION",
        "inheritancemodel": "INHERITANCEMODEL",
    }

    def __init__(self, session):
        self.session = session

    def insert_from_data(
        self,
        interpretation_snapshot_model,  # 'allele' or 'analysis'
        interpretation,  # interpretation object from db
        annotations,
        presented_alleleassessments,
        presented_allelereports,
        allele_ids=None,
        excluded_allele_ids=None,
        used_alleleassessments=None,
        used_allelereports=None,
        custom_annotations=None,
    ):

        if custom_annotations is None:
            custom_annotations = list()

        if used_alleleassessments is None:
            used_alleleassessments = list()

        if used_allelereports is None:
            used_allelereports = list()

        excluded = {}
        if interpretation_snapshot_model == "analysis":
            excluded = excluded_allele_ids
            allele_ids = list(set(allele_ids).union(set(itertools.chain(*list(excluded.values())))))

        # 'excluded' is not a concept for alleleinterpretation
        elif interpretation_snapshot_model == "allele":
            allele_ids = [interpretation.allele_id]

        snapshot_items = list()
        for allele_id in allele_ids:
            excluded_category = next((k for k, v in excluded.items() if allele_id in v), None)
            # Check if allele_id is in any of the excluded categories

            snapshot_item = {
                "allele_id": allele_id,
                "annotation_id": next(
                    (a["annotation_id"] for a in annotations if a["allele_id"] == allele_id), None
                ),
                "customannotation_id": next(
                    (
                        a["custom_annotation_id"]
                        for a in custom_annotations
                        if a["allele_id"] == allele_id
                    ),
                    None,
                ),
                "presented_alleleassessment_id": next(
                    (a.id for a in presented_alleleassessments if a.allele_id == allele_id), None
                ),
                "alleleassessment_id": next(
                    (a.id for a in used_alleleassessments if a.allele_id == allele_id), None
                ),
                "presented_allelereport_id": next(
                    (a.id for a in presented_allelereports if a.allele_id == allele_id), None
                ),
                "allelereport_id": next(
                    (a.id for a in used_allelereports if a.allele_id == allele_id), None
                ),
            }

            if interpretation_snapshot_model == "analysis":
                snapshot_item["analysisinterpretation_id"] = interpretation.id
                snapshot_item["filtered"] = (
                    SnapshotCreator.EXCLUDED_FLAG[excluded_category]
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
