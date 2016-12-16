import datetime

from sqlalchemy import not_

from vardb.datamodel import user, assessment, sample, genotype, allele, gene, workflow

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
from api.util.assessmentcreator import AssessmentCreator
from api.util.allelereportcreator import AlleleReportCreator
from api.util.snapshotcreator import SnapshotCreator
from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader
from api.v1.resource import Resource
from api.config import config


def get_latest_analysisinterpretation(session, analysis_id):
    return session.query(workflow.AnalysisInterpretation).filter(
        workflow.AnalysisInterpretation.analysis_id == analysis_id
    ).order_by(workflow.AnalysisInterpretation.id.desc()).first()


def get_current_interpretation(analysis):
    """
    Goes through the interpretations and selects the
    current one, if any. A current interpretation is
    defined as a interpretation that has yet to be started,
    or is currently in progress.
    """

    ongoing_statuses = ['Not started', 'Ongoing']
    current = list()
    for interpretation in analysis['interpretations']:
        if interpretation['status'] in ongoing_statuses:
            current.append(interpretation['id'])
    assert len(current) < 2
    return current[0] if current else None


class AnalysisInterpretationResource(Resource):

    def get(self, session, analysis_id):
        """
        Returns current analysisinterpretation for analysis.

        If no current analysisinterpretation exists, it returns null.
        ---
        summary: Get current interpretation
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
                        class1:
                          type: array
                          items:
                            type: integer
                        intronic:
                          type: array
                          items:
                            type: integer

            description: Interpretation object
        """

        latest_analysis_interpretation = get_latest_analysisinterpretation(session, analysis_id)
        if latest_analysis_interpretation:
            return InterpretationDataLoader(session, config).from_id(latest_analysis_interpretation.id)
        else:
            return None

    @request_json(
        ['id'],
        allowed=[
            'state',
            'user_state',
            'user_id'
        ]
    )
    def patch(self, session, analysis_id, data=None):
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

        latest_analysis_interpretation = get_latest_analysisinterpretation(session, analysis_id)

        AnalysisInterpretationResource.check_update_allowed(latest_analysis_interpretation, data)

        # Add current state to history if new state is different:
        if data['state'] != latest_analysis_interpretation.state:
            AnalysisInterpretationResource.update_history(latest_analysis_interpretation)

        # Patch (overwrite) state fields with new values
        latest_analysis_interpretation.state = data['state']
        latest_analysis_interpretation.user_state = data['user_state']

        latest_analysis_interpretation.date_last_update = datetime.datetime.now()

        session.commit()
        return None, 200

    @staticmethod
    def update_history(interpretation):
        if 'history' not in interpretation.state_history:
            interpretation.state_history['history'] = list()
        interpretation.state_history['history'].insert(0, {
            'time': datetime.datetime.now().isoformat(),
            'state': interpretation.state,
            'user_id': interpretation.user_id
        })

    @staticmethod
    def check_update_allowed(interpretation, patch_data):
        if interpretation.status == 'Done':
            raise ApiError("Cannot PATCH interpretation with status 'DONE'")
        elif interpretation.status == 'Not started':
            raise ApiError("Interpretation not started. Call it's analysis' start action to begin interpretation.")

        # Check that user is same as before
        if interpretation.user_id:
            if interpretation.user_id != patch_data['user_id']:
                raise ApiError("Interpretation owned by {} cannot be updated by other user ({})"
                               .format(interpretation.user_id, patch_data['user_id']))


class AnalysisActionOverrideResource(Resource):

    @request_json(['user_id'])
    def post(self, session, analysis_id, data=None):
        """
        Lets an user take over an analysis, by replacing the
        analysis' current interpretation's user_id with the input user_id.

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

        # Get user by username
        new_user = session.query(user.User).filter(
            user.User.id == data['user_id']
        ).one()

        analysis_interpretation = get_latest_analysisinterpretation(session, analysis_id)

        if analysis_interpretation.status != 'Ongoing':
            raise ApiError("Cannot reassign interpretation that is not 'Ongoing'.")

        # db will throw exception if user_id is not a valid id
        # since it's a foreign key
        analysis_interpretation.user = new_user
        session.commit()
        return None, 200


class AnalysisActionStartResource(Resource):

    @request_json(['user_id'])
    def post(self, session, analysis_id, data=None):
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

        # Get user by username
        start_user = session.query(user.User).filter(
            user.User.id == data['user_id']
        ).one()

        analysis_interpretation = get_latest_analysisinterpretation(session, analysis_id)

        if not analysis_interpretation:
            analysis_interpretation = workflow.AnalysisInterpretation()
            analysis_interpretation.allele_id = analysis_id
            session.add(analysis_interpretation)
        elif analysis_interpretation.status != 'Not started':
            raise ApiError("Cannot start existing interpretation where status = {}".format(analysis_interpretation.status))

        # db will throw exception if user_id is not a valid id
        # since it's a foreign key
        analysis_interpretation.user = start_user
        analysis_interpretation.status = 'Ongoing'
        session.commit()

        return None, 200


class AnalysisActionMarkReviewResource(Resource):

    def post(self, session, analysis_id):
        """
        Marks an analysis for review.

        This sets the analysis' current interpretation's status to `Done` and creates
        a new current interpretation with status `Not started`.

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
        # TODO: Validate that user is same as user on interpretation

        analysis_interpretation_current = get_latest_analysisinterpretation(session, analysis_id)

        if analysis_interpretation_current.status != 'Ongoing':
            raise ApiError("Interpretation is not ongoing.")

        analysis_interpretation_current.status = 'Done'
        analysis_interpretation_current.date_last_update = datetime.datetime.now()

        # Create next interpretation
        analysis_interpretation_next = workflow.AnalysisInterpretation()
        analysis_interpretation_next.analysis_id = analysis_interpretation_current.analysis_id
        analysis_interpretation_next.state = analysis_interpretation_current.state

        session.add(analysis_interpretation_next)
        session.commit()
        return None, 200


