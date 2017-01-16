from collections import defaultdict

from api import schemas
from rule_engine.grc import ACMGClassifier2015
from rule_engine.gre import GRE
from rule_engine.mapping_rules import rules
from api.util.genepanelconfig import GenepanelConfigResolver
from .alleledataloader import AlleleDataLoader


class ACMGDataLoader(object):

    def __init__(self, session):
        self.session = session

    @staticmethod
    def _find_single_transcript(annotation_data):
        # Find default transcript to use. Normally this one
        # transcript from filtered_transcripts in the annotation data
        # which is set using the genepanel as a filter.
        # If there is more than one transcript, or no transcript,
        # set it to None as the rules only support one transcript.
        # It should almost always be just one transcript.
        filtered_transcripts = annotation_data.get('filtered_transcripts', [])
        if len(filtered_transcripts) == 1:
            # Fetch transcript data from 'transcripts' key, given transcript
            # name from filtered_transcripts[0].
            return next((t for t in annotation_data['transcripts'] if t['transcript'] == filtered_transcripts[0]), None)
        else:
            return None

    def get_classification(self, codes):
        """
        Gets the final classification based on a given list of ACMG codes.

        :param codes: List of ACMG codes (str), e.g. ['PP1', 'BP2', ..]
        :returns: Dict with class, classification string and a list of codes that were used
        """
        classification = ACMGClassifier2015().classify(codes)
        classification_data = schemas.ClassificationSchema().dump(classification).data
        return classification_data

    def get_acmg_codes(self, annotation_data):
        """
        Calculates ACMG codes from the rules for the given annotation data.

        Example input:
        annotation_data = [
            "annotation": {...}  # From annotation processor
            "refassessment": {
                "alleleid_refid": {evaluation data}
            }
        ]

        :param annotation_data: List of annotation data dicts
        :returns: List of ACMG codes (dicts)
        """
        passed, nonpassed = GRE().query(rules, annotation_data)
        passed_data = schemas.RuleSchema().dump(passed, many=True).data
        return passed_data

    def _from_data(self,
                   alleles,
                   reference_assessments,
                   genepanel):
        """
        Calculates ACMG codes for a list of alleles already preloaded using the AlleleDataLoader.
        They must have been loaded with include_annotation and include_custom_annotation.
        A dictionary with the final data is returned, with allele id as keys.

        :param alleles: List of allele data from AlleleDataLoader.
        :param reference_assessments: List of referenceassessments (dicts) to use.
        :param genepanel: Genepanel to be used in annotationprocessor.
        :type genepanel: vardb.datamodel.gene.Genepanel
        :returns: dict with converted data using schema data.
        """

        resolver = GenepanelConfigResolver(genepanel)

        allele_classifications = dict()

        ra_per_allele = defaultdict(list)
        for ra in reference_assessments:
            ra_per_allele[ra['allele_id']].append(ra)

        for a in alleles:
            # Add extra data/keys that the rule engine expects to be there
            annotation_data = a['annotation']

            if a['id'] in ra_per_allele:
                annotation_data["refassessment"] = {str('_'.join([str(r['allele_id']), str(r['reference_id'])])): r['evaluation'] for r in ra_per_allele[a['id']]}

            transcript = ACMGDataLoader._find_single_transcript(annotation_data)
            annotation_data['transcript'] = transcript
            if transcript:
                annotation_data["genepanel"] = resolver.resolve(transcript['symbol'])
            else:
                annotation_data["genepanel"] = resolver.resolve(None)

            passed_data = self.get_acmg_codes(annotation_data)
            allele_classifications[a['id']] = {
                'codes': passed_data
            }
        return allele_classifications

    def from_objs(self,
                  alleles,
                  reference_assessments,
                  genepanel):
        """
        Calculates ACMG codes for a list of alleles model objects.
        A dictionary with the final data is returned, with allele.id as keys.

        Annotation data will be loaded automatically, using the AlleleDataLoader. If you already
        have alleles loaded with the AlleleDataLoader, see from_data().

        :param alleles: List
        :type alleles: vardb.datamodel.allele.Allele
        :param reference_assessments: List of referenceassessments (dicts) to use.
        :param genepanel: Genepanel to be used.
        :type genepanel: vardb.datamodel.gene.Genepanel
        :returns: dict with converted data using schema data.
        """

        loaded_alleles = None
        if alleles:
            loaded_alleles = AlleleDataLoader(self.session).from_objs(
                alleles,
                genepanel=genepanel,
                include_allele_assessment=False,
                include_reference_assessments=False
            )
        return self._from_data(
            loaded_alleles,
            reference_assessments,
            genepanel
        )
