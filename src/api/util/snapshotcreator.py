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

    def _find_first_matching(self, seq, predicate):
        return next((s for s in seq if predicate(s)), None)

    # internal helper methods:
    def _find_first_allele_assessment(self, created_alleleassessments, reused_alleleassessments, allele_id):
        """
        Find the first assessment from 'created..' and 'reused..' whose allele_id matches.
        If found, return a tuple (id_of_presented | None, id_of_created | None)
        """

        created = self._find_first_matching(created_alleleassessments, lambda x: x[1].allele_id == allele_id)
        reused = self._find_first_matching(reused_alleleassessments, lambda x: x[0].allele_id == allele_id)
        if created:
            return created[0].id if created[0] else None, created[1].id
        if reused:
            return reused[0].id, None
        raise ApiError("No allele assessment found for allele_id {} when finalizing analysis.".format(allele_id))

    def _find_first_allele_report(self, created_allele_reports, reused_allele_reports, allele_id):
        """
        Find the first report from 'created..' and 'reused..' whose allele_id matches.
        If found, return a tuple (id_of_presented | None, id_of_created | None)
        """
        created = self._find_first_matching(created_allele_reports, lambda x: x[1].allele_id == allele_id)
        reused = self._find_first_matching(reused_allele_reports, lambda x: x[0].allele_id == allele_id)
        if created:
            return created[0].id if created[0] else None, created[1].id
        if reused:
            return reused[0].id, None
        raise ApiError("No allele assessment found for allele_id {} when finalizing analysis.".format(allele_id))

    def _create_snapshot_object(
            self,
            interpretation_snapshot_model,
            interpretation_id,
            allele_id,
            annotations,
            custom_annotations,
            created_alleleassessments,
            reused_alleleassessments,
            created_allelereports,
            reused_allelereports,
            excluded_category=None):

        annotation = self._find_first_matching(annotations, lambda x: x['allele_id'] == allele_id)
        custom_annotation = self._find_first_matching(custom_annotations, lambda x: x['allele_id'] == allele_id)
        presented_alleleassessment_id, alleleassessment_id = self._find_first_allele_assessment(
            created_alleleassessments,
            reused_alleleassessments,
            allele_id)
        presented_allelereport_id, allelereport_id = self._find_first_allele_report(created_allelereports,
                                                                                    reused_allelereports,
                                                                                    allele_id)
        kwargs = {
            'allele_id': allele_id,
            'annotation_id': annotation['annotation_id'],
            'customannotation_id': custom_annotation['custom_annotation_id'] if (
                custom_annotation and 'custom_annotation_id' in custom_annotation) else None,
            'alleleassessment_id': alleleassessment_id,
            'presented_alleleassessment_id': presented_alleleassessment_id,
            'allelereport_id': allelereport_id,
            'presented_allelereport_id': presented_allelereport_id,
        }
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
            reused_alleleassessments,
            created_alleleassessments,
            reused_allelereports=None,
            created_allelereports=None,
            custom_annotations=None):

        if custom_annotations is None:
            custom_annotations = list()

        if created_allelereports is None:
            created_allelereports = list()

        if reused_allelereports is None:
            reused_allelereports = list()

        # Get working list of alleles straigt from interpretation to ensure we log all data
        excluded = dict()
        if interpretation_snapshot_model == 'analysis':
            analysisinterpretation = InterpretationDataLoader(self.session, config).from_id(interpretation_id)
            excluded = analysisinterpretation['excluded']
            allele_ids = analysisinterpretation['allele_ids'] + \
                         itertools.chain(*excluded.values())

        # 'excluded' is not a concept for alleleinterpretation
        elif interpretation_snapshot_model == 'allele':
            alleleinterpretation = self.session.query(workflow.AlleleInterpretation).filter(
                workflow.AlleleInterpretation.id == interpretation_id
            ).one()
            allele_ids = [alleleinterpretation.allele_id]

        snapshot_objects = list()
        for allele_id in allele_ids:
            # Check if allele_id is in any of the excluded categories
            excluded_category = next((k for k, v in excluded.iteritems() if allele_id in v), None)
            snapshot_object = self._create_snapshot_object_for_included_allele(
                interpretation_snapshot_model,
                interpretation_id,
                allele_id,
                annotations,
                custom_annotations,
                created_alleleassessments,
                reused_alleleassessments,
                created_allelereports,
                reused_allelereports,
                excluded_category=excluded_category
            )
            snapshot_objects.append(snapshot_object)

        return snapshot_objects
