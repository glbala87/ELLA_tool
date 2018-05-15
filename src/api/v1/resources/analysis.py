from sqlalchemy import tuple_
from vardb.datamodel import assessment, sample, genotype, workflow

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, authenticate
from api.v1.resource import LogRequestResource


class AnalysisListResource(LogRequestResource):

    @authenticate()
    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, per_page=None, user=None):
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
                (gp.name, gp.version) for gp in user.group.genepanels]
        return self.list_query(
            session,
            sample.Analysis,
            schema=schemas.AnalysisSchema(),
            rest_filter=rest_filter,
            per_page=per_page,
            page=page
        )


class AnalysisResource(LogRequestResource):

    @authenticate()
    def get(self, session, analysis_id, user=None):
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
        a = session.query(sample.Analysis).filter(
            sample.Analysis.id == analysis_id,
            tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_(
                (gp.name, gp.version) for gp in user.group.genepanels)
        ).one()
        analysis = schemas.AnalysisSchema().dump(a).data
        return analysis
