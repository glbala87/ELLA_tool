from vardb.datamodel import allele, sample, genotype, workflow

from api.allelefilter import AlleleFilter
from api.schemas import AnalysisInterpretationSchema, AlleleInterpretationSchema
from api.config import config as global_config


class InterpretationDataLoader(object):
    """
    Load various info about a interpretation (aka round) and the ID of the alleles that are part of it.
    There are two sources for the allele IDs:
    - Allele table (frequency/intron decided using annotation and config)
    - Snapshot table when the anlysis has been finalized
    """

    def __init__(self, session):
        self.session = session

    @staticmethod
    def _get_interpretation_schema(interpretation):
        if isinstance(interpretation, workflow.AnalysisInterpretation):
            return AnalysisInterpretationSchema
        elif isinstance(interpretation, workflow.AlleleInterpretation):
            return AlleleInterpretationSchema
        else:
            raise RuntimeError("Unknown interpretation class type.")

    def group_alleles_by_config_and_annotation(self, interpretation, filter_config_id):
        """
        Group the allele ids by checking the cutoff thresholds and region flag in annotation data
        and what gene it belongs to

        :param interpretation:
        :return: (normal, {'region': {}, 'frequency': [], 'gene': []})
        """

        if isinstance(interpretation, workflow.AlleleInterpretation):
            excluded_allele_ids = {
                'frequency': [],
                'region': [],
                'ppy': [],
                'quality': [],
                'consequence': [],
                'segregation': []
            }
            return [interpretation.allele.id], excluded_allele_ids

        elif isinstance(interpretation, workflow.AnalysisInterpretation):
            analysis_id = interpretation.analysis_id
            analysis_allele_ids = self.session.query(
                allele.Allele.id
            ).join(
                genotype.Genotype.alleles,
                sample.Sample,
                sample.Analysis
            ).filter(
                sample.Analysis.id == analysis_id
            ).all()

            af = AlleleFilter(self.session)
            _, filtered_alleles = af.filter_alleles(
                filter_config_id,
                None,
                {analysis_id: [a[0] for a in analysis_allele_ids]}
            )

            return filtered_alleles[analysis_id]['allele_ids'], filtered_alleles[analysis_id]['excluded_allele_ids']

    def group_alleles_by_finalization_filtering_status(self, interpretation):
        if not interpretation.snapshots:
            raise RuntimeError("Missing snapshot for interpretation.")

        allele_ids = []

        # Don't remove category below as long as it's part of snapshot tables' enums
        # even if it's not a filter being used anymore. Otherwise, viewing historic analyses will break
        categories = {
            'FREQUENCY': 'frequency',
            'REGION': 'region',
            'POLYPYRIMIDINE': 'ppy',
            'GENE': 'gene',
            'QUALITY': 'quality',
            'CONSEQUENCE': 'consequence',
            'SEGREGATION': 'segregation'
        }

        excluded_allele_ids = {k: [] for k in categories.values()}

        for snapshot in interpretation.snapshots:
            if hasattr(snapshot, 'filtered'):
                if snapshot.filtered in categories:
                    excluded_allele_ids[categories[snapshot.filtered]].append(snapshot.allele_id)
                else:
                    allele_ids.append(snapshot.allele_id)
            else:
                allele_ids.append(snapshot.allele_id)

        return allele_ids, excluded_allele_ids

    def from_obj(self, interpretation, filter_config_id):
        if interpretation.status == 'Done':
            allele_ids, excluded_ids = self.group_alleles_by_finalization_filtering_status(interpretation)
        else:
            allele_ids, excluded_ids = self.group_alleles_by_config_and_annotation(interpretation, filter_config_id)

        result = InterpretationDataLoader._get_interpretation_schema(interpretation)().dump(interpretation).data
        result['allele_ids'] = allele_ids
        result['excluded_allele_ids'] = excluded_ids
        return result
