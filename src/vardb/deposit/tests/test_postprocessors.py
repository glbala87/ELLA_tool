from vardb.deposit import postprocessors
from vardb.datamodel import allele, sample, genotype, workflow, assessment


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

        # Create alleleassesments for all alleles in database
        allele_ids = session.query(allele.Allele.id).all()

        for allele_id in allele_ids:
            aa = assessment.AlleleAssessment(
                allele_id=allele_id,
                genepanel_name="HBOC",
                genepanel_version="v01",
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
