from flask import request
from sqlalchemy import tuple_

from api import ApiError
from api.util.util import request_json, authenticate
from api.v1.resource import LogRequestResource

from api.util import queries
from vardb.datamodel.workflow import AlleleInterpretationSnapshot, AlleleInterpretation
from api.schemas.alleleinterpretations import AlleleInterpretationSnapshotSchema

from . import helpers


class AlleleGenepanelResource(LogRequestResource):

    @authenticate()
    def get(self, session, allele_id, gp_name, gp_version, user=None):
        """
        Returns genepanel for allele, only including relevant transcripts and phenotypes.
        """
        return helpers.load_genepanel_for_allele_ids(session, [allele_id], gp_name, gp_version)


class AlleleInterpretationResource(LogRequestResource):

    @authenticate()
    def get(self, session, allele_id, interpretation_id, user=None):
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
            description: AlleleInterpretation object
        """
        filter_config_id = queries.get_default_filter_config_id(session, user.id).scalar()
        return helpers.get_interpretation(
            session,
            user.group.genepanels,
            filter_config_id,
            alleleinterpretation_id=interpretation_id
        )

    @authenticate()
    @request_json(
        [],
        allowed=[
            'state',
            'user_state'
        ]
    )
    def patch(self, session, allele_id, interpretation_id, data=None, user=None):
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

        helpers.update_interpretation(session, user.id, data, alleleinterpretation_id=interpretation_id)
        session.commit()

        return None, 200


class AlleleInterpretationAllelesListResource(LogRequestResource):

    @authenticate()
    def get(self, session, allele_id, interpretation_id, user=None):
        if not session.query(AlleleInterpretation).filter(
            AlleleInterpretation.id == interpretation_id,
            AlleleInterpretation.allele_id == allele_id
        ).count():
            raise ApiError("Interpretation id {} is not part of allele with id {}".format(
                interpretation_id, allele_id
            ))
        allele_ids = request.args.get('allele_ids').split(',')
        current = request.args.get('current', '').lower() == 'true'
        return helpers.get_alleles(
            session,
            allele_ids,
            user.group.genepanels,
            alleleinterpretation_id=interpretation_id,
            current_allele_data=current
        )


class AlleleInterpretationListResource(LogRequestResource):

    @authenticate()
    def get(self, session, allele_id, user=None):
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
        filter_config_id = queries.get_default_filter_config_id(session, user.id).scalar()
        return helpers.get_interpretations(
            session,
            user.group.genepanels,
            filter_config_id,
            allele_id=allele_id
        )


class AlleleActionOverrideResource(LogRequestResource):

    @authenticate()
    def post(self, session, allele_id, user=None):
        """
        Lets an user take over an allele, by replacing the
        allele's current interpretation's user_id with the authenticated user id.

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

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        helpers.override_interpretation(session, user.id, allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionStartResource(LogRequestResource):

    @authenticate()
    @request_json(['gp_name', 'gp_version'])
    def post(self, session, allele_id, data=None, user=None):
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
              title: Genepanel
              required:
                - gp_name
                - gp_version
              properties:
                gp_name:
                  type: string
                gp_version:
                  type: string
              example:
                gp_name: HBOC
                gp_version: v01
            description: Genepanel

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.start_interpretation(session, user.id, data, allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionMarkInterpretationResource(LogRequestResource):

    @authenticate()
    @request_json(
        [
            'alleleassessments',
            'annotations',
            'custom_annotations',
            'allelereports'
        ]
    )
    def post(self, session, allele_id, data=None, user=None):
        """
        Marks an allele interpretation for interpretation.

        This sets the alleles current interpretation's status to `Done` and creates
        a new current interpretation with status `Not started` in `Interpretation` state.

        **Only works for alleles with a `Ongoing` current interpretation**
        ---
        summary: Mark allele for interpretation
        tags:
          - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        filter_config_id = queries.get_default_filter_config_id(session, user.id).scalar()
        helpers.markinterpretation_interpretation(
            session,
            data,
            filter_config_id,
            allele_id=allele_id
        )
        session.commit()

        return None, 200


class AlleleActionMarkReviewResource(LogRequestResource):

    @authenticate()
    @request_json(
        [
            'alleleassessments',
            'annotations',
            'custom_annotations',
            'allelereports'
        ]
    )
    def post(self, session, allele_id, data=None, user=None):
        """
        Marks an allele interpretation for review.

        This sets the alleles current interpretation's status to `Done` and creates
        a new current interpretation with status `Not started` in `Review` state

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

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        filter_config_id = queries.get_default_filter_config_id(session, user.id).scalar()
        helpers.markreview_interpretation(
            session,
            data,
            filter_config_id,
            allele_id=allele_id
        )
        session.commit()

        return None, 200


class AlleleActionReopenResource(LogRequestResource):

    @authenticate()
    def post(self, session, allele_id, user=None):
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

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.reopen_interpretation(session, allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionFinalizeResource(LogRequestResource):

    @authenticate(user_config=True)
    @request_json(
        [
            'alleleassessments',
            'referenceassessments',
            'allelereports',
            'annotations',
            'custom_annotations',
            'attachments'
        ]
    )
    def post(self, session, allele_id, user_config=None, data=None, user=None):
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
                  - analysis_id: 3
                    reference_id: 123
                    evaluation: {}
                    allele_id: 14
                  - id: 13
                    allele_id: 13
                    reference_id: 1
                alleleassessments:
                  - allele_id: 2
                    classification: '3'
                    evaluation: {}
                    analysis_id: 3
                  - id: 9
                    allele_id: 6
                allelereports:
                  - allele_id: 2
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

        filter_config_id = queries.get_default_filter_config_id(session, user.id).scalar()
        result = helpers.finalize_interpretation(
            session,
            user.id,
            data,
            filter_config_id,
            user_config,
            allele_id=allele_id
        )
        session.commit()

        return result, 200

    @authenticate()
    def get(self, session, allele_id, user=None):
        f = session.query(AlleleInterpretationSnapshot).filter(
            AlleleInterpretationSnapshot.allele_id == allele_id,
            tuple_(AlleleInterpretation.genepanel_name, AlleleInterpretation.genepanel_version).in_((gp.name, gp.version) for gp in user.group.genepanels),
        ).join(AlleleInterpretation).all()

        result = AlleleInterpretationSnapshotSchema(strict=True).dump(f, many=True).data
        return result


class AlleleGenepanelsListResource(LogRequestResource):

    @authenticate()
    def get(self, session, allele_id, user=None):
        return helpers.get_genepanels(session, [allele_id], user=user).data


class AlleleCollisionResource(LogRequestResource):

    @authenticate()
    def get(self, session, allele_id, user=None):

        allele_ids = request.args.get('allele_ids')
        if allele_ids is None:
            raise ApiError("Missing required arg allele_ids")

        if not allele_ids:
            return []

        allele_ids = [int(i) for i in allele_ids.split(',')]

        return helpers.get_workflow_allele_collisions(session, [allele_id], allele_id=allele_id)


class AlleleInterpretationLogListResource(LogRequestResource):

    @authenticate()
    def get(self, session, allele_id, user=None):
        """
        Get all interpreation log entries for an allele workflow.

        ---
        summary: Get interpretation log
        tags:
            - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        logs = helpers.get_interpretationlog(session, user.id, allele_id=allele_id)

        return logs, 200

    @authenticate()
    @request_json(
        [],
        allowed=[
            'warning_cleared',
            'priority',
            'message',
            'review_comment'
        ]
    )
    def post(self, session, allele_id, data=None, user=None):
        """
        Create a new interpretation log entry for an allele workflow.

        ---
        summary: Create interpretation log
        tags:
            - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        helpers.create_interpretationlog(session, user.id, data, allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleInterpretationLogResource(LogRequestResource):

    @authenticate()
    @request_json(
        ['message']
    )
    def patch(self, session, allele_id, log_id, data=None, user=None):
        """
        Patch an interpretation log entry.

        ---
        summary: Patch interpretation log
        tags:
            - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        helpers.patch_interpretationlog(
          session,
          user.id,
          log_id,
          data['message'],
          allele_id=allele_id
        )
        session.commit()

        return None, 200

    @authenticate()
    def delete(self, session, allele_id, log_id, user=None):
        """
        Delete an interpretation log entry.

        ---
        summary: Create interpretation log
        tags:
            - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
          - name: interpretationlog_id
            in: path
            type: integer
            description: Interpretation log id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        helpers.delete_interpretationlog(
          session,
          user.id,
          log_id,
          allele_id=allele_id
        )
        session.commit()

        return None, 200
