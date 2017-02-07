from vardb.datamodel import allele, sample, genotype, workflow

from api.util.allelefilter import AlleleFilter
from api.schemas import AnalysisInterpretationSchema, AlleleInterpretationSchema


class InterpretationDataLoader(object):
    """
    Load various info about a interpretation (aka round) and the ID of the alleles that are part of it.
    There are two sources for the allele IDs:
    - Allele table (frequency/intron decided using annotation and config)
    - Snapshot table when the anlysis has been finalized
    """

    def __init__(self, session, config):
        self.session = session
        self.config = config

    def _get_classification_options(self, classification):
        for option in self.config['classification']['options']:
            if classification == option['value']:
                return option

    def _get_interpretation_cls(self, interpretation):
        if isinstance(interpretation, workflow.AnalysisInterpretation):
            return workflow.AnalysisInterpretation
        elif isinstance(interpretation, workflow.AlleleInterpretation):
            return workflow.AlleleInterpretation
        else:
            raise RuntimeError("Unknown interpretation class type.")

    def _get_interpretation_schema(self, interpretation):
        if isinstance(interpretation, workflow.AnalysisInterpretation):
            return AnalysisInterpretationSchema
        elif isinstance(interpretation, workflow.AlleleInterpretation):
            return AlleleInterpretationSchema
        else:
            raise RuntimeError("Unknown interpretation class type.")

    def group_alleles_by_config_and_annotation(self, interpretation):
        """
        Group the allele ids by checking the cutoff thresholds and intronic flag in annotation data
        and what gene it belongs to

        :param interpretation:
        :return: (normal, {'intron': {}, 'frequency': [], 'gene': []})
        """

        if isinstance(interpretation, workflow.AlleleInterpretation):
            excluded_allele_ids = {
                'frequency': [],
                'intronic': [],
                'gene': []
            }
            return [interpretation.allele.id], excluded_allele_ids

        elif isinstance(interpretation, workflow.AnalysisInterpretation):
            genepanel = interpretation.analysis.genepanel

            allele_ids = self.session.query(allele.Allele.id).join(
                genotype.Genotype.alleles,
                sample.Sample,
                sample.Analysis,
                workflow.AnalysisInterpretation
            ).filter(
                workflow.AnalysisInterpretation.id == interpretation.id,
                genotype.Genotype.sample_id == sample.Sample.id
            ).all()

            allele_ids = [a[0] for a in allele_ids]
            af = AlleleFilter(self.session, self.config)

            gp_key = (genepanel.name, genepanel.version)
            filtered_alleles = af.filter_alleles(
                {gp_key: allele_ids}
            )

            return filtered_alleles[gp_key]['allele_ids'], filtered_alleles[gp_key]['excluded_allele_ids']

    def group_alleles_by_finalization_filtering_status(self, interpretation):
        if not interpretation.snapshots:
            raise RuntimeError("Missing snapshot for interpretation.")

        allele_ids = []
        excluded_allele_ids = {
            'frequency': [],
            'intronic': [],
            'gene': []
        }

        for snapshot in interpretation.snapshots:
            if hasattr(snapshot, 'filtered'):
                if snapshot.filtered == allele.Allele.FREQUENCY:
                    excluded_allele_ids['frequency'].append(snapshot.allele_id)
                elif snapshot.filtered == allele.Allele.INTRON:
                    excluded_allele_ids['intronic'].append(snapshot.allele_id)
                elif snapshot.filtered == allele.Allele.GENE:
                    excluded_allele_ids['gene'].append(snapshot.allele_id)
                else:
                    allele_ids.append(snapshot.allele_id)
            else:
                allele_ids.append(snapshot.allele_id)

        return allele_ids, excluded_allele_ids

    def from_obj(self, interpretation):
        if interpretation.status == 'Done':
            allele_ids, excluded_ids = self.group_alleles_by_finalization_filtering_status(interpretation)
        else:
            allele_ids, excluded_ids = self.group_alleles_by_config_and_annotation(interpretation)

        result = self._get_interpretation_schema(interpretation)().dump(interpretation).data
        result['allele_ids'] = allele_ids
        result['excluded_allele_ids'] = excluded_ids
        return result
