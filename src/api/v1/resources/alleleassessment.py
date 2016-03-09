import datetime

from vardb.datamodel import assessment

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
from api.util.assessmentcreator import AssessmentCreator
from api.v1.resource import Resource


class AlleleAssessmentResource(Resource):

    def get(self, session, aa_id=None):
        a = session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.id == aa_id
        ).one()
        result = schemas.AlleleAssessmentSchema(strict=True).dump(a)
        return result


class AlleleAssessmentListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=10000):
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
            'annotation_id',
            'classification',
            'genepanelName',
            'genepanelVersion',
            'analysis_id',
            'user_id',
            # 'transcript_id'  # TODO: Require when support in frontend
        ],
        allowed=[
            'evaluation',
            'status'
        ]
    )
    def post(self, session, data=None):
        """
        Creates or updates the existing AlleleAssessment for a provided allele_id.

        It follows the following rules:
        1. If no entries exists already for this allele, create a new one.
        2. If a non-curated (status=0) entry exists already, overwrite it.
        3. If a curated entry exists, create a new one. If status is set to 1,
           it is curated directly, otherwise it's left as non-curated.
        """
        if 'status' not in data:
            data['status'] = 0

        obj = schemas.AlleleAssessmentSchema(strict=True).load(data).data
        obj.dateLastUpdate = datetime.datetime.now()

        if obj.status == 0:
            existing_ass = session.query(assessment.AlleleAssessment).filter(
                assessment.AlleleAssessment.allele_id == obj.allele_id,
                assessment.AlleleAssessment.dateSuperceeded == None,
                assessment.AlleleAssessment.status == 0
            ).one_or_none()
            if existing_ass:
                # If there exists an assessment already for this allele_id which is not yet curated,
                # we update that one instead.
                obj.id = existing_ass.id
                session.merge(obj)
            else:
                session.add(obj)
        elif obj.status == 1:
            AssessmentCreator(session).curate_and_replace(alleleassessments=[obj])
        else:
            raise ApiError("Invalid status {}".format(obj.status))

        session.commit()

        # Reload to fetch all data
        new_obj = session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.id == obj.id
        ).one()
        return schemas.AlleleAssessmentSchema(strict=True).dump(new_obj).data, 200
