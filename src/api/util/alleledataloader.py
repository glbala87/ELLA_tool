import json
from vardb.datamodel import allele, sample, genotype, annotationshadow
from vardb.datamodel.annotation import CustomAnnotation, Annotation
from vardb.datamodel.assessment import AlleleAssessment, ReferenceAssessment, AlleleReport
from sqlalchemy import or_, text

from api.util.util import query_print_table
from api.util import queries
from api.schemas import AlleleSchema, GenotypeSchema, GenotypeSampleDataSchema, AnnotationSchema, CustomAnnotationSchema, AlleleAssessmentSchema, ReferenceAssessmentSchema, AlleleReportSchema, SampleSchema
from api.util.annotationprocessor import AnnotationProcessor
from api.config import config
from .calculate_qc import genotype_calculate_qc


# Top level keys:
KEY_REFERENCE_ASSESSMENTS = 'reference_assessments'
KEY_ALLELE_ASSESSMENT = 'allele_assessment'
KEY_ALLELE_REPORT = 'allele_report'
KEY_CUSTOM_ANNOTATION = 'custom_annotation'
KEY_ANNOTATION = 'annotation'
KEY_GENOTYPE = 'genotype'
KEY_SAMPLES = 'samples'
KEY_ALLELE = 'allele'

KEY_ANNOTATIONS = 'annotations'


