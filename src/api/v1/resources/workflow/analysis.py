from typing import Dict

from api import ApiError, ConflictError
from api.schemas.analysisinterpretations import AnalysisInterpretationSnapshotSchema
from api.schemas.filterconfigs import FilterConfigSchema
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.config import UserConfig
from api.schemas.pydantic.v1.resources import (
    AlleleCollisionResponse,
    AlleleGenepanelResponse,
    AlleleListResponse,
    AnalysisInterpretationListResponse,
    AnalysisInterpretationResponse,
    AnalysisInterpretationSnapshotListResponse,
    AnalysisStatsResponse,
    CreateInterpretationLogRequest,
    EmptyResponse,
    FilterConfigListResponse,
    FilteredAllelesResponse,
    FinalizeAlleleInterpretationResponse,
    FinalizeAlleleRequest,
    InterpretationLogListResponse,
    MarkAnalysisInterpretationRequest,
    PatchInterpretationLogRequest,
    PatchInterpretationRequest,
)
from api.util.util import authenticate, paginate, request_json, rest_filter, str2intlist
from api.v1.resource import LogRequestResource
from datalayer import queries
from flask import request
from sqlalchemy import tuple_
from sqlalchemy.orm import Session
from vardb.datamodel import allele, genotype, sample, user
from vardb.datamodel.sample import Analysis
from vardb.datamodel.workflow import AnalysisInterpretation, AnalysisInterpretationSnapshot

from . import helpers


class AnalysisStatsResource(LogRequestResource):
    @authenticate()
    @validate_output(AnalysisStatsResponse)
    def get(self, session: Session, analysis_id: int, user: user.User):

        # Number of alleles
        allele_count = (
            session.query(allele.Allele.id)
            .join(genotype.Genotype.alleles, sample.Sample)
            .filter(sample.Sample.analysis_id == analysis_id)
            .count()
        )

        stats = {"allele_count": allele_count}

        return stats


class AnalysisGenepanelResource(LogRequestResource):
    @authenticate()
    @validate_output(AlleleGenepanelResponse)
    def get(
        self, session: Session, analysis_id: int, gp_name: str, gp_version: str, user: user.User
    ):
        """
        Returns genepanel for analysis, only including relevant transcripts and phenotypes.
        """
        allele_ids = str2intlist(request.args.get("allele_ids", ""))
        return helpers.load_genepanel_for_allele_ids(session, allele_ids, gp_name, gp_version)


class AnalysisInterpretationAllelesListResource(LogRequestResource):
    @authenticate()
    @validate_output(AlleleListResponse, paginated=True)
    @paginate
    def get(
        self,
        session: Session,
        analysis_id: int,
        interpretation_id: int,
        user: user.User,
        **kwargs,
    ):
        if (
            not session.query(AnalysisInterpretation)
            .filter(
                AnalysisInterpretation.id == interpretation_id,
                AnalysisInterpretation.analysis_id == analysis_id,
            )
            .count()
        ):
            raise ApiError(
                "Interpretation id {} is not part of analysis with id {}".format(
                    interpretation_id, analysis_id
                )
            )
        allele_ids = str2intlist(request.args.get("allele_ids"))
        current = request.args.get("current", "").lower() == "true"
        filterconfig_id = request.args.get("filterconfig_id")
        if filterconfig_id is not None:
            filterconfig_id = int(filterconfig_id)
        return (
            helpers.get_alleles(
                session,
                allele_ids,
                user.group.genepanels,
                analysisinterpretation_id=interpretation_id,
                current_allele_data=current,
                filterconfig_id=filterconfig_id,
            ),
            len(allele_ids),
        )


