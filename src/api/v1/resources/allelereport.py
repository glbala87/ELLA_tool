from typing import Dict, Optional

from api import schemas
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import AlleleReportListResponse, AlleleReportResponse
from api.util.util import authenticate, paginate, rest_filter
from api.v1.resource import LogRequestResource
from sqlalchemy.orm import Session
from vardb.datamodel import assessment


class AlleleReportResource(LogRequestResource):
    @authenticate()
    @validate_output(AlleleReportResponse)
    def get(self, session: Session, ar_id: int, **kwargs):
        """
        Returns a single allelereport.
        ---
        summary: Get allelereport
        tags:
          - AlleleReport
        parameters:
          - name: ar_id
            in: path
            type: integer
            description: AlleleReport id
        responses:
          200:
            schema:
                $ref: '#/definitions/AlleleReport'
            description: AlleleReport object
        """
        a = session.query(assessment.AlleleReport).filter(assessment.AlleleReport.id == ar_id).one()
        result = schemas.AlleleReportSchema(strict=True).dump(a).data
        return result


class AlleleReportListResource(LogRequestResource):
    @authenticate()
    @validate_output(AlleleReportListResponse, paginated=True)
    @paginate
    @rest_filter
    def get(
        self,
        session: Session,
        rest_filter: Optional[Dict],
        page: int,
        per_page: int = 10000,
        **kwargs,
    ):
        """
        Returns a list of allelereports.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List allelereports
        tags:
          - AlleleReport
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
                $ref: '#/definitions/AlleleReport'
            description: List of allelereports
        """
        # TODO: Figure out how to deal with pagination
        return self.list_query(
            session,
            assessment.AlleleReport,
            schemas.AlleleReportSchema(strict=True),
            rest_filter=rest_filter,
            page=page,
            per_page=per_page,
        )
