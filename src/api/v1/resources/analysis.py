from typing import Dict, Optional

from api import schemas
from api.schemas.pydantic.v1 import validate_output
from api.schemas.pydantic.v1.resources import AnalysisListResponse, AnalysisResponse
from api.util.util import authenticate, paginate, rest_filter
from api.v1.resource import LogRequestResource
from sqlalchemy import tuple_
from sqlalchemy.orm import Session
from vardb.datamodel import sample, user


class AnalysisListResource(LogRequestResource):
    @authenticate()
    @validate_output(AnalysisListResponse, paginated=True)
    @paginate
    @rest_filter
    def get(
        self,
        session: Session,
        rest_filter: Optional[Dict],
        page: int,
        per_page: int,
        user: user.User,
        **kwargs,
    ):
        """
        Returns a list of analyses.

        * Supports `q=` filtering.
        * Supports pagination.
        ---
        summary: List analyses
        tags:
          - Analysis
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
                $ref: '#/definitions/Analysis'
            description: List of analyses
        """
        if rest_filter is None:
            rest_filter = dict()
        if not ("genepanel_name", "genepanel_version") in rest_filter:
            rest_filter[("genepanel_name", "genepanel_version")] = [
                (gp.name, gp.version) for gp in user.group.genepanels
            ]
        return self.list_query(
            session,
            sample.Analysis,
            schema=schemas.AnalysisSchema(),
            rest_filter=rest_filter,
            per_page=per_page,
            page=page,
        )


class AnalysisResource(LogRequestResource):
    @authenticate()
    @validate_output(AnalysisResponse)
    def get(self, session: Session, analysis_id: int, user: user.User):
        """
        Returns a single analysis.
        ---
        summary: Get analysis
        tags:
          - Analysis
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id
        responses:
          200:
            schema:
                $ref: '#/definitions/Analysis'
            description: Analysis object
        """
        a = (
            session.query(sample.Analysis)
            .filter(
                sample.Analysis.id == analysis_id,
                tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_(
                    (gp.name, gp.version) for gp in user.group.genepanels
                ),
            )
            .one()
        )
        analysis = schemas.AnalysisSchema().dump(a).data
        return analysis
