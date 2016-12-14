import itertools

from sqlalchemy import desc, not_

from vardb.datamodel import user, assessment, sample, genotype, allele, annotation, gene

from api import schemas, ApiError
from api.util.util import paginate, rest_filter, request_json
from api.util.assessmentcreator import AssessmentCreator
from api.util.allelereportcreator import AlleleReportCreator
from api.util.alleledataloader import AlleleDataLoader
from api.util.interpretationdataloader import InterpretationDataLoader
from api.v1.resource import Resource
from api.config import config


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

    @request_json(['properties'])
    def patch(self, session, analysis_id, data=None):
        """
        Updates an analysis.
        ---
        summary: Update analysis
        tags:
          - Analysis
        parameters:
          - name: analysis_id
            in: path
            type: integer
            description: Analysis id
          - data:
            in: body
            required: true
            schema:
              title: Analysis properties
              type: object
              required:
                - properties
              properties:
                properties:
                  description: Properties data
                  type: object
        responses:
          200:
            schema:
                $ref: '#/definitions/Analysis'
            description: Analysis object
        """
        a = session.query(sample.Analysis).filter(
            sample.Analysis.id == analysis_id
        ).one()

        a.properties = data['properties']
        session.commit()
        return schemas.AnalysisSchema().dump(a).data, 200

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


class AnalysisCollisionResource(Resource):
    def get(self, session, analysis_id):
        """
        Checks whether there are other analyses with
        alleles overlapping this analysis, AND
        having no valid classification in the system.

        The use case is to check whether the user could
        potentially be interpreting an allele at the same
        time as another user, duplicating the effort.

        Return the alleles in question and what user that it concerns.
        Do NOT return the analyses in question, this is not allowed.
        """

        aa = session.query(assessment.AlleleAssessment.allele_id).join(
            allele.Allele
        )

        # Subquery: Get all allele ids without any alleleassessments
        allele_ids_no_aa = session.query(allele.Allele.id).filter(not_(aa.exists()))

        # Subquery: Get all analyses that are ongoing
        analysis_ongoing_interpretation = session.query(sample.Analysis.id).join(
            sample.Interpretation
        ).filter(
            sample.Interpretation.status == 'Ongoing',
            sample.Analysis.id != analysis_id
        )

        # Subquery: Only include alleles which belongs to requested analysis
        analysis_alleles = session.query(allele.Allele.id).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis
        ).filter(sample.Analysis.id == analysis_id)

        # Get all combinations of users and alleles where the analyses belongs to ongoing
        # interpretations and the alleles have no existing alleleassessment
        user_alleles = session.query(
            user.User.id,
            allele.Allele.id,
            gene.Genepanel.name,
            gene.Genepanel.version
        ).join(
            genotype.Genotype.alleles,
            sample.Sample,
            sample.Analysis,
            sample.Interpretation
        ).filter(
            allele.Allele.id.in_(analysis_alleles),
            allele.Allele.id.in_(allele_ids_no_aa),
            sample.Analysis.id.in_(analysis_ongoing_interpretation),
            user.User.id == sample.Interpretation.user_id,
            gene.Genepanel.name == sample.Analysis.genepanel_name,
            gene.Genepanel.version == sample.Analysis.genepanel_version
        ).group_by(
            user.User.id,
            allele.Allele.id,
            gene.Genepanel.name,
            gene.Genepanel.version
        ).order_by(
            user.User.id
        ).limit(  # Just in case to prevent DB overload...
            200
        ).all()

        user_ids = set([ua[0] for ua in user_alleles])
        allele_ids = set([ua[1] for ua in user_alleles])

        # Load the full data for user and allele
        user_cache = session.query(user.User).filter(user.User.id.in_(user_ids)).all()
        allele_cache = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids)).all()
        genepanel_cache = dict()  # Will be filled later

        adl = AlleleDataLoader(session)
        result = list()
        # Generate result structure:
        #
        # [
        #   {
        #       "id": 1,
        #       "username": "testuser"
        #       "alleles": [
        #           {allele_data...}
        #       ],
        #       rest of user data...
        #   },
        #   {next entry...}
        # ]
        #
        # Genepanel is needed to select the default transcript, which
        # again is needed for showing relevant cDNA to the user
        for user_id, allele_id, gp_name, gp_version in user_alleles:
            user_in_result = next((u for u in result if u['id'] == user_id), None)
            if not user_in_result:
                user_obj = next(u for u in user_cache if u.id == user_id)
                dumped_user = schemas.UserSchema().dump(user_obj).data
                dumped_user['alleles'] = list()
                result.append(dumped_user)
                user_in_result = dumped_user
            allele_in_user_result = next((a for a in user_in_result['alleles'] if a['id'] == allele_id), None)
            if not allele_in_user_result:
                if (gp_name, gp_version) not in genepanel_cache:
                    # TODO: Query in a loop is a code smell re. performance,
                    # but complex primary keys are more hassle when prefilling cache...
                    gp_obj = session.query(gene.Genepanel).filter(
                        gene.Genepanel.name == gp_name,
                        gene.Genepanel.version == gp_version
                    ).one()
                    genepanel_cache[(gp_name, gp_version)] = gp_obj
                else:
                    gp_obj = genepanel_cache[(gp_name, gp_version)]

                allele_obj = next((a for a in allele_cache if a.id == allele_id))
                final_allele = adl.from_objs(
                    [allele_obj],
                    genepanel=gp_obj,
                    include_annotation=True,
                    include_custom_annotation=False,
                    include_allele_assessment=False,
                    include_reference_assessments=False
                )
                user_in_result['alleles'].append(final_allele[0])

        return result
