import datetime
from vardb.datamodel import sample, user, assessment

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
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
        ).order_by(sample.Interpretation.id).first()

        # Create next interpretation
        next_i = sample.Interpretation()
        next_i.analysis_id = i.analysis_id
        next_i.state = i.state

        session.add(next_i)
        session.commit()
        return None, 200


class AnalysisActionFinalizeResource(Resource):

    def post(self, session, analysis_id):
        # TODO: Validate that user is same as user on interpretation via internal auth
        # when that is ready


        def curate_and_replace(noncurated_assessments, previous_assessments, compare_func):
            """
            Curates noncurated [Allele|Reference]Assessments and marks previous ones as
            superceeded. The newly curated assessment is linked to the previous one.
            """
            for noncurated in noncurated_assessments:
                # Normally there should be just one previous,
                # but it is safer to check as if there were many
                for previous in previous_assessments:
                    if compare_func(noncurated, previous):
                        previous.dateSuperceeded = datetime.datetime.now()
                        noncurated.previousAssessment_id = previous.id

            # Set status as curated
            for noncurated in noncurated_assessments:
                noncurated.status = 1

        noncurated_aa = session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.analysis_id == analysis_id
        ).all()

        noncurated_ra = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.analysis_id == analysis_id
        ).all()


        # Curate and replace AlleleAssessments
        previous_aa = session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.allele_id.in_([a.allele_id for a in noncurated_aa]),
            assessment.AlleleAssessment.dateSuperceeded == None,
            assessment.AlleleAssessment.status == 1
        ).all()

        curate_and_replace(
            noncurated_aa,
            previous_aa,
            lambda n, p: n.allele_id == p.allele_id
        )

        # Curate and replace ReferenceAssessments
        previous_ra = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.allele_id.in_([a.allele_id for a in noncurated_ra]),
            assessment.ReferenceAssessment.reference_id.in_([a.reference_id for a in noncurated_ra]),
            assessment.ReferenceAssessment.dateSuperceeded == None,
            assessment.ReferenceAssessment.status == 1
        ).all()

        curate_and_replace(
            noncurated_ra,
            previous_ra,
            lambda n, p: n.allele_id == p.allele_id and
            n.reference.id == p.reference_id
        )

        # Attach ReferenceAssessments to AlleleAssessments

        # Get all relevant (curated) ReferenceAssessments (based on allele_id)
        # Don't filter on analysis_id, since there can be RAs that are reused from
        # previous analyses.
        relevant_ra = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.allele_id.in_([a.allele_id for a in noncurated_aa]),
            assessment.ReferenceAssessment.dateSuperceeded == None,
            assessment.ReferenceAssessment.status == 1
        )
        for aa in noncurated_aa:
            aa.referenceAssessments = [ra for ra in relevant_ra if ra.allele_id == aa.allele_id]

        # Mark all analysis' interpretations as done (we do all just in case)
        connected_interpretations = session.query(sample.Interpretation).filter(
            sample.Interpretation.analysis_id == analysis_id
        ).all()

        for i in connected_interpretations:
            i.status = 'Done'
        session.commit()

        return None, 200
