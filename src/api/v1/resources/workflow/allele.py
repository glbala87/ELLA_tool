import datetime
import itertools

from sqlalchemy import desc, not_

from vardb.datamodel import workflow, user, assessment, sample, genotype, allele, annotation, gene

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
from api.util.assessmentcreator import AssessmentCreator
from api.util.allelereportcreator import AlleleReportCreator
from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader
from api.v1.resource import Resource
from api.config import config


def get_latest_alleleinterpretation(session, allele_id):
    return session.query(workflow.AlleleInterpretation).filter(
        workflow.AlleleInterpretation.allele_id == allele_id
    ).order_by(workflow.AlleleInterpretation.id.desc()).first()


class AlleleInterpretationResource(Resource):

    def get(self, session, allele_id):
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
        allele_interpretation = session.query(workflow.AlleleInterpretation).filter(
            workflow.AlleleInterpretation.allele_id == allele_id
        ).order_by(workflow.AlleleInterpretation.id.desc()).first()

        return schemas.AlleleInterpretationSchema().dump(allele_interpretation).data

    @request_json(
        [],
        allowed=[
            'state',
            'user_state',
            'user_id'
        ]
    )
    def patch(self, session, allele_id, data=None):
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

        allele_interpretation = get_latest_alleleinterpretation(session, allele_id)

        # If interpretation is completed, no changes are allowed
        if allele_interpretation.status == 'Done':
            raise ApiError("Cannot PATCH interpretation with status 'DONE'")
        elif allele_interpretation.status == 'Not started':
            raise ApiError("Interpretation not started. Call it's start action to begin the interpretation.")

        # Check that user is same as before
        if allele_interpretation.user_id:
            if allele_interpretation.user_id != data['user_id']:
                raise ApiError("User id doesn't match existing user_id")

        # Check if new state is different than old, if so make a copy of the old into state_history
        if data['state'] != allele_interpretation.state:
            if 'history' not in allele_interpretation.state_history:
                allele_interpretation.state_history['history'] = list()
            allele_interpretation.state_history['history'].insert(0, {
                'time': datetime.datetime.now().isoformat(),
                'state': allele_interpretation.state,
                'user_id': allele_interpretation.user_id
            })

        # Patch (overwrite) state fields with new values
        allele_interpretation.state = data['state']
        allele_interpretation.user_state = data['user_state']

        allele_interpretation.date_last_update = datetime.datetime.now()

        session.commit()
        return None, 200


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
        # Get user by username
        new_user = session.query(user.User).filter(
            user.User.id == data['user_id']
        ).one()

        allele_interpretation = get_latest_alleleinterpretation(session, allele_id)

        if allele_interpretation.status != 'Ongoing':
            raise ApiError("Cannot reassign interpretation that is not 'Ongoing'.")

        # db will throw exception if user_id is not a valid id
        # since it's a foreign key
        allele_interpretation.user = new_user
        session.commit()
        return None, 200


class AlleleActionStartResource(Resource):

    @request_json(['user_id'])
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
        # Get user by username
        start_user = session.query(user.User).filter(
            user.User.id == data['user_id']
        ).one()

        allele_interpretation = get_latest_alleleinterpretation(session, allele_id)

        if not allele_interpretation:
            allele_interpretation = workflow.AlleleInterpretation()
            allele_interpretation.allele_id = allele_id
            session.add(allele_interpretation)
        elif allele_interpretation.status != 'Not started':
            raise ApiError("Cannot start existing interpretation where status = {}".format(allele_interpretation.status))

        # db will throw exception if user_id is not a valid id
        # since it's a foreign key
        allele_interpretation.user = start_user
        allele_interpretation.status = 'Ongoing'
        session.commit()
        return None, 200


