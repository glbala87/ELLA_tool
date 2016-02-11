from . import resources as r


class ApiV1(object):

    def init_app(self, api):

        api.add_resource(r.acmg.ACMGClassificationResource,
                         '/api/v1/acmg/alleles/')

        api.add_resource(r.alleleassessment.AlleleAssessmentResource,
                         '/api/v1/alleleassessments/<int:aa_id>/')

        api.add_resource(r.alleleassessment.AlleleAssessmentListResource,
                         '/api/v1/alleleassessments/')

        api.add_resource(r.allele.AlleleListResource,
                         '/api/v1/alleles/')

        api.add_resource(r.analysis.AnalysisListResource,
                         '/api/v1/analyses/')

        api.add_resource(r.config.ConfigResource,
                         '/api/v1/config/')

        api.add_resource(r.customannotation.CustomAnnotationList,
                         '/api/v1/customannotations/')

        api.add_resource(r.interpretation.InterpretationResource,
                         '/api/v1/interpretations/<int:interpretation_id>/')

        api.add_resource(r.interpretation.InterpretationReferenceAssessmentResource,
                         '/api/v1/interpretations/<int:interpretation_id>/referenceassessments/')

        api.add_resource(r.interpretation.InterpretationActionStartResource,
                         '/api/v1/interpretations/<int:interpretation_id>/actions/start/')

        api.add_resource(r.interpretation.InterpretationActionCompleteResource,
                         '/api/v1/interpretations/<int:interpretation_id>/actions/complete/')

        api.add_resource(r.interpretation.InterpretationActionFinalizeResource,
                         '/api/v1/interpretations/<int:interpretation_id>/actions/finalize/')

        api.add_resource(r.interpretation.InterpretationActionOverrideResource,
                         '/api/v1/interpretations/<int:interpretation_id>/actions/override/')

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

        return api
