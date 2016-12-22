import itertools

from vardb.datamodel import user, assessment, sample, genotype, allele, annotation, gene, workflow
from api import schemas, ApiError
from api.util.assessmentcreator import AssessmentCreator
from api.util.allelereportcreator import AlleleReportCreator
from api.util.interpretationdataloader import InterpretationDataLoader
from api.config import config


class SnapshotCreator(object):

    EXCLUDED_FLAG = {
        'class1': allele.Allele.CLASS1,
        'intronic': allele.Allele.INTRON,
        'gene': allele.Allele.GENE
    }

    def __init__(self, session):
        self.session = session

    def _create_snapshot_object(
            self,
            interpretation_snapshot_model,
            interpretation_id,
            allele_id,
            annotations,
            custom_annotations,
            presented_alleleassessments,
            presented_allelereports,
            used_alleleassessments=None,
            used_allelereports=None,
            excluded_category=None):

        annotation = next((a for a in annotations if a['allele_id'] == allele_id), None)
        custom_annotation = next((a for a in custom_annotations if a['allele_id'] == allele_id), None)

        kwargs = {
            'allele_id': allele_id,
        }

        if not excluded_category:
            presented_alleleassessment_id = next((a.id for a in presented_alleleassessments if a.allele_id == allele_id), None)
            alleleassessment_id = next((a.id for a in used_alleleassessments if a.allele_id == allele_id), None)

            presented_allelereport_id = next((a.id for a in presented_allelereports if a.allele_id == allele_id), None)
            allelereport_id = next((a.id for a in used_allelereports if a.allele_id == allele_id), None)

            kwargs.update({
                'annotation_id': annotation['annotation_id'],
                'customannotation_id': custom_annotation['custom_annotation_id'] if (
                                       custom_annotation and 'custom_annotation_id' in custom_annotation) else None,
                'alleleassessment_id': alleleassessment_id,
                'presented_alleleassessment_id': presented_alleleassessment_id,
                'allelereport_id': allelereport_id,
                'presented_allelereport_id': presented_allelereport_id,
            })

        if interpretation_snapshot_model == 'analysis':
            kwargs['analysisinterpretation_id'] = interpretation_id
            kwargs['filtered'] = SnapshotCreator.EXCLUDED_FLAG.get(excluded_category)
            return workflow.AnalysisInterpretationSnapshot(**kwargs)
        elif interpretation_snapshot_model == 'allele':
            kwargs['alleleinterpretation_id'] = interpretation_id
            return workflow.AlleleInterpretationSnapshot(**kwargs)

    def create_from_data(
            self,
            interpretation_snapshot_model,  # 'allele' or 'analysis'
            interpretation_id,
            annotations,
            presented_alleleassessments,
            presented_allelereports,
            used_alleleassessments=None,
            used_allelereports=None,
            custom_annotations=None):

        if custom_annotations is None:
            custom_annotations = list()

        if used_alleleassessments is None:
            used_alleleassessments = list()

        if used_allelereports is None:
            used_allelereports = list()

        # Get working list of alleles straigt from interpretation to ensure we log all data
        excluded = None
        if interpretation_snapshot_model == 'analysis':
            analysisinterpretation_obj = self.session.query(workflow.AnalysisInterpretation).filter(
                workflow.AnalysisInterpretation.id == interpretation_id
            ).one()
            analysisinterpretation = InterpretationDataLoader(self.session, config).from_obj(analysisinterpretation_obj)
            excluded = analysisinterpretation['excluded_allele_ids']
            allele_ids = analysisinterpretation['allele_ids'] + \
                         list(itertools.chain(*excluded.values()))

        # 'excluded' is not a concept for alleleinterpretation
        elif interpretation_snapshot_model == 'allele':
            alleleinterpretation = self.session.query(workflow.AlleleInterpretation).filter(
                workflow.AlleleInterpretation.id == interpretation_id
            ).one()
            allele_ids = [alleleinterpretation.allele_id]

        snapshot_objects = list()
        for allele_id in allele_ids:
            excluded_category = next((k for k, v in excluded.iteritems() if allele_id in v), None)
            # Check if allele_id is in any of the excluded categories
            snapshot_object = self._create_snapshot_object(
                interpretation_snapshot_model,
                interpretation_id,
                allele_id,
                annotations,
                custom_annotations,
                presented_alleleassessments,
                presented_allelereports,
                used_alleleassessments=used_alleleassessments,
                used_allelereports=used_allelereports,
                excluded_category=excluded_category
            )
            snapshot_objects.append(snapshot_object)

        return snapshot_objects