class AnalysisInterpretationResource(LogRequestResource):
    @authenticate()
    @validate_output(AnalysisInterpretationResponse)
    def get(self, session: Session, analysis_id: int, interpretation_id: int, user: user.User):
        """
        Returns analysisinterpretation for analysis.
        ---
        summary: Get analysis interpretation
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id
          - name: interpretation_id
            in: path
            type: integer
            description: AnalysisInterpretation id
        responses:
          200:
            schema:
              title: AnalysisInterpretation
              allOf:
                - $ref: '#/definitions/AnalysisInterpretation'
                - properties:
                    allele_ids:
                      title: Allele ids
                      type: array
                      description: Allele ids
                      items:
                        type: integer
                    excluded_alleles_by_caller_type:
                      title: ExcludedAlleles
                      type: object
                      description: Filtered allele ids
                      properties:
                        frequency:
                          type: array
                          items:
                            type: integer
                        region:
                          type: array
                          items:
                            type: integer
                        gene:
                          type: array
                          items:
                            type: integer

            description: Interpretation object
        """
        return helpers.get_interpretation(
            session, user.group.genepanels, user.id, analysisinterpretation_id=interpretation_id
        )

    @authenticate()
    @validate_output(EmptyResponse)
    @request_json(model=PatchInterpretationRequest)
    def patch(
        self,
        session: Session,
        analysis_id: int,
        interpretation_id: int,
        data: PatchInterpretationRequest,
        user: user.User,
    ):
        """
        Updates the current interpretation inplace.

        **Only allowed for interpretations that are `Ongoing`**
        ---
        summary: Update interpretation
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id
          - data:
            in: body
            required: true
            schema:
              title: AnalysisInterpretation data
              type: object
              properties:
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
            session, user.id, data, analysisinterpretation_id=interpretation_id
        )
        session.commit()


class AnalysisInterpretationListResource(LogRequestResource):
    @authenticate()
    @validate_output(AnalysisInterpretationListResponse)
    def get(self, session: Session, analysis_id: int, user: user.User):
        """
        Returns all interpretations for analysis.
        ---
        summary: Get interpretations
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/AnalysisInterpretation'

            description: AnalysisInterpretation objects
        """
        return helpers.get_interpretations(
            session, user.group.genepanels, user.id, analysis_id=analysis_id
        )


class AnalysisActionOverrideResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    def post(self, session: Session, analysis_id: int, user: user.User):
        """
        Lets an user take over an analysis, by replacing the
        analysis' current interpretation's user_id with the authenticated user_id.

        **Only works for analyses with a `Ongoing` current interpretation**
        ---
        summary: Assign analysis to another user
        tags:
            - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.override_interpretation(session, user.id, workflow_analysis_id=analysis_id)
        session.commit()


class AnalysisActionStartResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    def post(self, session: Session, analysis_id: int, user: user.User):
        """
        Starts an analysisinterpretation.

        If no analysisinterpretations exists for given analysis id, one is created.
        ---
        summary: Start analysis
        tags:
            - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.start_interpretation(session, user.id, data=None, workflow_analysis_id=analysis_id)
        session.commit()


class AnalysisActionMarkNotReadyResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    @request_json(model=MarkAnalysisInterpretationRequest)
    def post(
        self,
        session: Session,
        analysis_id: int,
        data: MarkAnalysisInterpretationRequest,
        user: user.User,
    ):
        """
        Marks an analysis as Not ready.

        This sets the analysis' current interpretation's status to `Done` and creates
        a new current interpretation with status `Not started` in `Not ready` state.

        **Only works for analyses with a `Ongoing` current interpretation**
        ---
        summary: Mark analysis as Not ready
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.marknotready_interpretation(session, data, workflow_analysis_id=analysis_id)
        session.commit()


class AnalysisActionMarkInterpretationResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    @request_json(model=MarkAnalysisInterpretationRequest)
    def post(
        self,
        session: Session,
        analysis_id: int,
        data: MarkAnalysisInterpretationRequest,
        user: user.User,
    ):
        """
        Marks an analysis for interpretation.

        This sets the analysis' current interpretation's status to `Done` and creates
        a new current interpretation with status `Not started` in `Interpretation` state.

        **Only works for analyses with a `Ongoing` current interpretation**
        ---
        summary: Mark analysis for interpretation
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.markinterpretation_interpretation(session, data, workflow_analysis_id=analysis_id)
        session.commit()


class AnalysisActionMarkReviewResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    @request_json(model=MarkAnalysisInterpretationRequest)
    def post(
        self,
        session: Session,
        analysis_id: int,
        data: MarkAnalysisInterpretationRequest,
        **kwargs,
    ):
        """
        Marks an analysis for review.

        This sets the analysis' current interpretation's status to `Done` and creates
        a new current interpretation with status `Not started` in `Review` state.

        **Only works for analyses with a `Ongoing` current interpretation**
        ---
        summary: Mark analysis for review
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.markreview_interpretation(session, data, workflow_analysis_id=analysis_id)
        session.commit()


class AnalysisActionMarkMedicalReviewResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    @request_json(model=MarkAnalysisInterpretationRequest)
    def post(
        self,
        session: Session,
        analysis_id: int,
        data: MarkAnalysisInterpretationRequest,
        user: user.User,
    ):
        """
        Marks an analysis for medical review.

        This sets the analysis' current interpretation's status to `Done` and creates
        a new current interpretation with status `Not started` in `Medical review` state.

        **Only works for analyses with a `Ongoing` current interpretation**
        ---
        summary: Mark analysis for medical review
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.markmedicalreview_interpretation(session, data, workflow_analysis_id=analysis_id)
        session.commit()


class AnalysisActionReopenResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    def post(self, session: Session, analysis_id: int, user: user.User):
        """
        Reopens an analysis workflow that has previously been finalized.

        This creates a new current interpretation for the analysis,
        with status set to `Not started`.


        **Only works for analyses with a `Ongoing` current interpretation**
        ---
        summary: Reopen analysis workflow
        tags:
          - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """

        helpers.reopen_interpretation(session, workflow_analysis_id=analysis_id)
        session.commit()


class AnalysisActionFinalizeAlleleResource(LogRequestResource):
    @authenticate(user_config=True, pydantic=True)
    @validate_output(FinalizeAlleleInterpretationResponse)
    @request_json(model=FinalizeAlleleRequest)
    def post(
        self,
        session: Session,
        analysis_id: int,
        user_config: UserConfig,
        data: FinalizeAlleleRequest,
        user: user.User,
    ):
        """
        Finalizes a single allele within an analysis.

        This will create any [alleleassessment|referenceassessment|allelereport] objects for the provided allele id.

        **Only works for analyses with a `Ongoing` current interpretation**

        ---
        summary: Finalize allele in analysis
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

        result = helpers.finalize_allele(
            session, user.id, user.group.id, data, user_config, workflow_analysis_id=analysis_id
        )
        session.commit()

        return result


