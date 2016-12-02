from vardb.datamodel import allele
from vardb.datamodel.annotation import CustomAnnotation, Annotation
from vardb.datamodel.assessment import AlleleAssessment, ReferenceAssessment, AlleleReport

from api.schemas import AlleleSchema, GenotypeSchema, AnnotationSchema, CustomAnnotationSchema, AlleleAssessmentSchema, ReferenceAssessmentSchema, AlleleReportSchema
from api.util.annotationprocessor import AnnotationProcessor
from api.util.sanger_verification import SangerVerification


# Top level keys:
KEY_REFERENCE_ASSESSMENTS = 'reference_assessments'
KEY_ALLELE_ASSESSMENT = 'allele_assessment'
KEY_ALLELE_REPORT = 'allele_report'
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
                  link_filter=None,
                  genotypes=None,
                  genepanel=None,  # Make genepanel mandatory?
                  include_annotation=True,
                  include_custom_annotation=True,
                  include_allele_assessment=True,
                  include_reference_assessments=True,
                  include_allele_report=True):
        """
        Loads data for a list of alleles from the database, and returns a dictionary
        with the final data, loaded using the allele schema.

        By default the most recent linked entities of the alleles are fetched from database.
        If specific entity ids are given in 'link_filter' those are loaded instead. Any explicitly given entities
        not linked to the alleles will not be part of the returned result

        Annotation is automatically processed using annotationprocessor. If possible, provide
        a genepanel for automatic transcript selection.

        :param alleles: List of allele objects.
        :param link_filter: a struct defining the ids of related entities to fetch. See other parameters for more info.
        :param genotypes: List of genotypes objects. Index of matching genotype object should match allele list index.
        :param genepanel: Genepanel to be used in annotationprocessor.
        :type genepanel: vardb.datamodel.gene.Genepanel
        :param annotation: If true, load the ones mentioned in link_filter.annotation_id
        :param include_custom_annotation: If true, load the ones mentioned in link_filter.customannotation_id
        :param include_allele_assessment: If true, load the ones mentioned in link_filter.alleleassessment_id
        :param include_reference_assessments: If true, load the ones mentioned in link_filter.referenceassessment_id
        :param include_allele_report: If true, load the ones mentioned in link_filter.allelereport_id
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
        #       'reference_assessment': {...} or not present,
        #       'allele_report': {...} or not present
        #    },
        #    id2: ...
        # }

        allele_schema = AlleleSchema()
        genotype_schema = GenotypeSchema()
        accumulated_allele_data = dict()
        for idx, al in enumerate(alleles):
            accumulated_allele_data[al.id] = {KEY_ALLELE: allele_schema.dump(al).data}
            if genotypes:
                genotype = genotypes[idx]
                accumulated_allele_data[al.id][KEY_GENOTYPE] = genotype_schema.dump(genotype).data

        allele_ids = accumulated_allele_data.keys()

        allele_annotations = list()
        if include_annotation:
            annotation_filters = self.setup_entity_filter(Annotation, 'annotation_id', allele_ids, link_filter)
            if annotation_filters:
                allele_annotations = self.session.query(Annotation).filter(*annotation_filters).all()

        allele_custom_annotations = list()
        if include_custom_annotation:
            custom_annotation_filters = self.setup_entity_filter(CustomAnnotation, 'customannotation_id', allele_ids, link_filter)
            if custom_annotation_filters:
                allele_custom_annotations = self.session.query(CustomAnnotation).filter(*custom_annotation_filters).all()

        allele_assessments = list()
        if include_allele_assessment:
            assessment_filters = self.setup_entity_filter(AlleleAssessment, 'alleleassessment_id', allele_ids, link_filter)
            if assessment_filters:
                allele_assessments = self.session.query(AlleleAssessment).filter(*assessment_filters).all()

        reference_assessments = list()
        if include_reference_assessments:
            reference_filters = self.setup_entity_filter(ReferenceAssessment, 'referenceassessment_id', allele_ids, link_filter)
            if reference_filters:
                reference_assessments = self.session.query(ReferenceAssessment).filter(*reference_filters).all()

        allele_reports = list()
        if include_allele_report:
            report_filters = self.setup_entity_filter(AlleleReport, 'allelereport_id', allele_ids, link_filter)
            if report_filters:
                allele_reports = self.session.query(AlleleReport).filter(*report_filters).all()

        # serialize the found entities:
        self.dump(accumulated_allele_data, allele_ids, allele_annotations, AnnotationSchema(), KEY_ANNOTATION)
        self.dump(accumulated_allele_data, allele_ids, allele_custom_annotations, CustomAnnotationSchema(),
                  KEY_CUSTOM_ANNOTATION)
        self.dump(accumulated_allele_data, allele_ids, allele_assessments, AlleleAssessmentSchema(), KEY_ALLELE_ASSESSMENT)
        self.dump(accumulated_allele_data, allele_ids, reference_assessments, ReferenceAssessmentSchema(),
                  KEY_REFERENCE_ASSESSMENTS, use_list=True)
        self.dump(accumulated_allele_data, allele_ids, allele_reports, AlleleReportSchema(), KEY_ALLELE_REPORT)

        # Create final data
        # genepanel_data = GenepanelSchema().dump(genepanel).data
        final_alleles = list()
        for allele_id, data in accumulated_allele_data.iteritems():
            final_allele = data[KEY_ALLELE]

            for key in [KEY_GENOTYPE, KEY_ALLELE_ASSESSMENT, KEY_REFERENCE_ASSESSMENTS, KEY_ALLELE_REPORT]:
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

            final_alleles.append(final_allele)

        return final_alleles

    def dump(self, accumulator, allowed_allele_ids, items, schema, key, use_list=False):
        """

        :param allowed_allele_ids:
        :param accumulator: The dict to mutate with dumped data
        :param items:
        :param schema: the Schema to use for serializing
        :param key: the key in acc to place the dumped data
        :param use_list: the dumped values are appended to a list
        :return:

        """
        for item in items:
            if item.allele_id not in allowed_allele_ids:
                return
            if use_list:
                if key not in accumulator[item.allele_id]:
                    accumulator[item.allele_id][key] = list()
                accumulator[item.allele_id][key].append(schema.dump(item, None, ).data)
            else:
                accumulator[item.allele_id][key] = schema.dump(item, None, ).data

    def setup_entity_filter(self, entity_clazz, key, allele_ids, query_object):
        """
        Create a list of filters for finding entities having a relationship
        with Allele. If the IDs of the entities are not defined in the query object,
        we choose the most recent ones instead of loading the specific ones.

        If query_object is given  we retrieve the entities mentioned there, regardless of there relationship
        with the allele mentioned in allele_ids. If an entity is not related to our alleles, they are discarded anyway
        when stitching together the final response

        :param entity_clazz: The entity to find
        :param key: the key of the query_object where the ids are found
        :param allele_ids: The IDs of Allele the entity class is related to
        :param query_object: a dict with ids of the entities to retrieve
        :return: An array of filters to be used in a session.query
        """
        filters = []

        if query_object and key in query_object:
            list_of_ids = query_object[key] if isinstance(query_object[key], list) else [query_object[key]]
            if len(list_of_ids) > 0:
                filters.append(entity_clazz.id.in_(list_of_ids))
            else:
                return None  # we don't want any entities
        else:
            filters.append(entity_clazz.allele_id.in_(allele_ids))
            filters.append(entity_clazz.date_superceeded == None)

        return filters


if __name__ == '__main__':
    from api import db

    adl = AlleleDataLoader(db.session)
    alleles = db.session.query(allele.Allele).limit(100).all()
    adl.from_objs(alleles)
