from flask import request
from sqlalchemy import tuple_
from vardb.datamodel import sample, genotype, allele

from api import ApiError, ConflictError
from api.util.util import request_json, authenticate, rest_filter, paginate
from api.v1.resource import LogRequestResource

from . import helpers
from api.util import queries
from vardb.datamodel.workflow import AnalysisInterpretationSnapshot, AnalysisInterpretation
from vardb.datamodel.sample import Analysis
from api.schemas.analysisinterpretations import (
    AnalysisInterpretationSnapshotSchema,
    AnalysisInterpretationSchema,
)
from api.schemas.filterconfigs import FilterConfigSchema


class AnalysisStatsResource(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id, user=None):

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
    def get(self, session, analysis_id, gp_name, gp_version, user=None):
        """
        Returns genepanel for analysis, only including relevant transcripts and phenotypes.
        """
        allele_ids = request.args.get("allele_ids", "")
        if not allele_ids:
            allele_ids = []
        else:
            allele_ids = allele_ids.split(",")
        return helpers.load_genepanel_for_allele_ids(session, allele_ids, gp_name, gp_version)


class AnalysisInterpretationAllelesListResource(LogRequestResource):
    @authenticate()
    @paginate
    def get(self, session, analysis_id, interpretation_id, user=None, page=None, per_page=None):
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
        allele_ids = request.args.get("allele_ids").split(",")
        current = request.args.get("current", "").lower() == "true"
        return (
            helpers.get_alleles(
                session,
                allele_ids,
                user.group.genepanels,
                analysisinterpretation_id=interpretation_id,
                current_allele_data=current,
            ),
            len(allele_ids),
        )


class AnalysisInterpretationResource(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id, interpretation_id, user=None):
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
                    excluded_allele_ids:
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
    @request_json(["id"], allowed=["state", "user_state"])
    def patch(self, session, analysis_id, interpretation_id, data=None, user=None):
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

        return None, 200


class AnalysisInterpretationListResource(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id, user=None):
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
    def post(self, session, analysis_id, user=None):
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

        helpers.override_interpretation(session, user.id, analysis_id=analysis_id)
        session.commit()

        return None, 200


class AnalysisActionStartResource(LogRequestResource):
    @authenticate()
    def post(self, session, analysis_id, user=None):
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

        helpers.start_interpretation(session, user.id, {}, analysis_id=analysis_id)
        session.commit()

        return None, 200


class AnalysisActionMarkNotReadyResource(LogRequestResource):
    @authenticate()
    @request_json(["alleleassessments", "annotations", "custom_annotations", "allelereports"])
    def post(self, session, analysis_id, data=None, user=None):
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

        helpers.marknotready_interpretation(session, data, analysis_id=analysis_id)
        session.commit()

        return None, 200


class AnalysisActionMarkInterpretationResource(LogRequestResource):
    @authenticate()
    @request_json(["alleleassessments", "annotations", "custom_annotations", "allelereports"])
    def post(self, session, analysis_id, data=None, user=None):
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

        helpers.markinterpretation_interpretation(session, data, analysis_id=analysis_id)
        session.commit()

        return None, 200


class AnalysisActionMarkReviewResource(LogRequestResource):
    @authenticate()
    @request_json(["alleleassessments", "annotations", "custom_annotations", "allelereports"])
    def post(self, session, analysis_id, data=None, user=None):
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

        helpers.markreview_interpretation(session, data, analysis_id=analysis_id)
        session.commit()

        return None, 200


class AnalysisActionMarkMedicalReviewResource(LogRequestResource):
    @authenticate()
    @request_json(["alleleassessments", "annotations", "custom_annotations", "allelereports"])
    def post(self, session, analysis_id, data=None, user=None):
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

        helpers.markmedicalreview_interpretation(session, data, analysis_id=analysis_id)
        session.commit()

        return None, 200


class AnalysisActionReopenResource(LogRequestResource):
    @authenticate()
    def post(self, session, analysis_id, user=None):
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

        helpers.reopen_interpretation(session, analysis_id=analysis_id)
        session.commit()

        return None, 200


