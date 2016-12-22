from sqlalchemy.orm import joinedload, contains_eager, load_only

from vardb.datamodel import allele, sample, genotype, workflow

from api.util.alleledataloader import AlleleDataLoader
from api.schemas import AnalysisInterpretationSchema, AlleleInterpretationSchema
from api.util.annotationprocessor.genepanelprocessor import ABOVE_RESULT


class InterpretationDataLoader(object):
    """
    Load various info about a interpretation (aka round) and the ID of the alleles that are part of it.
    There are two sources for the allele IDs:
    - Allele table (class1/intron decided using annotation and config)
    - AnalysisFinalized table when the anlysis has been finalized
    """

    def __init__(self, session, config):
        self.session = session
        self.config = config

    def _exclude_gene(self, allele):
        """
        Check whether gene(s) are part of excluded_genes list
        We only use genes from filtered transcripts, as that is the
        context the user cares about.
        """

        excluded_genes = self.config['variant_criteria']['exclude_genes']
        filtered = [t for t in allele['annotation']['transcripts'] if t['Transcript'] in allele['annotation']['filtered_transcripts']]
        allele_genes = [f['SYMBOL'] for f in filtered]
        return bool(list(set(excluded_genes).intersection(set(allele_genes))))

    def _exclude_class1(self, allele):
        for group in self.config['variant_criteria']['frequencies']['groups']:
            if any(c == ABOVE_RESULT for c in allele['annotation']['frequencies']['cutoff'][group].values()):
                return True
        return False

    def _exclude_intronic(self, allele):
        for filtered_transcript in allele['annotation']['filtered_transcripts']:
            t = next((tla for tla in allele['annotation']['transcripts'] if tla['Transcript'] == filtered_transcript), None)
            if t and t.get('intronic'):
                return True
        return False

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
        :return: (normal, {'intron': {}, 'class1': [], 'gene': []})
        """
        genepanel = interpretation.analysis.genepanel

        interpretation_cls = self._get_interpretation_cls(interpretation)

        alleles_with_id = self.session.query(allele.Allele).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            interpretation_cls
        ).options(
            contains_eager('genotypes'),  # do not use joinedload, as that will filter wrong
        ).filter(
            # TODO: Add AlleleInterpretation
            interpretation_cls.id == interpretation.id,
            genotype.Genotype.sample_id == sample.Sample.id
        ).options(
            load_only('id')
        ).all()

        loaded_alleles = AlleleDataLoader(self.session).from_objs(
            alleles_with_id,
            genepanel=genepanel,
            include_allele_assessment=False,
            include_reference_assessments=False
        )

        allele_ids = []
        excluded_allele_ids = {
            'class1': [],
            'intronic': [],
            'gene': []
        }

        for la in loaded_alleles:
            # Filter priority: Gene, class1, intronic
            if self._exclude_gene(la):
                excluded_allele_ids['gene'].append(la['id'])
            elif self._exclude_class1(la):
                excluded_allele_ids['class1'].append(la['id'])
            elif self._exclude_intronic(la):
                excluded_allele_ids['intronic'].append(la['id'])
            else:
                allele_ids.append(la['id'])

        return allele_ids, excluded_allele_ids

    def group_alleles_by_finalization_filtering_status(self, interpretation):
        if not interpretation.snapshots:
            raise RuntimeError("Missing snapshot for interpretation.")

        allele_ids = []
        excluded_allele_ids = {
            'class1': [],
            'intronic': [],
            'gene': []
        }

        for snapshot in interpretation.snapshots:
            if snapshot.filtered == allele.Allele.CLASS1:
                excluded_allele_ids['class1'].append(snapshot.allele_id)
            elif snapshot.filtered == allele.Allele.INTRON:
                excluded_allele_ids['intron'].append(snapshot.allele_id)
            elif snapshot.filtered == allele.Allele.GENE:
                excluded_allele_ids['gene'].append(snapshot.allele_id)
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
