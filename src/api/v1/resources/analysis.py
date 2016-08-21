from sqlalchemy import desc

from vardb.datamodel import sample, user, assessment

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
from api.util.assessmentcreator import AssessmentCreator
from api.util.allelereportcreator import AlleleReportCreator
from api.v1.resource import Resource


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


class AnalysisListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
        analyses = self.list_query(session, sample.Analysis, schema=schemas.AnalysisSchema(), rest_filter=rest_filter)
        for analysis in analyses:
            analysis['current_interpretation'] = get_current_interpretation(analysis)
        return analyses


class AnalysisResource(Resource):

    def get(self, session, analysis_id):

        a = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
        analysis = schemas.AnalysisSchema().dump(a).data
        analysis['current_interpretation'] = get_current_interpretation(analysis)
        return analysis


class AnalysisActionOverrideResource(Resource):

    @request_json(['user_id'])
    def post(self, session, analysis_id, data=None):
        """
        Lets an user take over an analysis, by replacing the
        current interpretation's user_id with the input user_id.
        """
        # Get user by username
        new_user = session.query(user.User).filter(
            user.User.id == data['user_id']
        ).one()

        a = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
        analysis = schemas.AnalysisSchema().dump(a).data
        int_id = get_current_interpretation(analysis)

        i = session.query(sample.Interpretation).filter(
            sample.Interpretation.id == int_id
        ).one()

        # db will throw exception if user_id is not a valid id
        # since it's a foreign key
        i.user = new_user
        session.commit()
        return None, 200


class AnalysisActionStartResource(Resource):

    @request_json(['user_id'])
    def post(self, session, analysis_id, data=None):
        """
        Start an interpretation, setting it's status to 'In progress'
        """
        # Get user by username
        start_user = session.query(user.User).filter(
            user.User.id == data['user_id']
        ).one()

        a = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
        analysis = schemas.AnalysisSchema().dump(a).data
        int_id = get_current_interpretation(analysis)

        i = session.query(sample.Interpretation).filter(
            sample.Interpretation.id == int_id
        ).one()

        if i.status != 'Not started':
            raise ApiError("Interpretation already started.")

        # db will throw exception if user_id is not a valid id
        # since it's a foreign key
        i.user = start_user
        i.status = 'Ongoing'
        session.commit()
        return None, 200


class AnalysisActionMarkReviewResource(Resource):

    def post(self, session, analysis_id):
        # TODO: Validate that user is same as user on interpretation
        # TODO: Consider some way to validate that it should be completable

        a = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
        analysis = schemas.AnalysisSchema().dump(a).data
        int_id = get_current_interpretation(analysis)

        a = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
        analysis = schemas.AnalysisSchema().dump(a).data
        int_id = get_current_interpretation(analysis)

        i = session.query(sample.Interpretation).filter(
            sample.Interpretation.id == int_id
        ).one()
        i.status = 'Done'

        # Create next interpretation
        next_i = sample.Interpretation()
        next_i.analysis_id = i.analysis_id
        next_i.state = i.state

        session.add(next_i)
        session.commit()
        return None, 200


class AnalysisActionReopenResource(Resource):

    def post(self, session, analysis_id):
        a = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
        analysis = schemas.AnalysisSchema().dump(a).data
        if get_current_interpretation(analysis) is not None:
            raise ApiError("Analysis is already pending or ongoing. Cannot reopen.")

        i = session.query(sample.Interpretation).filter(
            sample.Analysis.id == analysis_id
        ).order_by(desc(sample.Interpretation.id)).first()

        # Create next interpretation
        next_i = sample.Interpretation()
        next_i.analysis_id = i.analysis_id
        next_i.state = i.state

        session.add(next_i)
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

        The user must provide a list of alleleassessments, referenceassessments and allelereports.
        For each assessment/report, if an 'id' field is not part of the data, it will create
        a new assessment/report in the database. It will then link the analysis to this assessment/report.
        If an 'id' field does exist, it will check if the assessment/report with this id
        exists in the database, then link the analysis to this assessment/report. If the 'id' doesn't
        exists, an ApiError is given.

        In other words, if reusing a preexisting assessment/report, you can pass in just it's 'id',
        otherwise pass in all the data needed to create a new assessment/report (without an 'id' field).

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
                    "reference_id": 2
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

        aa = result['alleleassessments']['reused'] + result['alleleassessments']['created']
        ra = result['referenceassessments']['reused'] + result['referenceassessments']['created']

        arc = AlleleReportCreator(session)
        arc_result = arc.create_from_data(data['allelereports'], aa)

        arc = arc_result['reused'] + arc_result['created']

        # Mark all analysis' interpretations as done (we do all just in case)
        connected_interpretations = session.query(sample.Interpretation).filter(
            sample.Interpretation.analysis_id == analysis_id
        ).all()

        for i in connected_interpretations:
            i.status = 'Done'
        session.commit()

        return {
            'allelereports': schemas.AlleleReportSchema().dump(arc, many=True).data,
            'alleleassessments': schemas.AlleleAssessmentSchema().dump(aa, many=True).data,
            'referenceassessments': schemas.ReferenceAssessmentSchema().dump(ra, many=True).data,
        }, 200
