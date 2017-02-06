from flask import Flask, request, render_template, session, flash, redirect, \
    url_for, jsonify, Response
from util import FlaskClientProxy
import pytest
import vardb
from vardb.util import DB
from vardb.datamodel import sample
import os
import subprocess

TESTDATA_DIR = os.path.join(os.path.split(vardb.__file__)[0], "testdata")
assert os.path.isdir(TESTDATA_DIR)

ANALYSIS = "brca_sample_2"
GENEPANEL = "HBOC_v01"

from api.polling import ANNOTATION_JOBS_PATH, ANNOTATION_SERVICE_ANNOTATE_PATH, ANNOTATION_SERVICE_STATUS_PATH, \
    ANNOTATION_SERVICE_PROCESS_PATH, DEPOSIT_SERVICE_PATH

@pytest.fixture
def unannotated_vcf():
    filename = ANALYSIS+".vcf"
    full_path = subprocess.check_output("find %s -type f -name %s" % (TESTDATA_DIR, filename), shell=True).strip()
    with open(full_path, 'r') as f:
        vcf = f.read()
    return vcf


@pytest.fixture
def annotated_vcf():
    filename = ".".join([ANALYSIS, GENEPANEL]) + ".vcf"
    print filename
    full_path = subprocess.check_output("find %s -type f -name %s" % (TESTDATA_DIR, filename), shell=True).strip()
    with open(full_path, 'r') as f:
        vcf = f.read()
    return vcf

from vardb.util import DB




def split_vcf(vcf):
    lines = vcf.split('\n')
    header = []
    for l in iter(lines):
        header.append(l)
        if l.startswith("#CHROM"):
            break
    header = "\n".join(header)

    variants = []
    for l in iter(lines):
        variants.append(l)

    first = header+"\n"+"\n".join(variants[:len(variants)/2])
    second = header + "\n" + "\n".join(variants[len(variants)/2:])

    return {"first": first, "second": second}


@pytest.fixture
def split_annotated_vcf(annotated_vcf):
    return split_vcf(annotated_vcf)

@pytest.fixture
def split_unannotated_vcf(unannotated_vcf):
    return split_vcf(unannotated_vcf)

@pytest.fixture
def client():
    return FlaskClientProxy()

@pytest.fixture
def session():
    db = DB()
    db.connect()
    session = db.session()
    return session

def test_submit_annotationjob(session, client, unannotated_vcf):
    "Submit annotation job"
    data = dict(mode="Analysis",
                user_id=1,
                vcf=unannotated_vcf,
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
    assert annotation_job.vcf == unannotated_vcf
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

    annotation_jobs = session.query(sample.AnnotationJob).filter(
        sample.AnnotationJob.task_id==data["task_id"]
    ).all()
    assert len(annotation_jobs) == 1

    annotation_job = annotation_jobs[0]
    id = annotation_job.id

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
                vcf=unannotated_vcf,
                properties=dict(
                    analysis_name = "abc",
                    create_or_append = "Create",
                    genepanel = GENEPANEL,
                ))

    response = client.post(ANNOTATION_JOBS_PATH, data=data)
    assert response.status_code == 200

    update_data = dict(status="ANNOTATED", message="Message from server", task_id="123456789")
    response = client.patch(ANNOTATION_JOBS_PATH, data=update_data)
    assert response.status_code == 200

    annotation_jobs = session.query(sample.AnnotationJob).filter(
        sample.AnnotationJob.task_id == update_data["task_id"]
    ).all()

    assert len(annotation_jobs) == 1
    annotation_job = annotation_jobs[0]

    assert annotation_job.message == update_data["message"]
    assert annotation_job.status == update_data["status"]
    assert len(annotation_job.status_history) == 1