class AnalysisActionReopenResource(Resource):

    def post(self, session, analysis_id):
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
        analysis_interpretation = get_latest_analysisinterpretation(session, analysis_id)

        if analysis_interpretation is None:
            raise ApiError("There are no existing interpretations for this allele. Use the start action instead.")

        if not analysis_interpretation.status == 'Done':
            raise ApiError("Allele interpretation is already 'Not started' or 'Ongoing'. Cannot reopen.")

        # Create next interpretation
        analysis_interpretation_next = workflow.AlleleInterpretation()
        analysis_interpretation_next.allele_id = analysis_interpretation.allele_id
        analysis_interpretation_next.state = analysis_interpretation.state

        session.add(analysis_interpretation_next)
        session.commit()
        return None, 200


class AnalysisActionFinalizeResource(Resource):

    @request_json(
        [
            'alleleassessments',
            'referenceassessments',
            'allelereports'
        ]
    )
    def post(self, session, analysis_id, data=None):
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
                    "user_id": 1,
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
            ]
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
                      presented_alleleassessment_id:
                        description: Existing alleleassessment id. Displayed to the user (aka context)
                        type: integer
                      reuse:
                        description: The objects signals reuse of an existing alleleassessment
                        type: boolean
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
                      presented_allelereport_id:
                        description: Existing report id. Displayed to the user (aka context)
                        type: integer
                      reuse:
                        description: The objects signals reuse of an existing report
                        type: boolean
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
                annotations:
                  - allele_id: 1
                    annotation_id: 10
                  - allele_id: 2
                    annotation_id: 34
                custom_annotations:
                  - allele_id: 1
                    custom_annotation_id: 102
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
                  - presented_alleleassessment_id: 9,
                    reuse: true
                    allele_id: 6
                allelereports:
                  - user_id: 1
                    allele_id: 2
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
                    "user_id": 1,
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
                    "user_id": 1,
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
                    "user_id": 1,
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

        analysis_interpretation = get_latest_analysisinterpretation(session, analysis_id)

        if not analysis_interpretation.status == 'Ongoing':
            raise ApiError("Cannot finalize when latest interpretation is not 'Ongoing'")

        grouped_alleleassessments = AssessmentCreator(self.session).create_from_data(
            data['annotations'],
            data['alleleassessments'],
            data['custom_annotations'],
            data['referenceassessments']
        )

        # List of tuples (presented_assessment, created_assessment or None):
        reused_alleleassessments = grouped_alleleassessments['alleleassessments']['reused']
        created_alleleassessments = grouped_alleleassessments['alleleassessments']['created']

        for alleleassessment in created_alleleassessments:
            session.add(alleleassessment[1])

        # un-tuple:
        all_alleleassessents = \
            map(lambda a: a[0], reused_alleleassessments) + map(lambda a: a[1], created_alleleassessments)

        grouped_allelereports = AlleleReportCreator(self.session).create_from_data(
            data['allelereports'],
            all_alleleassessents
        )

        # List of tuples (presented_report, created_report or None):
        reused_allelereports = grouped_allelereports['reused']
        created_allelereports = grouped_allelereports['created']

        for allele_report in created_allelereports:
            session.add(allele_report[1])

        snapshot_objects = SnapshotCreator(session).create_from_data(
            'analysis',
            analysis_interpretation.id,
            data['annotations'],
            reused_alleleassessments,
            created_alleleassessments,
            reused_allelereports=reused_allelereports,
            created_allelereports=created_allelereports,
            custom_annotations=data.get('customannotations'),
        )

        for snapshot_object in snapshot_objects:
            session.add(snapshot_object)

        analysis_interpretation.status = 'Done'
        analysis_interpretation.date_last_update = datetime.datetime.now()

        # un-tuple:
        all_allelereports = map(lambda a: a[0], reused_allelereports) + map(lambda a: a[1], created_allelereports)

        reused_referenceassessments = grouped_alleleassessments['referenceassessments']['reused']
        created_referenceassessments = grouped_alleleassessments['referenceassessments']['created']
        all_referenceassessments = reused_referenceassessments + created_referenceassessments

        session.commit()

        return {
            'allelereports': schemas.AlleleReportSchema().dump(
                all_allelereports, many=True).data,
            'alleleassessments': schemas.AlleleAssessmentSchema().dump(
                all_alleleassessents, many=True).data,
            'referenceassessments': schemas.ReferenceAssessmentSchema().dump(all_referenceassessments,
                                                                             many=True).data,
        }, 200


