from flask import request

from api.util.util import request_json
from api.v1.resource import Resource

from . import helpers


class AlleleInterpretationResource(Resource):

    def get(self, session, allele_id, interpretation_id):
        """
        Returns current alleleinterpretation for allele.
        ---
        summary: Get current interpretation
        tags:
          - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
        responses:
          200:
            schema:
                $ref: '#/definitions/AlleleInterpretation'
            description: AnalysisInterpretation object
        """
        return helpers.get_interpretation(session, alleleinterpretation_id=interpretation_id)

    @request_json(
        [],
        allowed=[
            'state',
            'user_state',
            'user_id'
        ]
    )
    def patch(self, session, allele_id, interpretation_id, data=None):
        """
        Updates current interpretation inplace.

        **Only allowed for interpretations that are `Ongoing`**
        ---
        summary: Update interpretation
        tags:
          - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
          - data:
            in: body
            required: true
            schema:
              title: AlleleInterpretation data
              type: object
              required:
                - id
              properties:
                id:
                  description: Id of object to update
                  type: integer
                user_id:
                  description: User id of user performing update
                  type: integer
                state:
                  description: State data
                  type: object
                user_state:
                  description: User state data
                  type: object
        responses:
          200:
            type: null
            description: OK
        """

        helpers.update_interpretation(session, data, alleleinterpretation_id=interpretation_id)
        session.commit()

        return None, 200


class AlleleInterpretationAllelesListResource(Resource):

    def get(self, session, allele_id, interpretation_id):

        allele_ids = request.args.get('allele_ids').split(',')
        return helpers.get_alleles(session, allele_ids, alleleinterpretation_id=interpretation_id)


class AlleleInterpretationListResource(Resource):

    def get(self, session, allele_id):
        """
        Returns all interpretations for allele.
        ---
        summary: Get interpretations
        tags:
          - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/AlleleInterpretation'

            description: AlleleInterpretation objects
        """

        return helpers.get_interpretations(session, allele_id=allele_id)


