import json
import os
import pytest
import subprocess

from sqlalchemy import tuple_
import vardb
from api.polling import AnnotationJobsInterface
from vardb.datamodel import sample, annotationjob, allele, genotype
from vardb.deposit.importers import AlleleImporter

ANNOTATION_JOBS_PATH = "/api/v1/import/service/jobs/"

TESTDATA_DIR = os.path.join(os.path.split(vardb.__file__)[0], "testdata")
assert os.path.isdir(TESTDATA_DIR)

ANALYSIS = "brca_sample_3"
GENEPANEL_NAME = "HBOCUTV"
GENEPANEL_VERSION = "v01"


@pytest.fixture(scope="session")
def unannotated_vcf():
    filename = ANALYSIS + ".vcf"
    full_path = subprocess.check_output(
        "find %s -type f -name %s" % (TESTDATA_DIR, filename), shell=True
    ).strip()
    with open(full_path, "r") as f:
        vcf = f.read()

    return vcf


@pytest.fixture(scope="session")
def annotated_vcf():
    filename = "{}.{}_{}.vcf".format(ANALYSIS, GENEPANEL_NAME, GENEPANEL_VERSION)
    full_path = subprocess.check_output(
        "find %s -type f -name %s" % (TESTDATA_DIR, filename), shell=True
    ).strip()
    with open(full_path, "r") as f:
        vcf = f.read()
    return vcf


def split_vcf(vcf):
    lines = vcf.split("\n")
    header = []
    iter_lines = iter(lines)
    for l in iter_lines:
        header.append(l)
        if l.startswith("#CHROM"):
            break
    header = "\n".join(header)

    variants = []
    for l in iter_lines:
        if l.strip():
            variants.append(l)

    variants1 = variants[: len(variants) / 2]
    variants2 = variants[len(variants) / 2 :]

    N1 = len(variants1)
    N2 = len(variants2)
    first = header + "\n" + "\n".join(variants1)
    second = header + "\n" + "\n".join(variants2)

    return first, second, N1, N2


@pytest.fixture
def split_annotated_vcf(annotated_vcf):
    return split_vcf(annotated_vcf)


def test_submit_annotationjob(session, client):
    "Submit annotation job"
    data = {
        "mode": "Analysis",
        "user_id": 1,
        "data": "Dummy vcf data",
        "genepanel_name": GENEPANEL_NAME,
        "genepanel_version": GENEPANEL_VERSION,
        "properties": {"analysis_name": "abc", "create_or_append": "Create", "sample_type": "HTS"},
    }

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200

    annotation_jobs = session.query(annotationjob.AnnotationJob).all()
    assert len(annotation_jobs) == 1

    annotation_job = annotation_jobs[0]
    assert annotation_job.status == "SUBMITTED"
    assert annotation_job.data == data["data"]
    assert annotation_job.mode == "Analysis"
    assert annotation_job.genepanel_name == GENEPANEL_NAME
    assert annotation_job.genepanel_version == GENEPANEL_VERSION
    assert annotation_job.status_history == {}
    assert annotation_job.user_id == 1
    assert annotation_job.task_id == ""
    assert annotation_job.properties["analysis_name"] == data["properties"]["analysis_name"]
    assert annotation_job.properties["create_or_append"] == data["properties"]["create_or_append"]


def test_deposit_annotationjob(session, client, unannotated_vcf, annotated_vcf):
    data = {
        "mode": "Analysis",
        "status": "ANNOTATED",
        "task_id": "123456789",
        "user_id": 1,
        "data": unannotated_vcf,
        "genepanel_name": GENEPANEL_NAME,
        "genepanel_version": GENEPANEL_VERSION,
        "properties": {"analysis_name": "abc", "create_or_append": "Create", "sample_type": "HTS"},
    }

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    # Annotation job deposit
    annotationjob_interface = AnnotationJobsInterface(session)
    annotationjob_interface.deposit(id, annotated_vcf)
    session.commit()

    # Check that annotation job is deposited
    analyses = (
        session.query(sample.Analysis)
        .filter(
            sample.Analysis.name
            == "{}.{}_{}".format(
                data["properties"]["analysis_name"],
                data["genepanel_name"],
                data["genepanel_version"],
            )
        )
        .all()
    )

    assert len(analyses) == 1


