#!/usr/bin/env python

import datetime
import logging
import time
from os import path
from collections import defaultdict, OrderedDict
import pytz
from sqlalchemy.orm import subqueryload, joinedload
from openpyxl.writer.write_only import WriteOnlyCell
from openpyxl.styles import Font
from openpyxl import Workbook
from bs4 import BeautifulSoup

from vardb.datamodel import assessment, allele, sample, genotype
from datalayer import AlleleDataLoader

KEY_ANALYSES = "analyses"

"""
Dump current classification, i.e. alleleassessments for which
AlleleAssessment.date_superceeded == None, to an Excel file
"""

BATCH_SIZE = 200
SCRIPT_DIR = path.abspath(path.dirname(__file__))
log = logging.getLogger(__name__)

REF_FORMAT = "{title} (Pubmed {pmid}): {evaluation}"
REF_ORDER = ["relevance", "ref_auth_classification", "comment"]
CHROMOSOME_FORMAT = "{chromosome}:{start_position}-{open_end_position}"
DATE_FORMAT = "%Y-%m-%d"


# (field name, [Column header, Column width])
COLUMN_PROPERTIES = OrderedDict(
    [
        ("gene", ["Gene", 6]),
        ("transcript", ["Transcript", 15]),
        ("hgvsc", ["HGVSc", 26]),
        ("class", ["Class", 6]),
        ("date", ["Date", 11]),
        ("hgvsp", ["HGVSp", 26]),
        ("exon", ["#exon or intron/total", 11]),
        ("rsnum", ["RS number", 11]),
        ("consequence", ["Consequence", 20]),
        ("coordinate", ["GRCh37", 20]),
        ("n_samples", ["# samples", 3]),
        ("prev_class", ["Prev. class", 6]),
        ("prev_class_superceeded", ["Superceeded date", 11]),
        ("classification_eval", ["Evaluation", 20]),
        ("report", ["Report", 20]),
        ("acmg_eval", ["ACMG evaluation", 20]),
        ("freq_eval", ["Frequency comment", 20]),
        ("extdb_eval", ["External DB comment", 20]),
        ("pred_eval", ["Prediction comment", 20]),
        ("ref_eval", ["Reference evaluations", 20]),
        (KEY_ANALYSES, ["Analyses", 20]),
    ]
)


# openpyxl does not handle unicode control characters, except for \x09 (\t), \x10 (\n), \x0d(=13) (\r)
# Remove these from any string coming from html
CONTROL_CHARS_MAP = dict.fromkeys(i for i in range(32) if i not in [9, 10, 13])


def remove_control_chars(s):
    return s.translate(CONTROL_CHARS_MAP)


def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    attachments = [img.get("title") for img in soup.find_all("img")]
    return remove_control_chars(soup.get_text()) + (
        " " + ", ".join(attachments) if attachments else ""
    )


def get_batch(alleleassessments):
    """
    Generates lists of AlleleAssessment objects
    :param alleleassessments: An sqlalchemy.orm.query object
    :yield : a list of max BATCH_SIZE AlleleAssessments
    """
    i_batch = 0
    while True:
        batch = alleleassessments.slice(i_batch * BATCH_SIZE, (i_batch + 1) * BATCH_SIZE).all()

        if batch:
            yield batch
        else:
            return
        i_batch += 1


def format_transcripts(allele_annotation):
    """
    Make dict with info about a transcript for all
    filtered transcript in allele_annotation
    :param allele_annotation: an allele_dict['annotation'] dict
    :return : a dict with info about transcript
    """
    keys = {
        "gene": "symbol",
        "transcript": "transcript",
        "hgvsc": "HGVSc_short",
        "hgvsp": "HGVSp",
        "exon": "exon",
        "intron": "intron",
        "rsnum": "dbsnp",
        "consequences": "consequences",
    }

    formatted_transcripts = defaultdict(list)
    filtered_transcripts = [
        t
        for t in allele_annotation["transcripts"]
        if t["transcript"] in allele_annotation["filtered_transcripts"]
    ]

    # If we have no filtered transcripts, include all of them so we can show something
    if not filtered_transcripts:
        filtered_transcripts = allele_annotation["transcripts"]

    for transcript in filtered_transcripts:
        for key, allele_key in list(keys.items()):
            formatted_transcript = transcript.get(allele_key)
            if isinstance(formatted_transcript, list):
                formatted_transcript = ", ".join(formatted_transcript)
            if formatted_transcript:
                formatted_transcripts[key].append(formatted_transcript)

    return {key: " | ".join(value) for key, value in list(formatted_transcripts.items())}


