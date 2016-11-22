import datetime

from vardb.datamodel import assessment

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
from api.util.assessmentcreator import AssessmentCreator
from api.v1.resource import Resource


class AlleleAssessmentResource(Resource):

    def get(self, session, aa_id=None):
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

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=10000):
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

    @request_json(
        [
            'allele_id',
            'classification',
            'user_id',
        ],
        allowed=[
            # 'id' is excluded on purpose, as the endpoint should always result in a new assessment
            'analysis_id',
            'genepanel_name',
            'genepanel_version',
            'evaluation',
            'previous_assessment_id',
            'referenceassessments'
        ]
    )
    def post(self, session, data=None):
        """
        Creates a new AlleleAssessment(s) for a given allele(s).

        If any AlleleAssessment exists already for the same allele, it will be marked as superceded.

        **If assessment should be created as part of finalizing an analysis, check the `analyses/{id}/finalize` resource instead.**

        POST data example:
        ```
        {
            # New assessment will be created, superceding any old one
            "user_id": 1,
            "allele_id": 2,
            "classification": "3",
            "reuse": false,
            "evaluation": {...data...},
            "analysis_id": 3,  # Optional, should be given when assessment is made in context of analysis
            "genepanel_name": "HBOC", # Optional only if analysis_id provided
            "genepanel_version": "v01", # Optional only if analysis_id provided

            "referenceassessments": [  # Optional
                {
                    "allele_id": 2,
                    "analysis_id": 3,
                    "evaluation": {...data...}
                },
                {
                    "analysis_id": 3,
                    "allele_id": 2,
                    "id": 3  # Reuse existing referenceassessment, but link it to this alleleassessment
                }
            ]
        }

        # TODO: what's the role of this as opposed to api/v1/resources/analysis.py?

        ```
        Provided data can also be a list of items.

        ---
        summary: Create alleleassessment
        tags:
          - AlleleAssessment
        parameters:
          - name: data
            in: body
            required: true
            schema:
              type: array
              items:
                title: AlleleAssessment data
                type: object
                required:
                  - user_id
                  - allele_id
                  - evaluation
                  - classification
                properties:
                  user_id:
                    description: User id
                    type: integer
                  analysis_id:
                    description: Analysis id
                    type: integer
                  genepanel_name:
                    description: Genepanel name. Required if no analysis id
                    type: string
                  genepanel_version:
                    description: Genepanel version. Required if no analysis id
                    type: string
                  allele_id:
                    description: Allele id
                    type: integer
                  evaluation:
                    description: Evaluation data object
                    type: object
                  classification:
                    description: Classification
                    type: string
                  referenceassessments:
                    name: referenceassessment
                    type: array
                    items:
                      title: ReferenceAssessment
                      type: object
                      required:
                        - allele_id
                        - reference_id
                      properties:
                        id:
                          description: Existing referenceassessment id. If provided, existing object will be linked to alleleassessment.
                          type: integer
                        user_id:
                          description: User id. Required if not reusing existing object
                          type: integer
                        analysis_id:
                          description: Analysis id. Required if not reusing existing object
                          type: integer
                        allele_id:
                          description: Allele id
                          type: integer
                        reference_id:
                          description: Reference id
                          type: integer
                        evaluation:
                          description: Evaluation data object
                          type: object
              example:
                - user_id: 3
                  allele_id: 2
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
                - user_id: 3
                  allele_id: 3
                  classification: "4"
                  evaluation: {}
                  genepanel_name: "HBOC"
                  genepanel_version: "v01"
            description: Submitted data
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/AlleleAssessment'
            description: List of created alleleassessments
        """

        if not isinstance(data, list):
            data = [data]

        ac = AssessmentCreator(session)
        result = ac.create_from_data(alleleassessments=data)
        # un-tuple:
        aa = map(lambda x: x[0], result['alleleassessments']['reused'])\
             + map(lambda x: x[1], result['alleleassessments']['created'])

        if not isinstance(data, list):
            aa = aa[0]

        session.commit()
        return schemas.AlleleAssessmentSchema().dump(aa, many=isinstance(aa, list)).data
