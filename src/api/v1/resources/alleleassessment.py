from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, request_json, authenticate
from api.util.assessmentcreator import AssessmentCreator
from api.v1.resource import Resource


class AlleleAssessmentResource(Resource):

    @authenticate()
    def get(self, session, aa_id=None, user=None):
        """
        Returns a single alleleassessment.
        ---
        summary: Get alleleassessment
        tags:
          - AlleleAssessment
        parameters:
          - name: aa_id
            in: path
            type: integer
            description: AlleleAssessment id
        responses:
          200:
            schema:
                $ref: '#/definitions/AlleleAssessment'
            description: AlleleAssessment object
        """
        a = session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.id == aa_id
        ).one()
        result = schemas.AlleleAssessmentSchema(strict=True).dump(a).data
        return result


class AlleleAssessmentListResource(Resource):

    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=10000, user=None):
        """
        Returns a list of alleleassessments.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List alleleassessments
        tags:
          - AlleleAssessment
        parameters:
          - name: q
            in: query
            type: string
            description: JSON filter query
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/AlleleAssessment'
            description: List of alleleassessments
        """
        # TODO: Figure out how to deal with pagination
        return self.list_query(
            session,
            assessment.AlleleAssessment,
            schemas.AlleleAssessmentSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            num_per_page=num_per_page
        )

    @authenticate()
    @request_json(
        ["allele_assessments", "annotations"],
        # required fields for dict of dict not supported
        allowed={
            "allele_assessments": [
                'allele_id',
                'analysis_id',
                'classification',
                'genepanel_name',
                'genepanel_version',
                'evaluation',
                'previous_assessment_id',
                'referenceassessments'
            ],
            "custom_annotations": [
                'custom_annotation_id',
                'allele_id',
            ],
            "annotations": [
                'annotation_id',
                'allele_id',
            ]
        })
    def post(self, session, data=None, user=None):
        """
        Creates a new AlleleAssessment(s) for a given allele(s).

        If any AlleleAssessment exists already for the same allele, it will be marked as superceded.
        If assessment should be created as part of finalizing an analysis, check the `analyses/{id}/finalize` resource instead.

        ---
        summary: Create alleleassessment
        tags:
          - AlleleAssessment
        parameters:
          - name: data
            in: body
            required: true
            schema:
              title: Data object
              type: object
              required:
                - annotations
                - allele_assessments
              properties:
                annotations:
                  description: annotatation for the allele to assess
                  type: array
                  items:
                    type: object
                    required:
                      - annotation_id
                      - allele_id
                    properties:
                      annotation_id:
                        type: integer
                      allele_id:
                        type: integer
                allele_assessments:
                  "description": our assessment data
                  type: array
                  items:
                    "$ref": "#/definitions/AlleleAssessmentInput"
                custom_annotations:
                  "description": "custom annotation for the allele"
                  type: array
                  items:
                    type: object
                    required:
                      - custom_annotation_id
                      - allele_id
                    properties:
                      custom_annotation_id:
                        type: integer
                      allele_id:
                        type: integer
              example:
                annotations:
                  - annotation_id: 12
                    allele_id: 1
                custom_annotations:
                  - custom_annotation_id: 45
                    allele_id: 4
                allele_assessments:
                    - allele_id: 2
                      classification: "3"
                      evaluation: {}
                      analysis_id: 3
                      referenceassessments:
                        - allele_id: 2
                          reference_id: 53
                          analysis_id: 3
                          evaluation: {}
                        - id: 3
                          allele_id: 2
                          reference_id: 23
                    - allele_id: 3
                      classification: "4"
                      evaluation: {}
                      genepanel_name: "HBOC"
                      genepanel_version: "v01"
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/AlleleAssessment'
            description: List of created alleleassessments
        """

        annotations = data["annotations"]
        custom_annotations = data["custom_annotations"] if "custom_annotations" in data else None
        allelele_assessments = data["allele_assessments"]

        ac = AssessmentCreator(session)
        grouped_alleleassessments = ac.create_from_data(
            user.id,
            annotations,
            allelele_assessments,
            custom_annotations=custom_annotations
        )
        created_alleleassessments = grouped_alleleassessments['alleleassessments']['created']

        session.add_all(created_alleleassessments)
        session.commit()

        return schemas.AlleleAssessmentSchema().dump(created_alleleassessments, many=True).data