class AlleleActionMarkReviewResource(Resource):

    def post(self, session, allele_id):
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
        # TODO: Validate that user is same as user on interpretation

        allele_interpretation = get_latest_alleleinterpretation(session, allele_id)

        if allele_interpretation.status != 'Ongoing':
            raise ApiError("Interpretation is not ongoing.")

        allele_interpretation.status = 'Done'
        allele_interpretation.date_last_update = datetime.datetime.now()

        # Create next interpretation
        allele_interpretation_next = workflow.AlleleInterpretation()
        allele_interpretation_next.allele_id = allele_interpretation.allele_id
        allele_interpretation_next.state = allele_interpretation.state

        session.add(allele_interpretation_next)
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

        allele_interpretation = get_latest_alleleinterpretation(session, allele_id)

        if allele_interpretation is None:
            raise ApiError("There are no existing interpretations for this allele. Use the start action instead.")

        if not allele_interpretation.status == 'Done':
            raise ApiError("Allele interpretation is already 'Not started' or 'Ongoing'. Cannot reopen.")

        # Create next interpretation
        allele_interpretation_next = workflow.AlleleInterpretation()
        allele_interpretation_next.allele_id = allele_interpretation.allele_id
        allele_interpretation_next.state = allele_interpretation.state

        session.add(allele_interpretation_next)
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
                    "id": 9
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
                    "id": 9
                    "allele_id": 6
                }
            ]
        }

        """

        ac = AssessmentCreator(session)

        result = ac.create_from_data(
            data['alleleassessments'],
            data['referenceassessments'],
        )

        all_alleleassessments = result['alleleassessments']['reused'] + result['alleleassessments']['created']
        all_referenceassessments = result['referenceassessments']['reused'] + result['referenceassessments']['created']

        arc = AlleleReportCreator(session)
        arc_result = arc.create_from_data(data['allelereports'], all_alleleassessments)

        all_allelereports = arc_result['reused'] + arc_result['created']

        connected_interpretations = session.query(sample.Interpretation).filter(
            sample.Interpretation.analysis_id == analysis_id
        ).all()

        # Check that exactly one is ongoing
        if not len([i for i in connected_interpretations if i.status == 'Ongoing']) == 1:
            raise ApiError("There's more than one ongoing interpretation. This shouldn't happen!")

        if [i for i in connected_interpretations if i.status == 'Not started']:
            raise ApiError("One or more interpretations are marked as 'Not started'. Finalization not possible.")

        current_interpretation = next((i for i in connected_interpretations if i.status == 'Ongoing'), None)

        if current_interpretation is None:
            raise ApiError("Trying to finalize analysis with no 'Ongoing' interpretations")

        # Create analysisfinalized objects:
        # We need to fetch all allele ids to store info for.
        # Allele ids are provided by the 'Ongoing' interpretation

        i = InterpretationDataLoader(session, config).from_id(current_interpretation.id)

        allele_ids = i['allele_ids']
        excluded = i['excluded_allele_ids']

        all_allele_ids = allele_ids + list(itertools.chain(*excluded.values()))

        # Fetch connected annotation ids
        allele_annotation = session.query(
            allele.Allele.id,
            annotation.Annotation.id,
            annotation.CustomAnnotation.id
        ).outerjoin(  # Outer join since not all alleles have customannotation
            annotation.Annotation,
            annotation.CustomAnnotation,
        ).filter(
            annotation.Annotation.date_superceeded == None,
            annotation.CustomAnnotation.date_superceeded == None,
            allele.Allele.id.in_(all_allele_ids)
        ).all()

        def create_analaysisfinalize(allele_id, alleleassessment_id=None, allelereport_id=None, filtered=None):
            _, annotation_id, customannotation_id = next(a for a in allele_annotation if a[0] == allele_id)
            af_data = {
                'analysis_id': analysis_id,
                'allele_id': allele_id,
                'annotation_id': annotation_id,
                'customannotation_id': customannotation_id,
                'alleleassessment_id': alleleassessment_id,
                'allelereport_id': allelereport_id,
                'filtered': filtered
            }
            af = sample.AnalysisFinalized(**af_data)
            return af

        for allele_id in allele_ids:
            af = create_analaysisfinalize(
                allele_id,
                alleleassessment_id=next(a.id for a in all_alleleassessments if a.allele_id == allele_id),
                allelereport_id=next(a.id for a in all_allelereports if a.allele_id == allele_id),
            )
            session.add(af)

        for allele_id in excluded['class1']:
            af = create_analaysisfinalize(allele_id, filtered='CLASS1')
            session.add(af)

        for allele_id in excluded['intronic']:
            af = create_analaysisfinalize(allele_id, filtered='INTRON')
            session.add(af)

        # Mark all analysis' interpretations as done (we do all just in case)
        for ci in connected_interpretations:
            ci.status = 'Done'

        session.commit()

        return {
            'allelereports': schemas.AlleleReportSchema().dump(all_allelereports, many=True).data,
            'alleleassessments': schemas.AlleleAssessmentSchema().dump(all_alleleassessments, many=True).data,
            'referenceassessments': schemas.ReferenceAssessmentSchema().dump(all_referenceassessments, many=True).data,
        }, 200

'''
class AnalysisCollisionResource(Resource):
    def get(self, session, allele_id):
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
'''