class AnalysisCollisionResource(Resource):
    def get(self, session, analysis_id):
        """
        Checks whether there are other analyses with
        alleles overlapping this analysis, AND
        having no valid classification in the system.

        The use case is to check whether the user could
        potentially be interpreting an allele at the same
        time as another user, duplicating the effort.

        Return the alleles in question and what user that it concerns.
        Do NOT return the analyses in question, this is not allowed.
        """

        aa = session.query(assessment.AlleleAssessment.allele_id).join(
            allele.Allele
        )

        # Subquery: Get all allele ids without any alleleassessments
        allele_ids_no_aa = session.query(allele.Allele.id).filter(not_(aa.exists()))

        # Subquery: Get all analyses that are ongoing
        analysis_ongoing_interpretation = session.query(sample.Analysis.id).join(
            sample.Interpretation
        ).filter(
            sample.Interpretation.status == 'Ongoing',
            sample.Analysis.id != analysis_id
        )

        # Subquery: Only include alleles which belongs to requested analysis
        analysis_alleles = session.query(allele.Allele.id).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(sample.Analysis.id == analysis_id)

        # Get all combinations of users and alleles where the analyses belongs to ongoing
        # interpretations and the alleles have no existing alleleassessment
        user_alleles = session.query(
            user.User.id,
            allele.Allele.id,
            gene.Genepanel.name,
            gene.Genepanel.version
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            sample.Interpretation
        ).filter(
            allele.Allele.id.in_(analysis_alleles),
            allele.Allele.id.in_(allele_ids_no_aa),
            sample.Analysis.id.in_(analysis_ongoing_interpretation),
            user.User.id == sample.Interpretation.user_id,
            gene.Genepanel.name == sample.Analysis.genepanel_name,
            gene.Genepanel.version == sample.Analysis.genepanel_version
        ).group_by(
            user.User.id,
            allele.Allele.id,
            gene.Genepanel.name,
            gene.Genepanel.version
        ).order_by(
            user.User.id
        ).limit(  # Just in case to prevent DB overload...
            200
        ).all()

        user_ids = set([ua[0] for ua in user_alleles])
        allele_ids = set([ua[1] for ua in user_alleles])

        # Load the full data for user and allele
        user_cache = session.query(user.User).filter(user.User.id.in_(user_ids)).all()
        allele_cache = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids)).all()
        genepanel_cache = dict()  # Will be filled later

        adl = AlleleDataLoader(session)
        result = list()
        # Generate result structure:
        #
        # [
        #   {
        #       "id": 1,
        #       "username": "testuser"
        #       "alleles": [
        #           {allele_data...}
        #       ],
        #       rest of user data...
        #   },
        #   {next entry...}
        # ]
        #
        # Genepanel is needed to select the default transcript, which
        # again is needed for showing relevant cDNA to the user
        for user_id, allele_id, gp_name, gp_version in user_alleles:
            user_in_result = next((u for u in result if u['id'] == user_id), None)
            if not user_in_result:
                user_obj = next(u for u in user_cache if u.id == user_id)
                dumped_user = schemas.UserSchema().dump(user_obj).data
                dumped_user['alleles'] = list()
                result.append(dumped_user)
                user_in_result = dumped_user
            allele_in_user_result = next((a for a in user_in_result['alleles'] if a['id'] == allele_id), None)
            if not allele_in_user_result:
                if (gp_name, gp_version) not in genepanel_cache:
                    # TODO: Query in a loop is a code smell re. performance,
                    # but complex primary keys are more hassle when prefilling cache...
                    gp_obj = session.query(gene.Genepanel).filter(
                        gene.Genepanel.name == gp_name,
                        gene.Genepanel.version == gp_version
                    ).one()
                    genepanel_cache[(gp_name, gp_version)] = gp_obj
                else:
                    gp_obj = genepanel_cache[(gp_name, gp_version)]

                allele_obj = next((a for a in allele_cache if a.id == allele_id))
                final_allele = adl.from_objs(
                    [allele_obj],
                    genepanel=gp_obj,
                    include_annotation=True,
                    include_custom_annotation=False,
                    include_allele_assessment=False,
                    include_reference_assessments=False
                )
                user_in_result['alleles'].append(final_allele[0])

        return result