def format_classification(alleleassessment, adl, previous_alleleassessment=None):

    """
    Make a list of the classification fields of an AlleleAssessment
    :param alleleassessment: an AlleleAssessment object
    :param adl: an AlleleDataLoader object
    :return : a dict of formatted strings for an assessment
    """

    link_filter = {"annotation_id": [alleleassessment.annotation_id]}
    allele_dict = adl.from_objs(
        [alleleassessment.allele],
        link_filter=link_filter,
        genepanel=alleleassessment.genepanel,
        include_annotation=True,
        include_custom_annotation=False,
        include_allele_assessment=False,
        include_reference_assessments=False,
        include_allele_report=True,
    )[0]

    # Imported assessments without date can have 0000-00-00 as created_time. strftime doesn't like that..
    if alleleassessment.date_created < datetime.datetime(
        year=1950, month=1, day=1, tzinfo=pytz.utc
    ):
        date = "0000-00-00"
    else:
        date = alleleassessment.date_created.strftime(DATE_FORMAT)
    acmg_evals = " | ".join(
        [
            ": ".join([ae["code"], html_to_text(ae["comment"])]) if ae["comment"] else ae["code"]
            for ae in alleleassessment.evaluation.get("acmg", {}).get("included", [])
        ]
    )

    # Note that the order of the first ref evaluation fields are specified by
    # REF_ORDER. In order to include all refs, the remaining evaluation keys
    # are added using a set-operation:
    ref_evals = " | ".join(
        [
            REF_FORMAT.format(
                title=re.reference.title,
                pmid=re.reference.pubmed_id,
                evaluation=", ".join(
                    [
                        "=".join(map(str, [key, re.evaluation[key]]))
                        for key in REF_ORDER + list(set(re.evaluation.keys()) - set(REF_ORDER))
                        if key in re.evaluation
                    ]
                ),
            )
            for re in alleleassessment.referenceassessments
            if len(re.evaluation)
        ]
    )

    coordinate = CHROMOSOME_FORMAT.format(
        chromosome=allele_dict["chromosome"],
        start_position=allele_dict["start_position"] + 1,  # DB is 0-based
        open_end_position=allele_dict["open_end_position"],
    )

    formatted_transcript = format_transcripts(allele_dict["annotation"])

    n_samples = len(alleleassessment.allele.genotypes)

    return {
        "gene": formatted_transcript.get("gene"),
        "class": alleleassessment.classification,
        "transcript": formatted_transcript.get("transcript"),
        "hgvsc": formatted_transcript.get("hgvsc"),
        "date": date,
        "hgvsp": formatted_transcript.get("hgvsp"),
        "exon": formatted_transcript.get("exon") or formatted_transcript.get("intron"),
        "rsnum": formatted_transcript.get("rsnum"),
        "consequence": formatted_transcript.get("consequences"),
        "coordinate": coordinate,
        "n_samples": n_samples,
        "prev_class": previous_alleleassessment.classification if previous_alleleassessment else "",
        "prev_class_superceeded": previous_alleleassessment.date_superceeded.strftime(DATE_FORMAT)
        if previous_alleleassessment
        else "",
        "classification_eval": html_to_text(
            alleleassessment.evaluation.get("classification", {}).get("comment", "")
        ),
        "acmg_eval": acmg_evals,
        "report": html_to_text(
            allele_dict.get("allele_report", {}).get("evaluation", {}).get("comment", "")
        ),
        "freq_eval": html_to_text(
            alleleassessment.evaluation.get("frequency", {}).get("comment", "")
        ),
        "extdb_eval": html_to_text(
            alleleassessment.evaluation.get("external", {}).get("comment", "")
        ),
        "pred_eval": html_to_text(
            alleleassessment.evaluation.get("prediction", {}).get("comment", "")
        ),
        "ref_eval": html_to_text(ref_evals),
    }


