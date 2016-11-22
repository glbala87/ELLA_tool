from sqlalchemy.orm import joinedload, contains_eager, load_only

from vardb.datamodel import allele, sample, genotype

from api.util.alleledataloader import AlleleDataLoader
from api.schemas import InterpretationSchema
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

    def group_alleles_by_config_and_annotation(self, interpretation):
        """
        Group the allele ids by checking the cutoff thresholds and intronic flag in annotation data
        and what gene it belongs to

        :param interpretation:
        :return: (normal, {'intron': {}, 'class1': [], 'gene': []})
        """
        genepanel = interpretation.analysis.genepanel

        alleles_with_id = self.session.query(allele.Allele).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            sample.Interpretation
        ).options(
            contains_eager('genotypes'),  # do not use joinedload, as that will filter wrong
        ).filter(
            sample.Interpretation.id == interpretation.id,
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

    def group_alleles_by_finalization_filtering_status(self, analysis_id):
        entities_finalized =\
            self.session.query(sample.AnalysisFinalized
            ).filter(
            sample.AnalysisFinalized.analysis_id == analysis_id
            ).all()

        allele_ids = []
        excluded_allele_ids = {
            'class1': [],
            'intronic': [],
            'gene': []
        }

        for f in entities_finalized:
            if f.filtered == allele.Allele.CLASS1:
                excluded_allele_ids['class1'].append(f.allele_id)
            elif f.filtered == allele.Allele.INTRON:
                excluded_allele_ids['intron'].append(f.allele_id)
            elif f.filtered == allele.Allele.GENE:
                excluded_allele_ids['gene'].append(f.allele_id)
            else:
                allele_ids.append(f.allele_id)

        return allele_ids, excluded_allele_ids

    def from_id(self, interpretation_id):
        interpretation = self.session.query(sample.Interpretation).options(
            joinedload('analysis'),
            joinedload('analysis.samples')
        ).filter(sample.Interpretation.id == interpretation_id
        ).one()

        analysis_is_finalized = all(map(lambda i:  i.status == 'Done', interpretation.analysis.interpretations))

        allele_ids, excluded_ids = (self.group_alleles_by_finalization_filtering_status(interpretation.analysis_id)
            if analysis_is_finalized else self.group_alleles_by_config_and_annotation(interpretation))

        result = InterpretationSchema().dump(interpretation).data
        result['allele_ids'] = allele_ids
        result['excluded_allele_ids'] = excluded_ids
        return result
