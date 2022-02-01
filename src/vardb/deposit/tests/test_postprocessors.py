from vardb.deposit import postprocessors
from vardb.datamodel import allele, sample, genotype, workflow, assessment
from api.v1.resources.workflow import helpers


class TestPostprocessors:
    def test_prepare_data(self, test_database):
        test_database.refresh()

    def test_analysis_not_ready_warnings(self, session):

        # Use analysis id 1
        analysis = session.query(sample.Analysis).filter(sample.Analysis.id == 1).one()

        # First, fudge the data to ensure that we pass all tests
        analysis.warnings = ""

        alleles = (
            session.query(allele.Allele)
            .join(genotype.Genotype.alleles, sample.Sample)
            .filter(sample.Analysis.id == analysis.id)
        )
        for al in alleles:
            al.change_type = "SNP"

        gsds = (
            session.query(genotype.GenotypeSampleData)
            .join(genotype.Genotype, sample.Sample)
            .filter(sample.Analysis.id == analysis.id)
        ).all()

        for gsd in gsds:
            gsd.type = "Reference"
            gsd.sequencing_depth = 1000
            gsd.genotype.sequencing_depth = 1000
            gsd.genotype.variant_quality = 1000
            gsd.genotype.filter_status = "PASS"

        interpretation = (
            session.query(workflow.AnalysisInterpretation)
            .filter(workflow.AnalysisInterpretation.analysis_id == analysis.id)
            .one()
        )

        filter_config_id = 1

        assert interpretation.workflow_status == "Interpretation"
        postprocessors.analysis_not_ready_warnings(
            session, analysis, interpretation, filter_config_id
        )
        assert interpretation.workflow_status == "Interpretation"

        # Change analysis warnings so it changes status
        analysis.warnings = "WARNING!"
        postprocessors.analysis_not_ready_warnings(
            session, analysis, interpretation, filter_config_id
        )
        assert interpretation.workflow_status == "Not ready"

        # Make sure we're back to normal
        analysis.warnings = ""
        interpretation.workflow_status = "Interpretation"
        postprocessors.analysis_not_ready_warnings(
            session, analysis, interpretation, filter_config_id
        )
        assert interpretation.workflow_status == "Interpretation"

        # Change another parameter so needs_verification is set to True
        for gsd in gsds:
            gsd.genotype.filter_status = "FAIL"

        postprocessors.analysis_not_ready_warnings(
            session, analysis, interpretation, filter_config_id
        )
        assert interpretation.workflow_status == "Not ready"

    def test_analysis_finalize_without_findings(self, session):

        # Use analysis id 2

        # First test that it's not finalized
        analysis = session.query(sample.Analysis).filter(sample.Analysis.id == 2).one()

        interpretation = (
            session.query(workflow.AnalysisInterpretation)
            .filter(workflow.AnalysisInterpretation.analysis_id == analysis.id)
            .one()
        )

        analysis.warnings = "WARNING"

        filter_config_id = 1
        postprocessors.analysis_finalize_without_findings(
            session, analysis, interpretation, filter_config_id
        )

        assert interpretation.finalized is None

        # Create alleleassesments for all non-filtered alleles
        allele_ids, _ = helpers.get_filtered_alleles(session, interpretation, filter_config_id)

        for allele_id in allele_ids:
            aa = assessment.AlleleAssessment(
                allele_id=allele_id,
                genepanel_name="HBOC",
                genepanel_version="v01.0",
                classification="1",
                user_id=1,
                usergroup_id=1,
            )
            session.add(aa)

        session.flush()

        # Check again (should still not do anything due to analysis.warning)
        postprocessors.analysis_finalize_without_findings(
            session, analysis, interpretation, filter_config_id
        )
        assert interpretation.finalized is None

        # Then make sure it should finalize
        analysis.warnings = ""
        postprocessors.analysis_finalize_without_findings(
            session, analysis, interpretation, filter_config_id
        )
        assert interpretation.finalized is True

    def test_analysis_tag_all_classified(self, session, test_database):

        test_database.refresh()

        # Use analysis id 2
        analysis = session.query(sample.Analysis).filter(sample.Analysis.id == 2).one()

        interpretation = (
            session.query(workflow.AnalysisInterpretation)
            .filter(workflow.AnalysisInterpretation.analysis_id == analysis.id)
            .one()
        )

        filter_config_id = 1
        allele_ids, _ = helpers.get_filtered_alleles(session, interpretation, filter_config_id)
        assert allele_ids
        #
        # Test ALL CLASSIFIED
        #
        for allele_id in allele_ids:
            aa = assessment.AlleleAssessment(
                allele_id=allele_id,
                genepanel_name="HBOC",
                genepanel_version="v01.0",
                classification="5",
                user_id=1,
                usergroup_id=1,
            )
            session.add(aa)

        session.flush()

        # Clear out any existing data
        session.execute("DELETE FROM interpretationlog")

        postprocessors.analysis_tag_all_classified(
            session, analysis, interpretation, filter_config_id
        )
        # Check that overview comment is added correctly
        il = (
            session.query(workflow.InterpretationLog)
            .filter(workflow.InterpretationLog.analysisinterpretation_id == interpretation.id)
            .one()
        )
        assert il.analysisinterpretation_id == interpretation.id
        assert il.review_comment == "ALL CLASSIFIED"
        session.delete(il)
        session.flush()

        #
        # Test NO VARIANTS
        #

        # Delete all non-filtered variants from analysis
        to_delete_allele_ids = ",".join([str(a) for a in allele_ids])
        session.execute(f"DELETE FROM genotype WHERE allele_id IN ({to_delete_allele_ids})")
        postprocessors.analysis_tag_all_classified(
            session, analysis, interpretation, filter_config_id
        )
        # Check that overview comment is added correctly
        il = (
            session.query(workflow.InterpretationLog)
            .filter(workflow.InterpretationLog.analysisinterpretation_id == interpretation.id)
            .one()
        )
        assert il.analysisinterpretation_id == interpretation.id
        assert il.review_comment == "NO VARIANTS"
