from vardb.datamodel import assessment

from api import schemas
from api.util.util import paginate, rest_filter, authenticate
from api.v1.resource import LogRequestResource


class AlleleReportResource(LogRequestResource):
    @authenticate()
    def get(self, session, ar_id=None, user=None):
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
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, per_page=10000, user=None):
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
