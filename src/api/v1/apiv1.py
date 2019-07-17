from . import resources as r
from .docs import ApiV1Docs
from api import schemas


class ApiV1(object):
    def __init__(self, app, api):
        self.app = app
        self.api = api
        self.api_v1_docs = ApiV1Docs(app, api)

    def _add_schemas(self):
        """
        Loads our marshmallow schemas into docs.
        """
        self.api_v1_docs.add_schema("Analysis", schemas.AnalysisSchema())
        self.api_v1_docs.add_schema(
            "AnalysisInterpretation", schemas.AnalysisInterpretationSchema()
        )
        self.api_v1_docs.add_schema("AlleleInterpretation", schemas.AlleleInterpretationSchema())
        self.api_v1_docs.add_schema("Interpretation", schemas.AnalysisInterpretationSchema())
        self.api_v1_docs.add_schema("Allele", schemas.AlleleSchema())
        self.api_v1_docs.add_schema("Reference", schemas.ReferenceSchema())
        self.api_v1_docs.add_schema("ReferenceAssessment", schemas.ReferenceAssessmentSchema())
        self.api_v1_docs.add_schema("AlleleAssessment", schemas.AlleleAssessmentSchema())
        self.api_v1_docs.add_schema("AlleleAssessmentInput", schemas.AlleleAssessmentInputSchema())
        self.api_v1_docs.add_schema("AlleleReport", schemas.AlleleReportSchema())
        self.api_v1_docs.add_schema("User", schemas.UserSchema())
        self.api_v1_docs.add_schema("Classification", schemas.ClassificationSchema())
        self.api_v1_docs.add_schema("Rule", schemas.RuleSchema())
        self.api_v1_docs.add_schema("Genepanel", schemas.GenepanelFullSchema())
        self.api_v1_docs.add_schema("Annotation", schemas.AnnotationSchema())
        self.api_v1_docs.add_schema("CustomAnnotation", schemas.CustomAnnotationSchema())
        self.api_v1_docs.add_schema("Genotype", schemas.GenotypeSchema())

    def _add_resource(self, resource, *paths):
        """
        Add resource to both restful api and to docs.
        """
        self.api.add_resource(resource, *paths)
        self.api_v1_docs.add_resource(paths[0], resource)

    def setup_api(self):

        # Expose swagger UI at /api/v1/docs
        # and expose the api spec at /api/v1/specs/
        self.api_v1_docs.init_api_docs("/api/v1/docs", "/api/v1/specs/")

        self._add_schemas()

        # ---------------------------------------------------------------------------------------------------------
        # Rule engine
        # ---------------------------------------------------------------------------------------------------------

        self._add_resource(r.acmg.ACMGAlleleResource, "/api/v1/acmg/alleles/")

        self._add_resource(r.acmg.ACMGClassificationResource, "/api/v1/acmg/classifications/")

        # ---------------------------------------------------------------------------------------------------------
        # Entities
        # ---------------------------------------------------------------------------------------------------------

        self._add_resource(r.allele.AlleleListResource, "/api/v1/alleles/")

        self._add_resource(r.allele.AlleleByGeneListResource, "/api/v1/alleles/by-gene/")

        self._add_resource(
            r.allele.AlleleAnalysisListResource, "/api/v1/alleles/<int:allele_id>/analyses/"
        )

        self._add_resource(
            r.alleleassessment.AlleleAssessmentResource, "/api/v1/alleleassessments/<int:aa_id>/"
        )

        self._add_resource(
            r.alleleassessment.AlleleAssessmentListResource, "/api/v1/alleleassessments/"
        )

        self._add_resource(r.allelereport.AlleleReportListResource, "/api/v1/allelereports/")

        self._add_resource(
            r.allelereport.AlleleReportResource, "/api/v1/allelereports/<int:ar_id>/"
        )

        # self._add_resource(r.allele.AlleleGenepanelListResource,
        #                   '/api/v1/alleles/<int:allele_id>/genepanels/')

        self._add_resource(r.analysis.AnalysisListResource, "/api/v1/analyses/")

        self._add_resource(r.analysis.AnalysisResource, "/api/v1/analyses/<int:analysis_id>/")

        self._add_resource(r.broadcast.BroadcastResource, "/api/v1/broadcasts/")

        self._add_resource(r.customannotation.CustomAnnotationList, "/api/v1/customannotations/")

        self._add_resource(r.config.ConfigResource, "/api/v1/config/")

        self._add_resource(
            r.filterconfig.FilterconfigResource, "/api/v1/filterconfigs/<int:filterconfig_id>"
        )

        self._add_resource(r.genepanel.GenepanelListResource, "/api/v1/genepanels/")

        self._add_resource(r.genepanel.GenepanelResource, "/api/v1/genepanels/<name>/<version>/")

        self._add_resource(r.reference.ReferenceListResource, "/api/v1/references/")

        self._add_resource(
            r.referenceassessment.ReferenceAssessmentResource,
            "/api/v1/referenceassessments/<int:ra_id>/",
        )

        self._add_resource(
            r.referenceassessment.ReferenceAssessmentListResource, "/api/v1/referenceassessments/"
        )

        self._add_resource(r.search.SearchResource, "/api/v1/search/")

        self._add_resource(r.search.SearchOptionsResource, "/api/v1/search/options/")

        self._add_resource(r.user.UserListResource, "/api/v1/users/")

        self._add_resource(r.user.UserResource, "/api/v1/users/<int:user_id>/")

        # ---------------------------------------------------------------------------------------------------------
        # Overview
        # ---------------------------------------------------------------------------------------------------------

        self._add_resource(r.overview.OverviewAlleleResource, "/api/v1/overviews/alleles/")

        self._add_resource(
            r.overview.OverviewAlleleFinalizedResource, "/api/v1/overviews/alleles/finalized/"
        )

        self._add_resource(r.overview.OverviewAnalysisResource, "/api/v1/overviews/analyses/")

        self._add_resource(
            r.overview.OverviewAnalysisFinalizedResource, "/api/v1/overviews/analyses/finalized/"
        )

        self._add_resource(
            r.overview.OverviewAnalysisByFindingsResource, "/api/v1/overviews/analyses/by-findings/"
        )

        self._add_resource(r.overview.OverviewUserStatsResource, "/api/v1/overviews/userstats/")

        # ---------------------------------------------------------------------------------------------------------
        # Annotation
        # ---------------------------------------------------------------------------------------------------------
        self._add_resource(r.annotationjob.AnnotationJob, "/api/v1/import/service/jobs/<int:id>/")

        self._add_resource(r.annotationjob.AnnotationJobList, "/api/v1/import/service/jobs/")

        self._add_resource(
            r.annotationjob.AnnotationServiceRunning, "/api/v1/import/service/running/"
        )

        self._add_resource(r.annotationjob.ImportSamples, "/api/v1/import/service/samples/")

        # ---------------------------------------------------------------------------------------------------------
        # Workflow variant
        # ---------------------------------------------------------------------------------------------------------
        self._add_resource(
            r.workflow.allele.AlleleGenepanelResource,
            "/api/v1/workflows/alleles/<int:allele_id>/genepanels/<gp_name>/<gp_version>/",
        )

        self._add_resource(
            r.workflow.allele.AlleleGenepanelsListResource,
            "/api/v1/workflows/alleles/<int:allele_id>/genepanels/",
        )

        self._add_resource(
            r.workflow.allele.AlleleInterpretationListResource,
            "/api/v1/workflows/alleles/<int:allele_id>/interpretations/",
        )

        self._add_resource(
            r.workflow.allele.AlleleInterpretationResource,
            "/api/v1/workflows/alleles/<int:allele_id>/interpretations/<int:interpretation_id>/",
        )

        self._add_resource(
            r.workflow.allele.AlleleInterpretationAllelesListResource,
            "/api/v1/workflows/alleles/<int:allele_id>/interpretations/<int:interpretation_id>/alleles/",
        )

        self._add_resource(
            r.workflow.allele.AlleleActionStartResource,
            "/api/v1/workflows/alleles/<int:allele_id>/actions/start/",
        )

        self._add_resource(
            r.workflow.allele.AlleleActionMarkInterpretationResource,
            "/api/v1/workflows/alleles/<int:allele_id>/actions/markinterpretation/",
        )

        self._add_resource(
            r.workflow.allele.AlleleActionMarkReviewResource,
            "/api/v1/workflows/alleles/<int:allele_id>/actions/markreview/",
        )

        self._add_resource(
            r.workflow.allele.AlleleActionFinalizeResource,
            "/api/v1/workflows/alleles/<int:allele_id>/actions/finalize/",
            "/api/v1/workflows/alleles/<int:allele_id>/snapshots/",
        )

        self._add_resource(
            r.workflow.allele.AlleleActionOverrideResource,
            "/api/v1/workflows/alleles/<int:allele_id>/actions/override/",
        )

        self._add_resource(
            r.workflow.allele.AlleleActionReopenResource,
            "/api/v1/workflows/alleles/<int:allele_id>/actions/reopen/",
        )

        self._add_resource(
            r.workflow.allele.AlleleCollisionResource,
            "/api/v1/workflows/alleles/<int:allele_id>/collisions/",
        )

        self._add_resource(
            r.workflow.allele.AlleleInterpretationLogListResource,
            "/api/v1/workflows/alleles/<int:allele_id>/logs/",
        )

        self._add_resource(
            r.workflow.allele.AlleleInterpretationLogResource,
            "/api/v1/workflows/alleles/<int:allele_id>/logs/<int:log_id>/",
        )

        # ---------------------------------------------------------------------------------------------------------
        # Workflow analysis
        # ---------------------------------------------------------------------------------------------------------

        self._add_resource(
            r.workflow.analysis.AnalysisStatsResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/stats/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisInterpretationListResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/interpretations/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisGenepanelResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/genepanels/<gp_name>/<gp_version>/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisInterpretationResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/interpretations/<int:interpretation_id>/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisInterpretationFinishAllowedResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/interpretations/<int:interpretation_id>/finishallowed",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisInterpretationFilteredAlleles,
            "/api/v1/workflows/analyses/<int:analysis_id>/interpretations/<int:interpretation_id>/filteredalleles/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisInterpretationAllelesListResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/interpretations/<int:interpretation_id>/alleles/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisActionStartResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/actions/start/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisActionMarkNotReadyResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/actions/marknotready/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisActionMarkInterpretationResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/actions/markinterpretation/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisActionMarkReviewResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/actions/markreview/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisActionMarkMedicalReviewResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/actions/markmedicalreview/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisActionFinalizeResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/actions/finalize/",
            "/api/v1/workflows/analyses/<int:analysis_id>/snapshots/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisActionOverrideResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/actions/override/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisActionReopenResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/actions/reopen/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisCollisionResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/collisions/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisInterpretationLogListResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/logs/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisInterpretationLogResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/logs/<int:log_id>/",
        )

        self._add_resource(
            r.workflow.analysis.AnalysisFilterConfigResource,
            "/api/v1/workflows/analyses/<int:analysis_id>/filterconfigs/",
        )

        # ---------------------------------------------------------------------------------------------------------
        # Security
        # ---------------------------------------------------------------------------------------------------------

        self._add_resource(r.user.LoginResource, "/api/v1/users/actions/login/")

        self._add_resource(r.user.LogoutResource, "/api/v1/users/actions/logout/")

        self._add_resource(r.user.ChangePasswordResource, "/api/v1/users/actions/changepassword/")

        self._add_resource(r.user.CurrentUser, "/api/v1/users/currentuser/")

        self._add_resource(
            r.attachment.AttachmentResource,
            "/api/v1/attachments/upload/",
            "/api/v1/attachments/<int:attachment_id>",
        )

        self._add_resource(r.attachment.AttachmentListResource, "/api/v1/attachments/")

        # ---------------------------------------------------------------------------------------------------------
        # Reports
        # ---------------------------------------------------------------------------------------------------------

        self._add_resource(
            r.report.NonStartedAnalysesVariants, "/api/v1/reports/non-started-analyses-variants/"
        )

        self._add_resource(r.report.Diff, "/api/v1/reports/diff/")

        # ---------------------------------------------------------------------------------------------------------
        # IGV
        # ---------------------------------------------------------------------------------------------------------

        self._add_resource(r.igv.IgvResource, "/api/v1/igv/<filename>")

        self._add_resource(r.igv.IgvSearchResource, "/api/v1/igv/search/")

        self._add_resource(
            r.igv.GenepanelBedResource, "/api/v1/igv/genepanel/<gp_name>/<gp_version>/"
        )

        self._add_resource(r.igv.ClassificationResource, "/api/v1/igv/classifications/")

        self._add_resource(r.igv.AnalysisVariantTrack, "/api/v1/igv/variants/<int:analysis_id>/")

        self._add_resource(r.igv.AnalysisTrackList, "/api/v1/igv/tracks/<int:analysis_id>/")

        self._add_resource(r.igv.GlobalTrack, "/api/v1/igv/tracks/global/<filename>")

        self._add_resource(
            r.igv.UserGroupTrack, "/api/v1/igv/tracks/usergroups/<int:usergroup_id>/<filename>"
        )

        self._add_resource(
            r.igv.AnalysisTrack, "/api/v1/igv/tracks/analyses/<int:analysis_id>/<filename>"
        )
