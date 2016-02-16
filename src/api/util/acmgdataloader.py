from .alleledataloader import AlleleDataLoader

from api import schemas, config

from rule_engine.gre import GRE
from rule_engine.grc import ACMGClassifier2015
from rule_engine.mapping_rules import rules


class ACMGDataLoader(object):

    def __init__(self, session):
        self.session = session

    def _set_transcript_annotation(self, annotation_data):
        # Set the default transcript to use. Normally this one
        # transcript from filtered_transcripts in the annotation data
        # which is set using the genepanel as a filter.
        # If there is more than one transcript, or no transcript,
        # set it to None as the rules only support one transcript.
        # It should almost always be just one transcript.
        filtered_transcripts = annotation_data.get('filtered_transcripts', [])
        if len(filtered_transcripts) == 1:
            # Fetch transcript data from 'transcripts' key, given transcript
            # name from filtered_transcripts[0].
            transcript = next((t for t in annotation_data['transcripts'] if t['Transcript'] == filtered_transcripts[0]), None)
            annotation_data["transcript"] = transcript
        else:
            annotation_data['transcript'] = None

    def _get_genepanel_annotation(self, genepanel):
        """
        :param genepanel: Genepanel in dumped schema format
        """
        # Currently just using default values
        return {
            "gp_inheritance": "autosomal_dominant",
            "gp_last_exon": "last_exon_important",
            "gp_disease_mode": "lof_missense"
        }.update(config.config['acmg']['freq_cutoff_defaults'])

    def _classify(self, annotation_data):
        passed, nonpassed = GRE().query(rules, annotation_data)
        passed_data = schemas.RuleSchema().dump(passed, many=True).data
        classification = ACMGClassifier2015().classify(passed)
        classification_data = schemas.ClassificationSchema().dump(classification).data
        return classification_data, passed_data

    def from_data(self,
                  alleles,
                  reference_assessments,
                  genepanel):
        """
        Calculates ACMG codes for a list of alleles already preloaded using the AlleleDataLoader.
        They must have been loaded with include_annotation and include_custom_annotation.
        A dictionary with the final data is returned, with allele id as keys.

        :param alleles: List of allele data from AlleleDataLoader.
        :param reference_assessments: List of ReferenceAssessment model objects to use.
        :param genepanel: Genepanel to be used in annotationprocessor.
        :returns: dict with converted data using schema data.
        """

        gp_annotation_data = self._get_genepanel_annotation(genepanel)
        allele_classifications = dict()
        for a in alleles:
            # Add extra data/keys that the rule engine expects to be there
            annotation_data = a['annotation']
            annotation_data["genepanel"] = gp_annotation_data
            annotation_data["refassessment"] = {str(r.id): r.evaluation for r in reference_assessments if r.allele_id == a['id']}
            self._set_transcript_annotation(annotation_data)

            classification_data, passed_data = self._classify(annotation_data)
            allele_classifications[a['id']] = {
                'classification': classification_data,
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

        :param alleles: List of allele objects.
        :param reference_assessments: List of ReferenceAssessment objects to use.
        :param genepanel: Genepanel to be used.
        :returns: dict with converted data using schema data.
        """
        loaded_alleles = AlleleDataLoader(self.session).from_objs(
            alleles,
            genepanel=genepanel,
            include_allele_assessment=False,
            include_reference_assessments=False
        )
        return self.from_data(
            loaded_alleles,
            reference_assessments,
            genepanel
        )
