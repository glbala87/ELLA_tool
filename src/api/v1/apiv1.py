from . import resources as r


class ApiV1(object):

    def init_app(self, api):

        api.add_resource(r.acmg.ACMGAlleleResource,
                         '/api/v1/acmg/alleles/')

        api.add_resource(r.acmg.ACMGClassificationResource,
                         '/api/v1/acmg/classifications/')

        api.add_resource(r.alleleassessment.AlleleAssessmentResource,
                         '/api/v1/alleleassessments/<int:aa_id>/')

        api.add_resource(r.alleleassessment.AlleleAssessmentListResource,
                         '/api/v1/alleleassessments/')

        api.add_resource(r.allele.AlleleListResource,
                         '/api/v1/alleles/',
                         '/api/v1/alleles/<list:allele_ids>')

        api.add_resource(r.allele.AlleleGenepanelListResource,
                         '/api/v1/alleles/<int:allele_id>/genepanels/')

        api.add_resource(r.analysis.AnalysisListResource,
                         '/api/v1/analyses/')

        api.add_resource(r.analysis.AnalysisResource,
                         '/api/v1/analyses/<int:analysis_id>/')

        api.add_resource(r.analysis.AnalysisActionStartResource,
                         '/api/v1/analyses/<int:analysis_id>/actions/start/')

        api.add_resource(r.analysis.AnalysisActionMarkReviewResource,
                         '/api/v1/analyses/<int:analysis_id>/actions/markreview/')

        api.add_resource(r.analysis.AnalysisActionFinalizeResource,
                         '/api/v1/analyses/<int:analysis_id>/actions/finalize/')

        api.add_resource(r.analysis.AnalysisActionOverrideResource,
                         '/api/v1/analyses/<int:analysis_id>/actions/override/')

        api.add_resource(r.analysis.AnalysisActionReopenResource,
                         '/api/v1/analyses/<int:analysis_id>/actions/reopen/')

        api.add_resource(r.config.ConfigResource,
                         '/api/v1/config/')

        api.add_resource(r.customannotation.CustomAnnotationList,
                         '/api/v1/customannotations/')

        api.add_resource(r.interpretation.InterpretationResource,
                         '/api/v1/interpretations/<int:interpretation_id>/')

        api.add_resource(r.reference.ReferenceListResource,
                         '/api/v1/references/')

        api.add_resource(r.referenceassessment.ReferenceAssessmentResource,
                         '/api/v1/referenceassessments/<int:ra_id>/')

        api.add_resource(r.referenceassessment.ReferenceAssessmentListResource,
                         '/api/v1/referenceassessments/')

        api.add_resource(r.search.SearchResource,
                         '/api/v1/search/')

        api.add_resource(r.user.UserListResource,
                         '/api/v1/users/')

        api.add_resource(r.user.UserResource,
                         '/api/v1/users/<int:user_id>/')

        api.add_resource(r.genepanel.GenepanelResource,
                         '/api/v1/genepanels/<name>/<version>')

        return api
