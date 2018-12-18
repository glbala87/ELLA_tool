from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, request_json, authenticate
from api.util.assessmentcreator import AssessmentCreator
from api.v1.resource import LogRequestResource


class AlleleAssessmentResource(LogRequestResource):
    @authenticate()
    def get(self, session, aa_id=None, user=None):
        """
        Returns a single alleleassessment.
        ---
        summary: Get alleleassessment
        tags:
          - AlleleAssessment
        parameters:
          - name: aa_id
            in: path
            type: integer
            description: AlleleAssessment id
        responses:
          200:
            schema:
                $ref: '#/definitions/AlleleAssessment'
            description: AlleleAssessment object
        """
        a = (
            session.query(assessment.AlleleAssessment)
            .filter(assessment.AlleleAssessment.id == aa_id)
            .one()
        )
        result = schemas.AlleleAssessmentSchema(strict=True).dump(a).data
        return result


class AlleleAssessmentListResource(LogRequestResource):
    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, per_page=10000, user=None):
        """
        Returns a list of alleleassessments.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List alleleassessments
        tags:
          - AlleleAssessment
        parameters:
          - name: q
            in: query
            type: string
            description: JSON filter query
        responses:
          200:
            schema:
              type: array
              items:
                $ref: '#/definitions/AlleleAssessment'
            description: List of alleleassessments
        """
        # TODO: Figure out how to deal with pagination
        return self.list_query(
            session,
            assessment.AlleleAssessment,
            schemas.AlleleAssessmentSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            per_page=per_page,
        )
