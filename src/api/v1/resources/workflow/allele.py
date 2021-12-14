from api import ApiError
from api.schemas.alleleinterpretations import AlleleInterpretationSnapshotSchema
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import (
    AlleleInterpretationListResource as PydanticAlleleInterpretationListResource,
    AlleleGenepanelResource as PydanticAlleleGenepanelResource,
)
from api.util.util import authenticate, request_json
from api.v1.resource import LogRequestResource
from flask import request
from sqlalchemy import tuple_
from sqlalchemy.orm import Session
from vardb.datamodel.user import User
from vardb.datamodel.workflow import AlleleInterpretation, AlleleInterpretationSnapshot

from . import helpers


class AlleleGenepanelResource(LogRequestResource):
    @authenticate()
    @validate_output(PydanticAlleleGenepanelResource)
    def get(self, session: Session, allele_id: int, gp_name: str, gp_version: str, user: User):
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
        return helpers.get_interpretation(
            session, user.group.genepanels, user.id, alleleinterpretation_id=interpretation_id
        )

    @authenticate()
    @request_json([], allowed=["state", "user_state"])
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

        helpers.update_interpretation(
            session, user.id, data, alleleinterpretation_id=interpretation_id
        )
        session.commit()

        return None, 200


class AlleleInterpretationAllelesListResource(LogRequestResource):
    @authenticate()
    def get(self, session, allele_id, interpretation_id, user=None):
        if (
            not session.query(AlleleInterpretation)
            .filter(
                AlleleInterpretation.id == interpretation_id,
                AlleleInterpretation.allele_id == allele_id,
            )
            .count()
        ):
            raise ApiError(
                "Interpretation id {} is not part of allele with id {}".format(
                    interpretation_id, allele_id
                )
            )
        allele_ids = request.args.get("allele_ids", "").split(",")
        current = request.args.get("current", "").lower() == "true"
        return helpers.get_alleles(
            session,
            allele_ids,
            user.group.genepanels,
            alleleinterpretation_id=interpretation_id,
            current_allele_data=current,
        )


class AlleleInterpretationListResource(LogRequestResource):
    @authenticate()
    @validate_output(PydanticAlleleInterpretationListResource)
    def get(self, session: Session, allele_id: int, user: User):
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
        return helpers.get_interpretations(
            session, user.group.genepanels, user.id, allele_id=allele_id
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
        helpers.override_interpretation(session, user.id, workflow_allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionStartResource(LogRequestResource):
    @authenticate()
    @request_json(["gp_name", "gp_version"])
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

        helpers.start_interpretation(session, user.id, data, workflow_allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionMarkInterpretationResource(LogRequestResource):
    @authenticate()
    @request_json(
        ["alleleassessment_ids", "allelereport_ids", "annotation_ids", "custom_annotation_ids"]
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

        helpers.markinterpretation_interpretation(session, data, workflow_allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionMarkReviewResource(LogRequestResource):
    @authenticate()
    @request_json(
        ["alleleassessment_ids", "allelereport_ids", "annotation_ids", "custom_annotation_ids"]
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

        helpers.markreview_interpretation(session, data, workflow_allele_id=allele_id)
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

        helpers.reopen_interpretation(session, workflow_allele_id=allele_id)
        session.commit()

        return None, 200


class AlleleActionFinalizeAlleleResource(LogRequestResource):
    @authenticate(user_config=True)
    @request_json(jsonschema="workflowActionFinalizeAllelePost.json")
    def post(self, session, allele_id, user_config=None, data=None, user=None):
        """
        Finalizes a single allele within an allele workflow.

        This will create any [alleleassessment|referenceassessment|allelereport] objects for the provided allele id.

        **Only works for analyses with a `Ongoing` current interpretation**

        ---
        summary: Finalize allele in analysis
        tags:
          - Workflow
        parameters:
          - name: allele_id
            in: path
            type: integer
            description: Allele id
          - name: data
            in: body
            required: true
            type: object

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        result = helpers.finalize_allele(
            session, user.id, user.group.id, data, user_config, workflow_allele_id=allele_id
        )
        session.commit()

        return result, 200


class AlleleActionFinalizeResource(LogRequestResource):
    @authenticate(user_config=True)
    @request_json(
        ["alleleassessment_ids", "allelereport_ids", "annotation_ids", "custom_annotation_ids"]
    )
    def post(self, session, allele_id, user_config=None, data=None, user=None):
        """
        Finalizes an allele workflow.

        **Only works for analyses with a `Ongoing` current interpretation**

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
            type: object


        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        result = helpers.finalize_workflow(
            session, user.id, data, user_config, workflow_allele_id=allele_id
        )
        session.commit()

        return result, 200

    @authenticate()
    def get(self, session, allele_id, user=None):
        f = (
            session.query(AlleleInterpretationSnapshot)
            .filter(
                AlleleInterpretationSnapshot.allele_id == allele_id,
                tuple_(
                    AlleleInterpretation.genepanel_name, AlleleInterpretation.genepanel_version
                ).in_((gp.name, gp.version) for gp in user.group.genepanels),
            )
            .join(AlleleInterpretation)
            .all()
        )

        result = AlleleInterpretationSnapshotSchema(strict=True).dump(f, many=True).data
        return result


class AlleleGenepanelsListResource(LogRequestResource):
    @authenticate()
    def get(self, session, allele_id, user=None):
        return helpers.get_genepanels(session, [allele_id], user=user).data


class AlleleCollisionResource(LogRequestResource):
    @authenticate()
    def get(self, session, allele_id, user=None):

        allele_ids = request.args.get("allele_ids")
        if allele_ids is None:
            raise ApiError("Missing required arg allele_ids")

        if not allele_ids:
            return []

        allele_ids = [int(i) for i in allele_ids.split(",")]

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
    @request_json([], allowed=["warning_cleared", "priority", "message", "review_comment"])
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
    @request_json(["message"])
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
            session, user.id, log_id, data["message"], allele_id=allele_id
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
        helpers.delete_interpretationlog(session, user.id, log_id, allele_id=allele_id)
        session.commit()

        return None, 200
