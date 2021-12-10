from typing import Dict, Optional
from api import schemas
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import AlleleAssessmentResponse, AlleleAssessmentListResponse
from api.util.util import authenticate, paginate, rest_filter
from api.v1.resource import LogRequestResource
from sqlalchemy.orm import Session
from vardb.datamodel import assessment, user


class AlleleAssessmentResource(LogRequestResource):
    @authenticate()
    @validate_output(AlleleAssessmentResponse)
    def get(self, session: Session, aa_id: int, user: user.User):
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
    @validate_output(AlleleAssessmentListResponse, paginated=True)
    @paginate
    @rest_filter
    def get(
        self,
        session: Session,
        rest_filter: Optional[Dict],
        page: int,
        per_page: int,
        user: user.User,
    ):
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