def test_status_update_annotationjob(session, client):
    # Submit annotation job
    data = {
        "mode": "Analysis",
        "user_id": 1,
        "data": "Dummy vcf data",
        "genepanel_name": GENEPANEL_NAME,
        "genepanel_version": GENEPANEL_VERSION,
        "properties": {"analysis_name": "abc", "create_or_append": "Create", "sample_type": "HTS"},
    }

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    update_data = {"status": "ANNOTATED", "message": "Message from server", "task_id": "123456789"}

    annotationjob_interface = AnnotationJobsInterface(session)
    annotationjob_interface.patch(id, **update_data)

    annotation_jobs = (
        session.query(annotationjob.AnnotationJob)
        .filter(annotationjob.AnnotationJob.id == id)
        .all()
    )

    assert len(annotation_jobs) == 1
    annotation_job = annotation_jobs[0]

    assert annotation_job.message == update_data["message"]
    assert annotation_job.status == update_data["status"]
    assert annotation_job.task_id == update_data["task_id"]
    assert len(annotation_job.status_history) == 1


def get_alleles(vcf, session):
    from vardb.util.vcfiterator import VcfIterator

    from StringIO import StringIO

    fd = StringIO()
    fd.write(vcf)
    fd.flush()
    fd.seek(0)

    vcfiterator = VcfIterator(fd)
    allele_importer = AlleleImporter(session)
    alleles = []
    for a in vcfiterator.iter():
        allele_importer.add(a)
    alleles = allele_importer.process()
    session.rollback()
    fd.close()
    return alleles


def test_deposit_independent_variants(test_database, session, client, annotated_vcf):
    test_database.refresh()
    alleles = get_alleles(annotated_vcf, session)

    data = {
        "mode": "Variants",
        "status": "ANNOTATED",
        "task_id": "123456789",
        "user_id": 1,
        "data": annotated_vcf,
        "genepanel_name": GENEPANEL_NAME,
        "genepanel_version": GENEPANEL_VERSION,
        "properties": {"sample_type": "Sanger"},
    }

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    # Annotation job deposit
    annotationjob_interface = AnnotationJobsInterface(session)
    annotationjob_interface.deposit(id, annotated_vcf)
    session.commit()

    # Check that annotation job is deposited
    deposited_allele_values = list()
    for al in alleles:
        deposited_allele_values.append(
            (
                al["chromosome"],
                al["start_position"],
                al["open_end_position"],
                al["change_from"],
                al["change_to"],
                al["change_type"],
            )
        )

    deposited_alleles_count = (
        session.query(allele.Allele)
        .filter(
            tuple_(
                allele.Allele.chromosome,
                allele.Allele.start_position,
                allele.Allele.open_end_position,
                allele.Allele.change_from,
                allele.Allele.change_to,
                allele.Allele.change_type,
            ).in_(deposited_allele_values)
        )
        .count()
    )

    assert len(alleles) == deposited_alleles_count


def test_append_to_analysis(test_database, session, client, annotated_vcf):
    test_database.refresh()

    # Split vcf in two, to be submitted first as new analysis,
    # then to append to the newly created analysis
    first_vcf, second_vcf, N1, N2 = split_vcf(annotated_vcf)

    # Create a new analysis
    data1 = {
        "mode": "Analysis",
        "user_id": 1,
        "data": first_vcf,
        "genepanel_name": GENEPANEL_NAME,
        "genepanel_version": GENEPANEL_VERSION,
        "properties": {"analysis_name": "abc", "create_or_append": "Create", "sample_type": "HTS"},
    }

    response = client.post(ANNOTATION_JOBS_PATH, data=data1)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    # Annotation job deposit
    annotationjob_interface = AnnotationJobsInterface(session)
    annotationjob_interface.deposit(id, first_vcf)
    session.commit()

    # Check that annotation job is deposited
    analysis_name = "{}.{}_{}".format(
        data1["properties"]["analysis_name"], data1["genepanel_name"], data1["genepanel_version"]
    )
    analyses = session.query(sample.Analysis).filter(sample.Analysis.name == analysis_name).all()

    assert len(analyses) == 1
    analysis_id = analyses[0].id
    genotypes = (
        session.query(genotype.Genotype)
        .join(sample.Sample)
        .filter(sample.Sample.analysis_id == analysis_id)
        .all()
    )
    assert len(genotypes) == N1

    # Create new annotation job, to append to newly created analysis
    data2 = {
        "mode": "Analysis",
        "user_id": 1,
        "data": second_vcf,
        "genepanel_name": GENEPANEL_NAME,
        "genepanel_version": GENEPANEL_VERSION,
        "properties": {
            "analysis_name": analysis_name,
            "create_or_append": "Append",
            "sample_type": "HTS",
        },
    }

    response = client.post(ANNOTATION_JOBS_PATH, data=data2)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    # Annotation job deposit
    annotationjob_interface = AnnotationJobsInterface(session)
    annotationjob_interface.deposit(id, second_vcf)
    session.commit()

    # Check that the new alleles were added to analysis
    genotypes = (
        session.query(genotype.Genotype)
        .join(sample.Sample)
        .filter(sample.Sample.analysis_id == analysis_id)
        .all()
    )

    assert len(genotypes) == N1 + N2