class AlleleDataLoader(object):

    def __init__(self, session):
        self.session = session
        self.inclusion_regex = config.get("transcripts", {}).get("inclusion_regex")

    def from_objs(self,
                  alleles,
                  link_filter=None,
                  genepanel=None,  # Make genepanel mandatory?
                  include_genotype_samples=None,
                  include_annotation=True,
                  include_custom_annotation=True,
                  include_allele_assessment=True,
                  include_reference_assessments=True,
                  include_allele_report=True,
                  allele_assessment_schema=None):
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
        :param include_genotype_samples: List of samples ids to include genotypes for.
        :param genepanel: Genepanel to be used in annotationprocessor.
        :type genepanel: vardb.datamodel.gene.Genepanel
        :param annotation: If true, load the ones mentioned in link_filter.annotation_id
        :param include_custom_annotation: If true, load the ones mentioned in link_filter.customannotation_id or, if not provided, the latest data
        :param include_allele_assessment: If true, load the ones mentioned in link_filter.alleleassessment_id or, if not provided, the latest data
        :param include_reference_assessments: If true, load the ones mentioned in link_filter.referenceassessment_id or, if not provided, the latest data
        :param include_allele_report: If true, load the ones mentioned in link_filter.allelereport_id or, if not provided, the latest data
        :param allele_assessment_schema: Use this schema for serialization. If None, use default
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
        sample_schema = SampleSchema()
        accumulated_allele_data = dict()
        allele_ids = list() # To keep input order

        for al in alleles:
            accumulated_allele_data[al.id] = {KEY_ALLELE: allele_schema.dump(al).data}
            allele_ids.append(al.id)

        if include_genotype_samples:
            samples = self.session.query(sample.Sample).filter(
                sample.Sample.id.in_(include_genotype_samples)
            ).all()
            for sample_id in include_genotype_samples:
                sample_obj = next(s for s in samples if s.id == int(sample_id))

                genotypes = self.session.query(genotype.Genotype).filter(
                    genotype.Genotype.sample_id == sample_id,
                    or_(
                        genotype.Genotype.allele_id.in_(allele_ids) if allele_ids else False,
                        genotype.Genotype.secondallele_id.in_(allele_ids) if allele_ids else False,
                    )
                ).all()


                # Add genotype into ['samples'][n]['genotype']
                if genotypes:
                    genotypesampledata = self.session.query(genotype.GenotypeSampleData).filter(
                        genotype.GenotypeSampleData.sample_id == sample_id,
                        genotype.GenotypeSampleData.genotype_id.in_([g.id for g in genotypes])
                    ).all()

                    for gt in genotypes:
                        for attr in ['allele_id', 'secondallele_id']:
                            allele_id = getattr(gt, attr)
                            # If both gt.allele_id and gt.secondallele_id has data, one might not be in required list
                            if allele_id is not None and allele_id in accumulated_allele_data:
                                if KEY_SAMPLES not in accumulated_allele_data[allele_id]:
                                    accumulated_allele_data[allele_id][KEY_SAMPLES] = list()
                                sample_serialized = sample_schema.dump(sample_obj).data  # We need to recreate here, we cannot reuse sample object
                                genotype_data = genotype_schema.dump(gt).data
                                sample_genotypesampledata = next(gsd for gsd in genotypesampledata if gsd.genotype_id == gt.id and gsd.secondallele == bool(attr == 'secondallele_id'))
                                genotype_data.update(
                                    GenotypeSampleDataSchema().dump(sample_genotypesampledata).data
                                )
                                genotype_data.update(
                                    genotype_calculate_qc(
                                        accumulated_allele_data[allele_id]['allele'],
                                        genotype_data,
                                        sample_serialized["sample_type"]
                                    )
                                )
                                sample_serialized[KEY_GENOTYPE] = genotype_data
                                accumulated_allele_data[allele_id][KEY_SAMPLES].append(sample_serialized)

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
        self.dump(accumulated_allele_data, allele_ids, allele_assessments, allele_assessment_schema() if allele_assessment_schema else AlleleAssessmentSchema(), KEY_ALLELE_ASSESSMENT)
        self.dump(accumulated_allele_data, allele_ids, reference_assessments, ReferenceAssessmentSchema(),
                  KEY_REFERENCE_ASSESSMENTS, use_list=True)
        self.dump(accumulated_allele_data, allele_ids, allele_reports, AlleleReportSchema(), KEY_ALLELE_REPORT)

        # Create final data

        # If genepanel is provided, get annotation transcripts filtered on genepanel
        annotation_transcripts = None
        if genepanel:
            annotation_transcripts_genepanel = queries.annotation_transcripts_genepanel(
                self.session,
                [(genepanel.name, genepanel.version)]
            ).subquery()
            annotation_transcripts = self.session.query(
                annotation_transcripts_genepanel.c.allele_id,
                annotation_transcripts_genepanel.c.annotation_transcript,
            ).filter(
                annotation_transcripts_genepanel.c.allele_id.in_(allele_ids)
            ).all()

        inclusion_regex_filtered = None
        if self.inclusion_regex:
            inclusion_regex_filtered = self.session.query(
                annotationshadow.AnnotationShadowTranscript.allele_id,
                annotationshadow.AnnotationShadowTranscript.transcript
            ).filter(
                annotationshadow.AnnotationShadowTranscript.allele_id.in_(allele_ids) if allele_ids else False,
                text("transcript ~ :reg").params(reg=self.inclusion_regex)
            ).distinct().all()

        final_alleles = list()
        for allele_id in allele_ids:
            data = accumulated_allele_data[allele_id]
            final_allele = data[KEY_ALLELE]
            for key in [KEY_SAMPLES, KEY_ALLELE_ASSESSMENT, KEY_REFERENCE_ASSESSMENTS, KEY_ALLELE_REPORT]:
                if key in data:
                    final_allele[key] = data[key]

            if KEY_ANNOTATION in data:

                # Copy data to avoid mutating db object.
                # json -> much faster than copy.deepcopy
                annotation_data = json.loads(json.dumps(data[KEY_ANNOTATION][KEY_ANNOTATIONS]))

                # 'filtered_transcripts' -> transcripts in our genepanel
                filtered_transcripts = []
                if annotation_transcripts:
                    filtered_transcripts = list(set([a.annotation_transcript for a in annotation_transcripts if a.allele_id == allele_id]))

                # Filter main transcript list on inclusion regex
                # (if in filtered_transcripts, don't exclude it)
                if inclusion_regex_filtered and 'transcripts' in annotation_data:
                    allele_regex_filtered = [t[1] for t in inclusion_regex_filtered if t[0] == allele_id]
                    annotation_data['transcripts'] = \
                        [t for t in annotation_data['transcripts'] \
                         if (t['transcript'] in allele_regex_filtered or t['transcript'] in filtered_transcripts)]

                # Convert annotation using annotationprocessor
                processed_annotation = AnnotationProcessor.process(
                    annotation_data,
                    custom_annotation=data.get(KEY_CUSTOM_ANNOTATION, {}).get(KEY_ANNOTATIONS),
                    genepanel=genepanel
                )
                final_allele[KEY_ANNOTATION] = processed_annotation

                final_allele[KEY_ANNOTATION]['filtered_transcripts'] = sorted(filtered_transcripts)
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
            filters.append(entity_clazz.allele_id.in_(allele_ids) if allele_ids else False)
            filters.append(entity_clazz.date_superceeded == None)

        return filters


if __name__ == '__main__':
    from api import db

    adl = AlleleDataLoader(db.session)
    alleles = db.session.query(allele.Allele).limit(100).all()
    adl.from_objs(alleles)
