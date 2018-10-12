import pytest
import os
from sqlalchemy import tuple_
from vardb.datamodel import sample, assessment, gene, user

TESTDATA = os.environ["TESTDATA"]
VCF = os.path.join(TESTDATA, "analyses/default/brca_sample_3.HBOCUTV_v01/brca_sample_3.HBOCUTV_v01.vcf")


def test_deposit_analysis(session, run_command):
    assert session.query(
        sample.Analysis
    ).filter(
        sample.Analysis.name == os.path.splitext(os.path.basename(VCF))[0]
    ).count() == 0

    result = run_command(["deposit", "analysis", VCF])
    assert result.exit_code == 0

    session.query(
        sample.Analysis
    ).filter(
        sample.Analysis.name == os.path.splitext(os.path.basename(VCF))[0]
    ).one()


def test_deposit_alleles(session, run_command):
    result = run_command(["deposit", "alleles", VCF])
    assert result.exit_code == 0


def test_deposit_annotation(session, run_command):
    result = run_command(["deposit", "annotation", VCF])
    assert result.exit_code == 0


def test_deposit_references(session, run_command):
    run_command(["database", "drop", "-f"])
    run_command(["database", "make", "-f"])

    assert session.query(assessment.Reference).count() == 0
    references = os.path.join(TESTDATA, "references_test.json")
    result = run_command(["deposit", "references", references])
    assert result.exit_code == 0
    assert session.query(assessment.Reference).count() == len(open(references, 'r').readlines())


def test_deposit_genepanel(session, run_command):
    run_command(["database", "drop", "-f"])
    run_command(["database", "make", "-f"])

    genepanel_name = "Ciliopati"
    genepanel_version = "v05"

    assert session.query(
        gene.Genepanel
    ).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version) == (genepanel_name, genepanel_version)
    ).count() == 0

    genepanel_folder = os.path.join(TESTDATA, "clinicalGenePanels/{}_{}".format(genepanel_name, genepanel_version))
    result = run_command(["deposit", "genepanel", "--folder", genepanel_folder])
    assert result.exit_code == 0
    session.query(
        gene.Genepanel
    ).filter(
        tuple_(gene.Genepanel.name, gene.Genepanel.version) == (genepanel_name, genepanel_version)
    ).one()


def test_append_genepanel_to_usergroup(session, test_database, run_command):
    test_database.refresh()
    genepanel_name = "Ciliopati"
    genepanel_version = "v05"
    usergroup = "testgroup01"

    ug = session.query(
        user.UserGroup
    ).filter(
        user.UserGroup.name == usergroup
    )
    assert (genepanel_name, genepanel_version) not in [(gp.name, gp.version) for gp in ug.one().genepanels]

    result = run_command(["deposit", "append_genepanel_to_usergroup", genepanel_name, genepanel_version, usergroup])
    assert result.exit_code == 0

    assert (genepanel_name, genepanel_version) in [(gp.name, gp.version) for gp in ug.one().genepanels]

