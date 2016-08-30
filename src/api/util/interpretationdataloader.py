from sqlalchemy.orm import joinedload, contains_eager, load_only

from vardb.datamodel import allele, sample, genotype

from api.util.alleledataloader import AlleleDataLoader
from api.schemas import InterpretationSchema
from api.util.annotationprocessor.genepanelprocessor import ABOVE_RESULT
from api.config import config


class InterpretationDataLoader(object):

    def __init__(self, session):
        self.session = session

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

        # Filter intronic and class 1 alleles into 'excluded'
        # by checking the cutoff thresholds and intronic flag
        # in annotation data
        allele_ids = []
        excluded_allele_ids = {
            'class1': [],
            'intronic': []
        }

        for la in loaded_alleles:
            added_to_excluded = False
            # Class 1 filtering takes precedence over intronic
            for group in config['variant_criteria']['frequencies']['groups']:
                if any(c == ABOVE_RESULT for c in la['annotation']['frequencies']['cutoff'][group].values()):
                    excluded_allele_ids['class1'].append(la['id'])
                    added_to_excluded = True
                    break
            else:
                # Check for intronic region in any of the genepanel transcripts
                for filtered_transcript in la['annotation']['filtered_transcripts']:
                    t = next(tla for tla in la['annotation']['transcripts'] if tla['Transcript'] == filtered_transcript)
                    if t['intronic']:
                        excluded_allele_ids['intronic'].append(la['id'])
                        added_to_excluded = True
                        break
            if not added_to_excluded:
                allele_ids.append(la['id'])

        result = InterpretationSchema().dump(a)
        data = result.data
        data['allele_ids'] = allele_ids
        data['excluded_allele_ids'] = excluded_allele_ids
        return data