class AlleleActionOverrideResource(Resource):

    @request_json(['user_id'])
    def post(self, session, allele_id, data=None):
        """
        Lets an user take over an allele, by replacing the
        allele's current interpretation's user_id with the input user_id.

        **Only works for alleles with an `Ongoing` current interpretation**
        ---
        summary: Assign allele to another user
        tags:
            - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
          - name: data
            in: body
            type: object
            required: true
            schema:
              title: User id object
              required:
                - user_id
              properties:
                user_id:
                  type: integer
                example:
                  user_id: 1
            description: User id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        helpers.override_interpretation(session, data, allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionStartResource(Resource):

    @request_json(['user_id', 'gp_name', 'gp_version'])
    def post(self, session, allele_id, data=None):
        """
        Starts an alleleinterpretation.

        If no alleleinterpretations exists for given allele id, one is created.

        If all interpretations are 'Done', an error will be returned.
        Use the `/reopen/` action to reopen such an workflow.
        ---
        summary: Start allele interpretation
        tags:
            - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
          - name: data
            in: body
            type: object
            required: true
            schema:
              title: User id object
              required:
                - user_id
              properties:
                user_id:
                  type: integer
              example:
                user_id: 1
            description: User id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.start_interpretation(session, data, allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionMarkReviewResource(Resource):

    @request_json(
        [
            'alleleassessments',
            'annotations',
            'custom_annotations',
            'allelereports'
        ]
    )
    def post(self, session, allele_id, data=None):
        """
        Marks an allele interpretation for review.

        This sets the alleles current interpretation's status to `Done` and creates
        a new current interpretation with status `Not started`.

        **Only works for alleles with a `Ongoing` current interpretation**
        ---
        summary: Mark allele for review
        tags:
          - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
          - name: data
            in: body
            type: object
            required: true
            schema:
              title: User id object
              required:
                - user_id
              properties:
                user_id:
                  type: integer
              example:
                user_id: 1
            description: User id
        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.markreview_interpretation(session, data, allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionReopenResource(Resource):

    def post(self, session, allele_id):
        """
        Reopens an allele workflow that has previously been finalized.

        This creates a new current interpretation for the allele,
        with status set to `Not started`.

        ---
        summary: Reopen allele workflow
        tags:
          - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
          - name: data
            in: body
            type: object
            required: true
            schema:
                title: User id object
                required:
                    - user_id
                properties:
                    user_id:
                        type: integer
                example:
                    user_id: 1
            description: User id
        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.reopen_interpretation(session, allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionFinalizeResource(Resource):

    @request_json(
        [
            'alleleassessments',
            'referenceassessments',
            'allelereports'
        ]
    )
    def post(self, session, allele_id, data=None):
        """
        Finalizes an analysis.

        This sets the analysis' current interpretation's status to `Done` and creates
        any [alleleassessment|referenceassessment|allelereport] objects for the provided alleles,
        unless it's specified to reuse the existing objects.

        You must provide a list of assessments/reports.
        For each assessment/report, if an 'id' field is not part of the data, it will create
        a new assessments/reports in the database.
        It will then link the analysis to these assessments/reports.

        If an 'id' field does exist, it will check if the assessment/report with this id
        exists in the database, then link the analysis to this assessment/report. If the 'id' doesn't
        exists, an ApiError is given.

        In other words, if reusing a preexisting assessment/report, you can pass in just it's 'id',
        otherwise pass in all the data needed to create a new assessment/report (without an 'id' field).

        **Only works for analyses with a `Ongoing` current interpretation**

        ```javascript
        Example POST data:
        {
            "referenceassessments": [
                {
                    // New assessment will be created, superceding any old one
                    "user_id": 1,
                    "analysis_id": 3,
                    "reference_id": 123
                    "evaluation": {...data...},
                    "analysis_id": 3,
                    "allele_id": 14,
                },
                {
                    // Reusing assessment
                    "id": 13,
                    "allele_id": 13,
                    "reference_id": 1
                }
            ],
            "alleleassessments": [
                {
                    // New assessment will be created, superceding any old one
                    "user_id": 1,
                    "allele_id": 2,
                    "classification": "3",
                    "evaluation": {...data...},
                    "analysis_id": 3,
                },
                {
                    // Reusing assessment
                    "id": 9
                    "allele_id": 6
                }
            ],
            "allelereports": [
                {
                    // New report will be created, superceding any old one
                    "user_id": 1,
                    "allele_id": 2,
                    "evaluation": {...data...},
                    "analysis_id": 3,
                },
                {
                    // Reusing report
                    "id": 9
                    "allele_id": 6
                }
            ]
        }
        ```

        ---
        summary: Finalize allele workflow
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id
          - name: data
            in: body
            required: true
            schema:
              title: Data object
              type: object
              required:
                - referenceassessments
                - alleleassessments
                - allelereports
              properties:
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
                        description: Existing referenceassessment id. If provided, existing object will be reused
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
                alleleassessment:
                  name: alleleassessment
                  type: array
                  items:
                    title: AlleleAssessment
                    type: object
                    required:
                      - allele_id
                    properties:
                      id:
                        description: Existing alleleassessment id. If provided, existing object will be reused
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
                      evaluation:
                        description: Evaluation data object
                        type: object
                      classification:
                        description: Classification
                        type: string
                allelereport:
                  name: allelereport
                  type: array
                  items:
                    title: AlleleReport
                    type: object
                    required:
                      - allele_id
                    properties:
                      id:
                        description: Existing reference id. If provided, existing object will be reused
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
                      evaluation:
                        description: Evaluation data object
                        type: object
              example:
                referenceassessments:
                  - user_id: 1
                    analysis_id: 3
                    reference_id: 123
                    evaluation: {}
                    allele_id: 14
                  - id: 13
                    allele_id: 13
                    reference_id: 1
                alleleassessments:
                  - user_id: 1
                    allele_id: 2
                    classification: '3'
                    evaluation: {}
                    analysis_id: 3
                  - id: 9
                    allele_id: 6
                allelereports:
                  - user_id: 1
                    allele_id: 2
                    evaluation: {}
                    analysis_id: 3
                  - id: 9
                    allele_id: 6
              description: Submitted data


        responses:
          200:
            description: Returns null
          500:
            description: Error
        """


        result = helpers.finalize_interpretation(session, data, allele_id=allele_id)
        session.commit()

        return result, 200


class AlleleCollisionResource(Resource):
    def get(self, session, allele_id):
        return helpers.get_workflow_allele_collisions(session, [allele_id], allele_id=allele_id)