def dump_alleleassessments(session, filename, with_analysis_names):
    """
    Save all current alleleassessments to Excel document
    :param session: An sqlalchemy session
    :param filename:
    """

    if not filename:
        raise RuntimeError("Filename for classification export is mandatory")

    if not with_analysis_names:
        del COLUMN_PROPERTIES[KEY_ANALYSES]

    alleleassessments = (
        session.query(assessment.AlleleAssessment)
        .options(
            subqueryload(assessment.AlleleAssessment.annotation)
            .subqueryload("allele")
            .joinedload("genotypes"),
            joinedload(assessment.AlleleAssessment.genepanel),
            subqueryload(assessment.AlleleAssessment.referenceassessments).joinedload("reference"),
        )
        .filter(assessment.AlleleAssessment.date_superceeded.is_(None))
    )

    adl = AlleleDataLoader(session)

    # Write only: Constant memory usage
    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet()

    csv = []
    csv_headers = []
    titles = []
    for ii, cp in enumerate(COLUMN_PROPERTIES.values()):
        csv_headers.append(cp[0])
        title = WriteOnlyCell(worksheet, value=cp[0])
        title.font = Font(bold=True)
        titles.append(title)
        # chr(65) is 'A', chr(66) is 'B', etc
        worksheet.column_dimensions[chr(ii + 65)].width = cp[1]

    worksheet.append(titles)
    csv.append(csv_headers)

    t_start = time.time()
    t_total = 0
    rows = list()
    csv_body = []
    for batch_alleleassessments in get_batch(alleleassessments):
        t_query = time.time()
        log.info(
            "Loaded %s allele assessments in %s seconds"
            % (len(batch_alleleassessments), str(t_query - t_start))
        )

        for alleleassessment in batch_alleleassessments:
            previous_alleleassessment = (
                session.query(assessment.AlleleAssessment)
                .filter(~assessment.AlleleAssessment.date_superceeded.is_(None))  # Is superceeded
                .filter(assessment.AlleleAssessment.allele_id == alleleassessment.allele_id)
                .order_by(assessment.AlleleAssessment.date_superceeded.desc())
                .limit(1)
                .one_or_none()
            )
            classification_dict = format_classification(
                alleleassessment, adl, previous_alleleassessment=previous_alleleassessment
            )
            if with_analysis_names:
                analyses = (
                    session.query(sample.Analysis)
                    .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
                    .filter(allele.Allele.id == alleleassessment.allele_id)
                    .all()
                )
                analysis_names = ",".join(map(str, [a.name for a in analyses]))

                classification_dict[KEY_ANALYSES] = analysis_names
            classification_columns = [classification_dict[key] for key in COLUMN_PROPERTIES]
            csv_body.append(classification_columns)
            rows.append(classification_columns)
        t_get = time.time()
        log.info("Read the allele assessments in %s seconds" % str(t_get - t_query))
        t_total += t_get - t_start
        t_start = time.time()

    rows.sort(key=lambda x: (x[0] or "", x[1] or "", x[2] or ""))
    csv_body.sort(key=lambda x: (x[0] or "", x[1] or "", x[2] or ""))

    for r in rows:
        worksheet.append(r)
    for r in csv_body:
        csv.append(r)

    log.info("Dumped database in %s seconds" % t_total)

    with open(filename + ".csv", "w") as csv_file:
        for cols in csv:
            csv_file.write("\t".join(map(lambda c: str(c) if not isinstance(c, str) else c, cols)))
            csv_file.write("\n")

    workbook.save(filename + ".xlsx")
    log.info("Wrote database to %s.xlsx/csv" % filename)
