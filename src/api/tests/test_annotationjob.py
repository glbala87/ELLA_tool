from flask import Flask, request, render_template, session, flash, redirect, \
    url_for, jsonify, Response

import pytest
import os
import subprocess
import json

from vardb.datamodel import sample, allele, genotype
from vardb.deposit.importers import AlleleImporter

from api.polling import ANNOTATION_JOBS_PATH, ANNOTATION_SERVICE_ANNOTATE_PATH, ANNOTATION_SERVICE_STATUS_PATH, \
    ANNOTATION_SERVICE_PROCESS_PATH, DEPOSIT_SERVICE_PATH

import vardb
TESTDATA_DIR = os.path.join(os.path.split(vardb.__file__)[0], "testdata")
assert os.path.isdir(TESTDATA_DIR)

ANALYSIS = "brca_sample_3"
GENEPANEL = "HBOCUTV_v01"

@pytest.fixture(scope="session")
def unannotated_vcf():
    filename = ANALYSIS+".vcf"
    full_path = subprocess.check_output("find %s -type f -name %s" % (TESTDATA_DIR, filename), shell=True).strip()
    with open(full_path, 'r') as f:
        vcf = f.read()

    return vcf


@pytest.fixture(scope="session")
def annotated_vcf():
    filename = ".".join([ANALYSIS, GENEPANEL]) + ".vcf"
    full_path = subprocess.check_output("find %s -type f -name %s" % (TESTDATA_DIR, filename), shell=True).strip()
    with open(full_path, 'r') as f:
        vcf = f.read()
    return vcf

def split_vcf(vcf):
    lines = vcf.split('\n')
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

    variants1 = variants[:len(variants)/2]
    variants2 = variants[len(variants)/2:]

    N1 = len(variants1)
    N2 = len(variants2)
    first = header+"\n"+"\n".join(variants1)
    second = header + "\n" + "\n".join(variants2)

    return first,second, N1,N2


@pytest.fixture
def split_annotated_vcf(annotated_vcf):
    return split_vcf(annotated_vcf)

@pytest.fixture
def split_unannotated_vcf(unannotated_vcf):
    return split_vcf(unannotated_vcf)


def test_submit_annotationjob(session, client):
    "Submit annotation job"
    data = dict(mode="Analysis",
                user_id=1,
                vcf="Dummy vcf data",
                properties=dict(
                    analysis_name = "abc",
                    create_or_append = "Create",
                    genepanel = GENEPANEL,
                ))

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200

    annotation_jobs = session.query(sample.AnnotationJob).all()
    assert len(annotation_jobs) == 1

    annotation_job = annotation_jobs[0]
    assert annotation_job.status == "SUBMITTED"
    assert annotation_job.vcf == data["vcf"]
    assert annotation_job.mode == "Analysis"
    assert annotation_job.status_history == {}
    assert annotation_job.user_id == 1
    assert annotation_job.task_id == ""
    assert annotation_job.properties["analysis_name"] == data["properties"]["analysis_name"]
    assert annotation_job.properties["create_or_append"] == data["properties"]["create_or_append"]
    assert annotation_job.properties["genepanel"] == data["properties"]["genepanel"]


def test_deposit_annotationjob(session, client, unannotated_vcf, annotated_vcf):
    data = dict(mode="Analysis",
                status="ANNOTATED",
                task_id="123456789",
                user_id=1,
                vcf=unannotated_vcf,
                properties=dict(
                    analysis_name="abc",
                    create_or_append="Create",
                    genepanel=GENEPANEL
                ))

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    # Annotation job deposit
    deposit_data = dict(id=id, annotated_vcf=annotated_vcf)
    response = client.post(DEPOSIT_SERVICE_PATH, data=deposit_data)
    assert response.status_code == 200

    # Check that annotation job is deposited
    analyses = session.query(sample.Analysis).filter(
        sample.Analysis.name == ".".join([data["properties"]["analysis_name"], data["properties"]["genepanel"]])
    ).all()

    assert len(analyses) == 1