class AnalysisActionFinalizeResource(LogRequestResource):
    @authenticate(user_config=True, pydantic=True)
    @validate_output(EmptyResponse)
    @request_json(model=MarkAnalysisInterpretationRequest)
    def post(
        self,
        session: Session,
        analysis_id: int,
        user_config: UserConfig,
        data: MarkAnalysisInterpretationRequest,
        user: user.User,
    ):
        """
        Finalizes an analysis workflow.

        ---
        summary: Finalize analysis workflow
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

        helpers.finalize_workflow(
            session, user.id, data, user_config, workflow_analysis_id=analysis_id
        )
        session.commit()

    @authenticate()
    @validate_output(AnalysisInterpretationSnapshotListResponse)
    def get(self, session: Session, analysis_id: int, user: user.User):
        f = (
            session.query(AnalysisInterpretationSnapshot)
            .filter(
                Analysis.id == analysis_id,
                tuple_(Analysis.genepanel_name, Analysis.genepanel_version).in_(
                    (gp.name, gp.version) for gp in user.group.genepanels
                ),
            )
            .join(AnalysisInterpretation, Analysis)
            .all()
        )

        return AnalysisInterpretationSnapshotSchema(strict=True).dump(f, many=True).data


class AnalysisCollisionResource(LogRequestResource):
    @authenticate()
    @validate_output(AlleleCollisionResponse)
    def get(self, session: Session, analysis_id: int, user: user.User):
        if request.args.get("allele_ids") is None:
            raise ApiError("Missing required arg allele_ids")
        allele_ids = str2intlist(request.args.get("allele_ids"))

        # TODO: why is empty string a silent error?
        if not allele_ids:
            return []

        return helpers.get_workflow_allele_collisions(session, allele_ids, analysis_id=analysis_id)


class AnalysisInterpretationFinishAllowedResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    @rest_filter
    def get(self, session: Session, analysis_id: int, rest_filter: Dict, **kwargs):
        sample_ids = (
            session.query(sample.Sample.id).filter(sample.Sample.analysis_id == analysis_id).all()
        )
        sample_ids = [s[0] for s in sample_ids]

        if not sample_ids == rest_filter["sample_ids"]:
            raise ConflictError(
                "Can not finish interpretation. Additional data have been added to this analysis. Please refresh."
            )


class AnalysisInterpretationLogListResource(LogRequestResource):
    @authenticate()
    @validate_output(InterpretationLogListResponse)
    def get(self, session: Session, analysis_id: int, user: user.User):
        """
        Get all interpreation log entries for an analysis workflow.

        ---
        summary: Get interpretation log
        tags:
            - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        return helpers.get_interpretationlog(session, user.id, analysis_id=analysis_id)

    @authenticate()
    @validate_output(EmptyResponse)
    @request_json(model=CreateInterpretationLogRequest)
    def post(
        self,
        session: Session,
        analysis_id: int,
        data: CreateInterpretationLogRequest,
        user: user.User,
    ):
        """
        Create a new interpretation log entry for an analysis workflow.

        ---
        summary: Create interpretation log
        tags:
            - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        helpers.create_interpretationlog(session, user.id, data, analysis_id=analysis_id)
        session.commit()


class AnalysisInterpretationLogResource(LogRequestResource):
    @authenticate()
    @validate_output(EmptyResponse)
    @request_json(model=PatchInterpretationLogRequest)
    def patch(
        self,
        session: Session,
        analysis_id: int,
        log_id: int,
        data: PatchInterpretationLogRequest,
        user: user.User,
    ):
        """
        Patch an interpretation log entry.

        ---
        summary: Patch interpretation log
        tags:
            - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id

        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        helpers.patch_interpretationlog(
            session, user.id, log_id, data.message, analysis_id=analysis_id
        )
        session.commit()

    @authenticate()
    @validate_output(EmptyResponse)
    def delete(self, session: Session, analysis_id: int, log_id: int, user: user.User):
        """
        Delete an interpretation log entry.

        ---
        summary: Create interpretation log
        tags:
            - Workflow
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id
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
        helpers.delete_interpretationlog(session, user.id, log_id, analysis_id=analysis_id)
        session.commit()


class AnalysisInterpretationFilteredAlleles(LogRequestResource):
    @authenticate()
    @validate_output(FilteredAllelesResponse)
    def get(self, session: Session, interpretation_id: int, **kwargs):
        interpretation = (
            session.query(AnalysisInterpretation)
            .filter(AnalysisInterpretation.id == interpretation_id)
            .one()
        )

        filterconfig_id = request.args.get("filterconfig_id")
        if filterconfig_id is not None:
            filterconfig_id = int(filterconfig_id)

        (
            allele_ids,
            excluded_alleles,
        ) = helpers.get_filtered_alleles(session, interpretation, filter_config_id=filterconfig_id)
        assert (
            excluded_alleles
        ), f"Got unexpected excluded_alleles=None when filtering analysis interpretation {interpretation.id}"

        excluded_by_caller_type = helpers.filtered_by_caller_type(session, excluded_alleles)
        return {
            "allele_ids": allele_ids,
            "excluded_alleles_by_caller_type": excluded_by_caller_type,
        }


class AnalysisFilterConfigResource(LogRequestResource):
    @authenticate()
    @validate_output(FilterConfigListResponse)
    def get(self, session: Session, analysis_id: int, user: user.User):
        filterconfigs = queries.get_valid_filter_configs(
            session, user.group_id, analysis_id=analysis_id
        ).all()
        if not filterconfigs:
            raise ApiError("Unable to find filter config matching analysis {}".format(analysis_id))

        return FilterConfigSchema().dump(filterconfigs, many=True).data
