from vardb.datamodel import allele, assessment, annotation

from api.schemas import AlleleSchema, GenotypeSchema, AnnotationSchema, CustomAnnotationSchema, AlleleAssessmentSchema, ReferenceAssessmentSchema, GenepanelSchema
from api.util.annotationprocessor import AnnotationProcessor
from api.util.sanger_verification import SangerVerification


# Top level keys:
KEY_REFERENCE_ASSESSMENTS = 'reference_assessments'
KEY_ALLELE_ASSESSMENT = 'allele_assessment'
KEY_CUSTOM_ANNOTATION = 'custom_annotation'
KEY_ANNOTATION = 'annotation'
KEY_GENOTYPE = 'genotype'
KEY_ALLELE = 'allele'

KEY_ANNOTATIONS = 'annotations'


class AlleleDataLoader(object):

    def __init__(self, session):
        self.session = session

    def from_objs(self,
                  alleles,
                  genotypes=None,
                  genepanel=None,
                  include_annotation=True,
                  include_custom_annotation=True,
                  include_allele_assessment=True,
                  include_reference_assessments=True):
        """
        Loads data for a list of alleles from the database, and returns a dictionary
        with the final data, loaded using the allele schema.

        Annotation is automatically processed using annotationprocessor. If possible, provide
        a genepanel for automatic transcript selection.

        :param alleles: List of allele objects.
        :param genotypes: List of genotypes objects. Index of matching genotype object should match allele list index.
        :param genepanel: Genepanel to be used in annotationprocessor.
        :type genepanel: vardb.datamodel.gene.Genepanel
        :param annotation: Load current valid annotation data.
        :param custom_annotation: Load current valid custom annotation data.
        :param allele_assessment: Load current valid allele assessment
        :param reference_assessments: Load current valid reference assessments
        :returns: dict with converted data using schema data.
        """

        # Load data and group into a temporary dictionary for internal usage
        # It will look like this in the end ({...} means data loaded using schema):
        # {
        #    id1: {
        #       'allele': {...},
        #       'genotype': {...} or not present,
        #       'annotation': {...} or not present,
        #       'custom_annotation': {...} or not present,
        #       'allele_assessment': {...} or not present,
        #       'reference_assessment': {...} or not present
        #    },
        #    id2: ...
        # }

        allele_schema = AlleleSchema()
        genotype_schema = GenotypeSchema()
        allele_data = dict()
        for idx, al in enumerate(alleles):
            allele_data[al.id] = {KEY_ALLELE: allele_schema.dump(al).data}
            if genotypes:
                genotype = genotypes[idx]
                allele_data[al.id][KEY_GENOTYPE] = genotype_schema.dump(genotype).data

        ids = allele_data.keys()
        if include_annotation:
            annotation_schema = AnnotationSchema()
            allele_annotations = self.session.query(annotation.Annotation).filter(
                annotation.Annotation.allele_id.in_(ids),
                annotation.Annotation.dateSuperceeded == None
            ).all()
            for allele_annotation in allele_annotations:
                allele_data[allele_annotation.allele_id][KEY_ANNOTATION] = annotation_schema.dump(allele_annotation).data

        if include_custom_annotation:
            custom_annotation_schema = CustomAnnotationSchema()
            allele_custom_annotations = self.session.query(annotation.CustomAnnotation).filter(
                annotation.CustomAnnotation.allele_id.in_(ids),
                annotation.CustomAnnotation.dateSuperceeded == None
            ).all()
            for allele_custom_annotation in allele_custom_annotations:
                allele_data[allele_custom_annotation.allele_id][KEY_CUSTOM_ANNOTATION] = custom_annotation_schema.dump(allele_custom_annotation).data

        if include_allele_assessment:
            aa_schema = AlleleAssessmentSchema()
            allele_assessments = self.session.query(assessment.AlleleAssessment).filter(
                assessment.AlleleAssessment.allele_id.in_(ids),
                assessment.AlleleAssessment.dateSuperceeded == None
            ).all()
            for aa in allele_assessments:
                allele_data[aa.allele_id][KEY_ALLELE_ASSESSMENT] = aa_schema.dump(aa).data

        if include_reference_assessments:
            ra_schema = ReferenceAssessmentSchema()
            reference_assessments = self.session.query(assessment.ReferenceAssessment).filter(
                assessment.ReferenceAssessment.allele_id.in_(ids),
                assessment.ReferenceAssessment.dateSuperceeded == None
            ).all()
            for ra in reference_assessments:
                if KEY_REFERENCE_ASSESSMENTS not in allele_data[ra.allele_id]:
                    allele_data[ra.allele_id][KEY_REFERENCE_ASSESSMENTS] = list()
                allele_data[ra.allele_id][KEY_REFERENCE_ASSESSMENTS].append(ra_schema.dump(ra).data)

        # Create final data
        # genepanel_data = GenepanelSchema().dump(genepanel).data
        final_alleles = list()
        for allele_id, data in allele_data.iteritems():
            final_allele = data[KEY_ALLELE]

            for key in [KEY_GENOTYPE, KEY_ALLELE_ASSESSMENT, KEY_REFERENCE_ASSESSMENTS]:
                if key in data:
                    final_allele[key] = data[key]

            if KEY_ANNOTATION in data:
                # Convert annotation using annotationprocessor
                processed_annotation = AnnotationProcessor.process(
                    data[KEY_ANNOTATION][KEY_ANNOTATIONS],
                    genotype=data.get(KEY_GENOTYPE),
                    custom_annotation=data.get(KEY_CUSTOM_ANNOTATION, {}).get(KEY_ANNOTATIONS),
                    genepanel=genepanel
                )
                final_allele[KEY_ANNOTATION] = processed_annotation
                final_allele[KEY_ANNOTATION]['annotation_id'] = data[KEY_ANNOTATION]['id']

                if KEY_CUSTOM_ANNOTATION in data:
                    final_allele[KEY_ANNOTATION]['custom_annotation_id'] = data[KEY_CUSTOM_ANNOTATION]['id']

                # Add sanger verification check
                if KEY_GENOTYPE in data:
                    final_allele[KEY_ANNOTATION]['quality']['needs_verification'] = SangerVerification().needs_verification(final_allele)


            final_alleles.append(final_allele)

        return final_alleles


if __name__ == '__main__':
    from api import db

    adl = AlleleDataLoader(db.session)
    alleles = db.session.query(allele.Allele).limit(100).all()
    adl.from_objs(alleles)