def test_status_update_annotationjob(session, client):
    # Submit annotation job
    data = dict(mode="Analysis",
                user_id=1,
                vcf="Dummy vcf data",
                properties=dict(
                    analysis_name = "abc",
                    create_or_append = "Create",
                    genepanel = GENEPANEL,
                ))

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    update_data = dict(id=id,
                       status="ANNOTATED",
                       message="Message from server",
                       task_id="123456789")
    response = client.patch(ANNOTATION_JOBS_PATH, data=update_data)
    assert response.status_code == 200

    annotation_jobs = session.query(sample.AnnotationJob).filter(
        sample.AnnotationJob.id == id
    ).all()

    assert len(annotation_jobs) == 1
    annotation_job = annotation_jobs[0]

    assert annotation_job.message == update_data["message"]
    assert annotation_job.status == update_data["status"]
    assert annotation_job.task_id== update_data["task_id"]
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
        alleles += allele_importer.process(a)
    session.rollback()
    fd.close()
    return alleles


def test_deposit_independent_variants(test_database, session, client, annotated_vcf):
    alleles = get_alleles(annotated_vcf, session)
    existing = session.query(allele.Allele).all()
    alleles_to_be_added = list(set(alleles)-set(existing))
    alleles_already_added = list(set(alleles)-set(alleles_to_be_added))

    data = dict(mode="Variants",
                status="ANNOTATED",
                task_id="123456789",
                user_id=1,
                vcf=annotated_vcf,
                properties=dict(
                    genepanel=GENEPANEL
                ))

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    # Annotation job deposit
    deposit_data = dict(id=id, annotated_vcf=annotated_vcf)
    response = client.post(DEPOSIT_SERVICE_PATH, data=deposit_data)
    assert response.status_code == 200

    # Check that annotation job is deposited
    new_alleles = session.query(allele.Allele).filter(
        ~allele.Allele.id.in_([a.id for a in existing])
    ).all()

    new_alleles = [(a.chromosome, a.start_position, a.open_end_position, a.change_from, a.change_to, a.change_type) for a in new_alleles]
    alleles_to_be_added = [(a.chromosome, a.start_position, a.open_end_position, a.change_from, a.change_to, a.change_type) for a in alleles_to_be_added]

    assert len(new_alleles) == len(alleles_to_be_added)
    assert set(new_alleles) == set(alleles_to_be_added)


def test_append_to_analysis(test_database, session, client, annotated_vcf):
    test_database.refresh()

    # Split vcf in two, to be submitted first as new analysis,
    # then to append to the newly created analysis
    first_vcf, second_vcf, N1, N2 = split_vcf(annotated_vcf)

    # Create a new analysis
    data1 = dict(mode="Analysis",
                user_id=1,
                vcf=first_vcf,
                properties=dict(
                    analysis_name = "abc",
                    create_or_append = "Create",
                    genepanel = GENEPANEL,
                ))

    response = client.post(ANNOTATION_JOBS_PATH, data=data1)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    # Annotation job deposit
    deposit_data = dict(id=id, annotated_vcf=first_vcf)
    response = client.post(DEPOSIT_SERVICE_PATH, data=deposit_data)
    assert response.status_code == 200

    # Check that annotation job is deposited
    analysis_name = ".".join([data1["properties"]["analysis_name"], data1["properties"]["genepanel"]])
    analyses = session.query(sample.Analysis).filter(
        sample.Analysis.name == analysis_name,
    ).all()

    assert len(analyses) == 1
    analysis_id = analyses[0].id
    genotypes = session.query(genotype.Genotype).filter(
        genotype.Genotype.analysis_id == analysis_id,
    ).all()
    assert len(genotypes) == N1

    # Create new annotation job, to append to newly created analysis
    data2 = dict(mode="Analysis",
                user_id=1,
                vcf=second_vcf,
                properties=dict(
                    analysis_name = analysis_name,
                    create_or_append = "Append",
                    genepanel = GENEPANEL,
                ))

    response = client.post(ANNOTATION_JOBS_PATH, data=data2)
    assert response.status_code == 200
    id = json.loads(response.get_data())["id"]

    # Annotation job deposit (append)
    deposit_data = dict(id=id, annotated_vcf=second_vcf)
    response = client.post(DEPOSIT_SERVICE_PATH, data=deposit_data)
    assert response.status_code == 200

    # Check that the new alleles were added to analysis
    genotypes = session.query(genotype.Genotype).filter(
        genotype.Genotype.analysis_id == analysis_id,
    ).all()

    assert len(genotypes) == N1+N2

