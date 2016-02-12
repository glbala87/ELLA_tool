from vardb.datamodel import allele, assessment, annotation

from api.schemas import AlleleSchema, GenotypeSchema, AnnotationSchema, CustomAnnotationSchema, AlleleAssessmentSchema, ReferenceAssessmentSchema, GenepanelSchema
from api.util.annotationprocessor import AnnotationProcessor


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
            allele_data[al.id] = {'allele': allele_schema.dump(al).data}
            if genotypes:
                genotype = genotypes[idx]
                allele_data[al.id]['genotype'] = genotype_schema.dump(genotype).data

        ids = allele_data.keys()
        if include_annotation:
            annotation_schema = AnnotationSchema()
            allele_annotations = self.session.query(annotation.Annotation).filter(
                annotation.Annotation.allele_id.in_(ids),
                annotation.Annotation.dateSuperceeded == None
            ).all()
            for allele_annotation in allele_annotations:
                allele_data[allele_annotation.allele_id]['annotation'] = annotation_schema.dump(allele_annotation).data

        if include_custom_annotation:
            custom_annotation_schema = CustomAnnotationSchema()
            allele_custom_annotations = self.session.query(annotation.CustomAnnotation).filter(
                annotation.CustomAnnotation.allele_id.in_(ids),
                annotation.CustomAnnotation.dateSuperceeded == None
            ).all()
            for allele_custom_annotation in allele_custom_annotations:
                allele_data[allele_custom_annotation.allele_id]['custom_annotation'] = custom_annotation_schema.dump(allele_custom_annotation).data

        if include_allele_assessment:
            aa_schema = AlleleAssessmentSchema()
            allele_assessments = self.session.query(assessment.AlleleAssessment).filter(
                assessment.AlleleAssessment.allele_id.in_(ids),
                assessment.AlleleAssessment.dateSuperceeded == None,
                assessment.AlleleAssessment.status == 1  # Curated only
            ).all()
            for aa in allele_assessments:
                allele_data[aa.allele_id]['allele_assessment'] = aa_schema.dump(aa).data

        if include_reference_assessments:
            ra_schema = ReferenceAssessmentSchema()
            reference_assessments = self.session.query(assessment.ReferenceAssessment).filter(
                assessment.ReferenceAssessment.allele_id.in_(ids),
                assessment.ReferenceAssessment.dateSuperceeded == None,
                assessment.ReferenceAssessment.status == 1  # Curated only
            ).all()
            for ra in reference_assessments:
                if 'reference_assessments' not in allele_data[ra.allele_id]:
                    allele_data[ra.allele_id]['reference_assessments'] = list()
                allele_data[ra.allele_id]['reference_assessments'].append(ra_schema.dump(ra).data)

        # Create final data
        genepanel = GenepanelSchema().dump(genepanel).data
        final_alleles = list()
        for allele_id, data in allele_data.iteritems():
            final_allele = data['allele']

            if 'annotation' in data:
                # Convert annotation using annotationprocessor
                processed_annotation = AnnotationProcessor.process(
                    data['annotation']['annotations'],
                    genotype=data.get('genotype'),
                    custom_annotation=data.get('custom_annotation', {}).get('annotations'),
                    genepanel=genepanel
                )
                final_allele['annotation'] = processed_annotation
                final_allele['annotation']['annotation_id'] = data['annotation']['id']

                if 'custom_annotation' in data:
                    final_allele['annotation']['custom_annotation_id'] = data['custom_annotation']['id']

            for key in ['genotype', 'allele_assessment', 'reference_assessments']:
                if key in data:
                    final_allele[key] = data[key]

            final_alleles.append(final_allele)

        return final_alleles


if __name__ == '__main__':
    from api import db

    adl = AlleleDataLoader(db.session)
    alleles = db.session.query(allele.Allele).limit(100).all()
    adl.from_objs(alleles)
