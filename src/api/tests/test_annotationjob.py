import subprocess

import pytest
from sqlalchemy import tuple_

from api.polling import AnnotationJobsInterface
from vardb.datamodel import allele, annotationjob, genotype, sample
from vardb.deposit.importers import AlleleImporter

ANNOTATION_JOBS_PATH = "/api/v1/import/service/jobs/"

TESTDATA_DIR = "/ella/ella-testdata/testdata"

ANALYSIS = "brca_sample_3"
GENEPANEL_NAME = "HBOCUTV"
GENEPANEL_VERSION = "v1.0.0"


@pytest.fixture(scope="session")
def unannotated_vcf():
    return "\n".join(
        [
            "##fileformat=VCFv4.1",
            "##contig=<ID=13>",
            "#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	brca_sample_3",
            "13	32899256	CD101423	GA	G	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917",
            "13	32900236	CS1213347	A	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917",
            "13	32900261	CM065022	A	G	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917",
            "13	32900280	CD031824	TAA	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917",
            "13	32900290	CS994297	A	G	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917",
            "13	32972760	CD101423	G	A	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917",
        ]
    )


@pytest.fixture(scope="session")
def annotated_vcf():
    filename = "{}.{}_{}.vcf.gz".format(ANALYSIS, GENEPANEL_NAME, GENEPANEL_VERSION)
    full_path = subprocess.check_output(
        "find %s -type f -name %s" % (TESTDATA_DIR, filename), shell=True
    ).strip()
    import gzip

    with gzip.open(full_path, "rt") as f:
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

    variants1 = variants[: len(variants) // 2]
    variants2 = variants[len(variants) // 2 :]

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
    id = response.get_json()["id"]

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
    id = response.get_json()["id"]

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
    from io import StringIO

    from vardb.util.vcfiterator import VcfIterator

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


def get_allele_keys(vcf):
    keys = []
    for l in vcf.split("\n"):
        if not l or l.startswith("#"):
            continue
        else:
            chrom, pos, _, ref, alt = l.split("\t")[:5]
            keys.append((chrom, pos, ref, alt))

    return keys


def test_deposit_independent_variants(test_database, session, client, annotated_vcf):
    test_database.refresh()
    alleles = get_allele_keys(annotated_vcf)

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
    id = response.get_json()["id"]

    # Annotation job deposit
    annotationjob_interface = AnnotationJobsInterface(session)
    annotationjob_interface.deposit(id, annotated_vcf)
    session.commit()

    # Check that annotation job is deposited
    deposited_alleles_count = (
        session.query(allele.Allele)
        .filter(
            tuple_(
                allele.Allele.chromosome,
                allele.Allele.vcf_pos,
                allele.Allele.vcf_ref,
                allele.Allele.vcf_alt,
            ).in_(alleles)
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
    id = response.get_json()["id"]

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
    id = response.get_json()["id"]

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
