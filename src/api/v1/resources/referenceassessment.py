import datetime

from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, request_json

from api.v1.resource import Resource


class ReferenceAssessmentResource(Resource):

    def get(self, session, ra_id=None):
        a = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.id == ra_id
        ).one()
        result = schemas.ReferenceAssessmentSchema(strict=True).dump(a).data
        return result


class ReferenceAssessmentListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
        return self.list_query(
            session,
            assessment.ReferenceAssessment,
            schemas.ReferenceAssessmentSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            num_per_page=100000  # FIXME: Fix proper pagination...
        )

    @request_json(
        [
            'allele_id',
            'reference_id',
            'evaluation',
            'genepanelName',
            'genepanelVersion',
            'analysis_id',
            'user_id'
        ],
        True
    )
    def post(self, session, data=None):
        """
        Creates or updates the existing ReferenceAssessment for a provided
        allele_id and reference_id. Is conceptually similar to AlleleAssessment.

        It follows the following rules:
        1. If no entries exists already for this allele+reference, create a new one.
        2. If a non-curated (status=0) entry exists already, overwrite it.
        3. If a curated entry exists, create a new non-curated one.
        """

        raise RuntimeError("FIXME! REMOVE RESOURCE?")

        obj = schemas.ReferenceAssessmentSchema(strict=True).load(data).data
        obj.dateLastUpdate = datetime.datetime.now()

        # If there exists an assessment already for this allele_id which is not yet curated,
        # we update that one instead.
        existing_ass = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.allele_id == obj.allele_id,
            assessment.ReferenceAssessment.reference_id == obj.reference_id,
            assessment.ReferenceAssessment.dateSuperceeded == None,
            assessment.ReferenceAssessment.status == 0
        ).one_or_none()

        if existing_ass:
            obj.id = existing_ass.id
            session.merge(obj)
        else:
            session.add(obj)

        session.commit()

        # Reload to fetch all data
        new_obj = session.query(assessment.ReferenceAssessment).filter(
            assessment.ReferenceAssessment.id == obj.id
        ).one()
        return schemas.ReferenceAssessmentSchema(strict=True).dump(new_obj).data, 200


