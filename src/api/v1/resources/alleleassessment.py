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
            'classification',
            'analysis_id',
            'user_id',
        ],
        allowed=[
            # 'id' is not included on purpose, as the endpoint should always result in a new assessment
            'evaluation',
            'referenceassessments'
        ]
    )
    def post(self, session, data=None):
        """
        Creates a new AlleleAssessment for a provided allele_id.

        Data example:
        {
            # New assessment will be created, superceding any old one
            "user_id": 1,
            "allele_id": 2,
            "classification": "3",
            "evaluation": {...data...},
            "analysis_id": 3,
            "referenceassessments": [  # Optional
                {
                    "allele_id": 2,
                    "analysis_id": 3,
                    "evaluation": {...data...}
                },
                {
                    "analysis_id": 3,
                    "allele_id": 2,
                    "id": 3  # Reuse existing referenceassessment, but link it to this alleleassessment
                }
            ]
        }

        Provided data can also be a list of items.
        """
        if not isinstance(data, list):
            data = [data]

        ac = AssessmentCreator(session)
        result = ac.create_from_data(alleleassessments=data)

        aa = result['alleleassessments']['reused'] + result['alleleassessments']['created']
        if not isinstance(data, list):
            aa = aa[0]

        session.commit()
        return schemas.AlleleAssessmentSchema().dump(aa, many=isinstance(aa, list)).data
