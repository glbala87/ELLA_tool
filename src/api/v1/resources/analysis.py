
from vardb.datamodel import assessment, sample, genotype

from api import schemas, ApiError
from api.util.util import paginate, rest_filter
from api.v1.resource import Resource


class AnalysisListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
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
        analyses = self.list_query(session, sample.Analysis, schema=schemas.AnalysisSchema(), rest_filter=rest_filter)
        return analyses


class AnalysisResource(Resource):

    def get(self, session, analysis_id):
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
        a = session.query(sample.Analysis).filter(sample.Analysis.id == analysis_id).one()
        analysis = schemas.AnalysisSchema().dump(a).data
        return analysis

    def delete(self, session, analysis_id, override=False):
        """
        Deletes an analysis from the system, including corresponding samples, genotypes
        and interpretations. Alleles that were imported as part of the analysis are
        left intact, as we cannot know whether they were also "imported" (i.e in use)
        by other sources as well.

        Not callable by API as of yet.

        TODO: Make proper API description when included in API.
        """
        # NOTE: Not callable by API since override param will be false.
        # We cannot enable this in API until we have user authorization
        # It is however used by cli tool

        if not override:
            return None, 403  # Report as forbidden

        # If any alleleassessments points to this analysis, it cannot be removed
        # We'll get an error in any case, so this check is mostly to
        # present an error to the user
        if session.query(assessment.AlleleAssessment.id).filter(
            assessment.AlleleAssessment.analysis_id == analysis_id
        ).count():
            raise ApiError("One or more alleleassessments are pointing to this analysis. It's removal is not allowed.'")

        analysis = session.query(sample.Analysis).join(
            genotype.Genotype,
            sample.Sample,
        ).filter(
            sample.Analysis.id == analysis_id
        ).one()

        # Remove samples and genotypes
        samples = analysis.samples
        for s in samples:
            for g in s.genotypes:
                session.delete(g)
            session.delete(s)
        for i in analysis.interpretations:
            session.delete(i)

        # Clean up corresponding analysisfinalized entries
        # Will rarely happen (but can in principle), since we forbid to remove
        # analyses that have alleleassessments pointing to it.
        afs = session.query(sample.AnalysisFinalized).filter(
            sample.AnalysisFinalized.analysis_id == analysis_id
        ).all()
        for af in afs:
            session.delete(af)

        # Finally, delete analysis
        session.delete(analysis)

        session.commit()

        return None, 200