class AnalysisActionFinalizeResource(LogRequestResource):
    @authenticate(user_config=True)
    @request_json(
        [
            "alleleassessments",
            "referenceassessments",
            "allelereports",
            "annotations",
            "custom_annotations",
            "attachments",
            "notrelevant_allele_ids",
            "technical_allele_ids",
        ]
    )
    def post(self, session, analysis_id, user_config=None, data=None, user=None):
        """
        Finalizes an analysis.

        This sets the analysis' current interpretation's status to `Done` and creates
        any [alleleassessment|referenceassessment|allelereport] objects for the provided alleles,
        unless it's specified to reuse existing objects.

        The user must provide a list of alleleassessments, referenceassessments and allelereports.
        For each assessment/report, there are two cases:
        - 'reuse=False' or reuse is missing: a new assessment/report is created in the database using the data given.
        - 'reuse=True' The id of an existing assessment/report is expected in 'presented_assessment_id'
            or 'presented_report_id'.

        The assessment/report mentioned in the 'presented..' field is the one displayed/presented to the user.
        We pass it along to keep a record of the context of the assessment.

        The analysis will be linked to assessments/report.

        **Only works for analyses with a `Ongoing` current interpretation**

        ```javascript
        Example POST data:
        {
            "annotations": [
              {
               "allele_id": 14,
               "annotation_id": 56
               }
              ],
            "customannotations": [
               {
                "allele_id": 14,
                "custom_annotation_id": 56
               }
             ],
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
                    "presented_alleleassessment_id": 7 // optional
                    "reuse": false
                },
                {
                    // Reusing assessment
                    "allele_id": 6,
                    "presented_alleleassessment_id": 7,
                    "reuse": true
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
                    "allele_id": 6
                    "presented_allelereport_id": 7,
                    "reuse": true

                }
            ],
            "notrelevant_allele_ids": [1, 2, ...],
            "technical_allele_ids": [3, 4, ...],
        }
        ```

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
            schema:
              title: Data object
              type: object
              required:
                - annotations
                - customannotations
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
                      presented_alleleassessment_id:
                        description: Existing alleleassessment id. Displayed to the user (aka context)
                        type: integer
                      reuse:
                        description: The objects signals reuse of an existing alleleassessment
                        type: boolean
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
                      presented_allelereport_id:
                        description: Existing report id. Displayed to the user (aka context)
                        type: integer
                      reuse:
                        description: The objects signals reuse of an existing report
                        type: boolean
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
                annotations:
                  - allele_id: 1
                    annotation_id: 10
                  - allele_id: 2
                    annotation_id: 34
                custom_annotations:
                  - allele_id: 1
                    custom_annotation_id: 102
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
                  - presented_alleleassessment_id: 9,
                    reuse: true
                    allele_id: 6
                allelereports:
                  - allele_id: 2
                    evaluation: {}
                    analysis_id: 3
                  - presented_report_id: 9
                    reuse: true
                    allele_id: 6
              description: Submitted data


        responses:
          200:
            description: Returns null
          500:
            description: Error
        """
        """

        Example data:

        {
            "referenceassessments": [
                {
                    # New assessment will be created, superceding any old one
                    "analysis_id": 3,
                    "reference_id": 123
                    "evaluation": {...data...},
                    "analysis_id": 3,
                    "allele_id": 14,
                },
                {
                    # Reusing assessment
                    "id": 13,
                    "allele_id": 13,
                     "reference_id": 1
                }
            ],
            "alleleassessments": [
                {
                    # New assessment will be created, superceding any old one
                    "allele_id": 2,
                    "classification": "3",
                    "evaluation": {...data...},
                    "analysis_id": 3,
                },
                {
                    # Reusing assessment
                    "presented_alleleassessment_id": 9,
                    "reuse": true
                    "allele_id": 6
                }
            ],
            "allelereports": [
                {
                    # New report will be created, superceding any old one
                    "allele_id": 2,
                    "evaluation": {...data...},
                    "analysis_id": 3,
                },
                {
                    # Reusing report
                    "presented_allelereport_id": 9,
                    "reuse": true,
                    "allele_id": 6
                }
            ]
        }

        """

        result = helpers.finalize_interpretation(
            session, user.id, data, user_config, analysis_id=analysis_id
        )
        session.commit()

        return result, 200

    @authenticate()
    def get(self, session, analysis_id, user=None):
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

        result = AnalysisInterpretationSnapshotSchema(strict=True).dump(f, many=True).data
        return result


class AnalysisCollisionResource(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id, user=None):

        allele_ids = request.args.get("allele_ids")
        if allele_ids is None:
            raise ApiError("Missing required arg allele_ids")

        if not allele_ids:
            return []

        allele_ids = [int(i) for i in allele_ids.split(",")]

        return helpers.get_workflow_allele_collisions(session, allele_ids, analysis_id=analysis_id)


class AnalysisInterpretationFinishAllowedResource(LogRequestResource):
    @authenticate()
    @rest_filter
    def get(self, session, analysis_id, interpretation_id, rest_filter=None, data=None, user=None):
        sample_ids = (
            session.query(sample.Sample.id).filter(sample.Sample.analysis_id == analysis_id).all()
        )
        sample_ids = [s[0] for s in sample_ids]

        if not sample_ids == rest_filter["sample_ids"]:
            raise ConflictError(
                "Can not finish interpretation. Additional data have been added to this analysis. Please refresh."
            )
        else:
            return None, 200


class AnalysisInterpretationLogListResource(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id, user=None):
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
        logs = helpers.get_interpretationlog(session, user.id, analysis_id=analysis_id)

        return logs, 200

    @authenticate()
    @request_json([], allowed=["warning_cleared", "priority", "message", "review_comment"])
    def post(self, session, analysis_id, data=None, user=None):
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

        return None, 200


class AnalysisInterpretationLogResource(LogRequestResource):
    @authenticate()
    @request_json(["message"])
    def patch(self, session, analysis_id, log_id, data=None, user=None):
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
            session, user.id, log_id, data["message"], analysis_id=analysis_id
        )
        session.commit()

        return None, 200

    @authenticate()
    def delete(self, session, analysis_id, log_id, user=None):
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

        return None, 200


class AnalysisInterpretationFilteredAlleles(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id=None, interpretation_id=None, user=None):
        interpretation = (
            session.query(AnalysisInterpretation)
            .filter(AnalysisInterpretation.id == interpretation_id)
            .one()
        )

        filterconfig_id = request.args.get("filterconfig_id")
        if filterconfig_id is not None:
            filterconfig_id = int(filterconfig_id)

        allele_ids, excluded_allele_ids = helpers.get_filtered_alleles(
            session, interpretation, filter_config_id=filterconfig_id
        )
        result = {"allele_ids": allele_ids, "excluded_allele_ids": excluded_allele_ids}

        return result


class AnalysisFilterConfigResource(LogRequestResource):
    @authenticate()
    def get(self, session, analysis_id=None, user=None):
        filterconfigs = queries.get_valid_filter_configs(
            session, user.id, analysis_id=analysis_id
        ).all()
        if not filterconfigs:
            raise ApiError("Unable to find filter config matching analysis {}".format(analysis_id))
        return FilterConfigSchema().dump(filterconfigs, many=True).data
