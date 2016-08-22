import datetime

from vardb.datamodel import assessment

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
from api.v1.resource import Resource
from api.util.allelereportcreator import AlleleReportCreator


class AlleleReportResource(Resource):

    def get(self, session, ar_id=None):
        a = session.query(assessment.AlleleReport).filter(
            assessment.AlleleReport.id == ar_id
        ).one()
        result = schemas.AlleleReportSchema(strict=True).dump(a).data
        return result


class AlleleReportListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=10000):
        # TODO: Figure out how to deal with pagination
        return self.list_query(
            session,
            assessment.AlleleReport,
            schemas.AlleleReportSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            num_per_page=num_per_page
        )

    @request_json(
        [
            'allele_id',
            'evaluation',
            'user_id',
        ],
        allowed=[
            # 'id' is excluded on purpose, as the endpoint should always result in a new assessment
            'analysis_id'
        ]
    )
    def post(self, session, data=None):
        """
        Creates a new AlleleReport for a provided allele_id.

        If created as part of finalizing an analysis, check the analysis resource instead.

        Data example:
        [
            {
                # New report will be created, superceding any old one
                "user_id": 1,
                "allele_id": 2,
                "evaluation": {...data...},
                "analysis_id": 3,  # Optional, should be given when report is made in context of analysis
                "alleleassessment_id": 3,  # Optional, should be given when report is made in context of an alleleassessment
            },
            {
                "id": 4,  # Existing will be reused, so no report will be created...
                ...
            }
        ]

        Provided data can also be a list of items.
        """
        if not isinstance(data, list):
            data = [data]

        # Extract any alleleassessment_ids for passing into AlleleReportCreator
        aa_ids = [d['alleleassessment_id'] for d in data if 'alleleassessment_id' in d]
        aa = session.query(assessment.AlleleAssessment).filter(
            assessment.AlleleAssessment.id.in_(aa_ids)
        ).all()

        arc = AlleleReportCreator(session)
        result = arc.create_from_data(data, alleleassessments=aa)

        ar = result['alleleassessments']['reused'] + result['alleleassessments']['created']
        if not isinstance(data, list):
            ar = ar[0]

        session.commit()
        return schemas.AlleleReportSchema().dump(ar, many=isinstance(ar, list)).data
