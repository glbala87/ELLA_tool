from sqlalchemy.orm import joinedload, contains_eager, load_only

from vardb.datamodel import allele, sample, genotype

from api.util.alleledataloader import AlleleDataLoader
from api.schemas import InterpretationSchema
from api.util.annotationprocessor.genepanelprocessor import ABOVE_RESULT


class InterpretationDataLoader(object):

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

    def exclude_alleles(self, alleles):
        """
        Exclude intronic, class 1 and gene alleles by checking
        the cutoff thresholds, intronic flag in annotation data and
        what gene it belongs to.
        """

        allele_ids = []
        excluded_allele_ids = {
            'class1': [],
            'intronic': [],
            'gene': []
        }

        for la in alleles:
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

    def from_id(self, interpretation_id):
        a = self.session.query(sample.Interpretation).options(joinedload('analysis'), joinedload('analysis.samples')).filter(sample.Interpretation.id == interpretation_id).one()

        genepanel = a.analysis.genepanel

        alleles = self.session.query(allele.Allele).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            sample.Interpretation
        ).options(
            contains_eager('genotypes'),  # do not use joinedload, as that will filter wrong
        ).filter(
            sample.Interpretation.id == interpretation_id,
            genotype.Genotype.sample_id == sample.Sample.id
        ).options(
            load_only('id')
        ).all()

        adl = AlleleDataLoader(self.session)
        loaded_alleles = adl.from_objs(
            alleles,
            genepanel=genepanel,
            include_allele_assessment=False,
            include_reference_assessments=False
        )

        result = InterpretationSchema().dump(a).data

        # Exclude allele (ids) based on criterias
        allele_ids, excluded_allele_ids = self.exclude_alleles(loaded_alleles)
        result['allele_ids'] = allele_ids
        result['excluded_allele_ids'] = excluded_allele_ids
        return result