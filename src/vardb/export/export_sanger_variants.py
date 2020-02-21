#!/usr/bin/env python
# coding=utf-8

import logging
import re
import itertools
from os import path
from collections import defaultdict
from sqlalchemy import or_, tuple_
import xlsxwriter

from datalayer import AlleleDataLoader
from datalayer import AlleleFilter
from api.util.util import get_nested
from vardb.datamodel import genotype, sample, allele, workflow
from datalayer import queries


"""
Dump variants that need Sanger verification to file
"""

SANGER_VERIFY_SKIP_CLASSIFICATIONS = ["1", "2", "U"]

SCRIPT_DIR = path.abspath(path.dirname(__file__))
log = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"

ANALYSIS_NAME_RE = re.compile(
    "(?P<project_name>Diag-.+)-(?P<prove>.+)-(?P<genepanel_name>.+)-(?P<genepanel_version>.+)"
)

# Matches the following
# chr7:g.6013138N>N chr7:g.6013175N>N
# chr7:g.6013138N>N chr7:g.6013175N>N BRCA2 NM_000059.3 exon3
# chr2:g.48010497N>N chr2:g.48010531N>N CDK2NA NM_001231.2 exon4
WARNING_REGIONS_RE = re.compile(
    r"(?P<pos1>chr[0-9XYM]+:g\..+N>N)\ (?P<pos2>chr[0-9XYM]+:g\..+N>N)(\ (?P<gene>.*)\ (?P<transcript>NM_.*)\ (?P<exon>.*))?"
)


def extract_meta_from_name(analysis_name):
    matches = re.match(ANALYSIS_NAME_RE, analysis_name)
    if matches and len(matches.groupdict()) == 4:
        return matches.group("project_name"), matches.group("prove")
    else:
        return analysis_name, "?"


# Column header and width
COLUMN_PROPERTIES = [
    ("Importdato", 12),
    ("Prosjektnummer", 14),
    ("Prøvenummer", 12),
    ("Genpanel", 20),  # navn(versjon)
    ("Startposisjon (HGVSg)", 22),
    ("Stopposisjon (HGVSg)", 22),
    ("Gen", 10),
    ("Transkript", 14),
    ("HGVSc / ekson", 24),
    ("Klasse", 6),
    ("Dekning", 6),
    ("Må verifiseres?", 13),
]


def get_analysis_info(analysis):
    project_name, prove_number = extract_meta_from_name(analysis.name)
    return {
        "genepanel_name": analysis.genepanel_name,
        "genepanel_version": analysis.genepanel_version,
        "project_name": project_name,
        "prove_number": prove_number,
        "date_deposited": analysis.date_deposited.strftime(DATE_FORMAT),
    }


def create_variant_row(default_transcripts, analysis_info, allele_info, sanger_verify):
    found_transcripts = []
    transcripts = get_nested(allele_info, ["annotation", "transcripts"])
    for default_transcript in default_transcripts:  # default_transcripts are sorted
        found_transcripts.append(
            next((t for t in transcripts if t["transcript"] == default_transcript), {})
        )

    classification = get_nested(allele_info, ["allele_assessment", "classification"], "Ny")
    return [
        analysis_info["date_deposited"],
        analysis_info["project_name"],
        analysis_info["prove_number"],
        "{name} ({version})".format(
            name=analysis_info["genepanel_name"], version=analysis_info["genepanel_version"]
        ),
        "chr{chr}:g.{start}N>N".format(
            chr=allele_info["chromosome"], start=allele_info["start_position"]
        ),
        "chr{chr}:g.{stop}N>N".format(
            chr=allele_info["chromosome"], stop=allele_info["open_end_position"]
        ),
        " | ".join([t.get("symbol", "-") for t in found_transcripts]),
        " | ".join([t.get("transcript", "-") for t in found_transcripts]),
        " | ".join([t.get("HGVSc_short", "-") for t in found_transcripts]),
        classification,
        "",
        "Ja" if sanger_verify else "Nei",
    ]


def get_variant_rows(session, filter_config_id, ids_not_started):
    variant_rows = list()

    # find alleles of unstarted analysis
    analyses_allele_ids = (
        session.query(
            sample.Analysis.id.label("analysis_id"),
            sample.Analysis.genepanel_name,
            sample.Analysis.genepanel_version,
            allele.Allele.id.label("allele_id"),
        )
        .join(genotype.Genotype.alleles, sample.Sample, sample.Analysis)
        .filter(sample.Analysis.id.in_(ids_not_started))
        .distinct()
        .all()
    )

    analyses = session.query(sample.Analysis).filter(sample.Analysis.id.in_(ids_not_started)).all()

    gp_allele_ids = defaultdict(list)
    for analysis_id, gp_name, gp_version, allele_id in analyses_allele_ids:
        gp_allele_ids[(gp_name, gp_version)].append(allele_id)

    # filter the alleles:
    af = AlleleFilter(session)
    non_filtered_gp_allele_ids = af.filter_alleles(filter_config_id, gp_allele_ids)
    analysis_id_allele_ids = defaultdict(list)
    for analysis_id, gp_name, gp_version, allele_id in analyses_allele_ids:
        if allele_id in non_filtered_gp_allele_ids[(gp_name, gp_version)]["allele_ids"]:
            analysis_id_allele_ids[analysis_id].append(allele_id)

    all_allele_ids = itertools.chain.from_iterable(list(analysis_id_allele_ids.values()))

    alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(all_allele_ids)).all()

    # Load and display data about the alleles:
    adl = AlleleDataLoader(session)
    for analysis_id, allele_ids in analysis_id_allele_ids.items():
        analysis = next(a for a in analyses if a.id == analysis_id)
        analysis_info = get_analysis_info(analysis)

        analysis_alleles = [a for a in alleles if a.id in allele_ids]

        loaded_alleles = adl.from_objs(
            analysis_alleles,
            analysis_id=analysis.id,
            genepanel=analysis.genepanel,
            include_allele_assessment=True,
            include_custom_annotation=False,
            include_reference_assessments=False,
            include_allele_report=False,
        )

        for loaded_allele in loaded_alleles:
            sanger_verify = loaded_allele["samples"][0]["genotype"].get("needs_verification", True)
            default_transcripts = get_nested(loaded_allele, ["annotation", "filtered_transcripts"])

            classification = get_nested(loaded_allele, ["allele_assessment", "classification"])
            if classification in SANGER_VERIFY_SKIP_CLASSIFICATIONS:
                continue

            variant_rows.append(
                create_variant_row(default_transcripts, analysis_info, loaded_allele, sanger_verify)
            )

    return variant_rows


def create_warning_row(analysis_info, warning_info):
    return [
        analysis_info["date_deposited"],
        analysis_info["project_name"],
        analysis_info["prove_number"],
        "{name} ({version})".format(
            name=analysis_info["genepanel_name"], version=analysis_info["genepanel_version"]
        ),
        warning_info.get("pos1", ""),
        warning_info.get("pos2", ""),
        warning_info.get("gene", ""),
        warning_info.get("transcript", ""),
        warning_info.get("exon", ""),
        "",
        "<20",
        "",
    ]


def get_warning_rows(session, ids_not_started):
    warning_rows = list()

    analyses_with_warnings = (
        session.query(sample.Analysis)
        .filter(
            sample.Analysis.id.in_(ids_not_started),
            ~sample.Analysis.warnings.is_(None),
            sample.Analysis.warnings != "",
        )
        .order_by(sample.Analysis.date_deposited)
        .all()
    )

    for analysis in analyses_with_warnings:
        analysis_info = get_analysis_info(analysis)
        for match in re.finditer(WARNING_REGIONS_RE, analysis.warnings):
            warning_info = match.groupdict()
            warning_rows.append(create_warning_row(analysis_info, warning_info))

    return warning_rows


def export_variants(session, genepanels, filter_config_id, excel_file_obj, csv_file_obj=None):
    """
    Put alleles belonging to unfinished analyses in file

    :param session: An sqlalchemy session
    :param genepanels: List of (gp_name, gp_version) to include
    :param excel_file_obj: File obj in which to write excel data
    :param csv_file_obj: File obj in which to write csv data (optional)
    """

    if not excel_file_obj:
        raise RuntimeError("Argument 'excel_file_obj' must be specified")

    ids_not_started = (
        session.query(workflow.AnalysisInterpretation.analysis_id)
        .join(sample.Analysis)
        .filter(
            tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version).in_(
                genepanels
            ),
            or_(
                workflow.AnalysisInterpretation.analysis_id.in_(
                    queries.workflow_analyses_interpretation_not_started(session)
                ),
                workflow.AnalysisInterpretation.analysis_id.in_(
                    queries.workflow_analyses_notready_not_started(session)
                ),
            ),
        )
        .all()
    )
    if len(ids_not_started) < 1:
        return False

    # Datastructure for collecting file content:
    workbook = xlsxwriter.Workbook(excel_file_obj, {"in_memory": True})
    header_format = workbook.add_format({"bold": True})
    sanger_worksheet = workbook.add_worksheet("Variants")
    csv = []
    # temporary data structure to sort:
    worksheet_rows = []
    csv_rows = []

    # File headings
    csv_heading = []
    for i, (label, width) in enumerate(COLUMN_PROPERTIES):
        csv_heading.append("#" + label if i == 0 else label)
        sanger_worksheet.write(0, i, label, header_format)
        sanger_worksheet.set_column(i, i, width)

    csv.append(csv_heading)

    for variant_row in get_variant_rows(session, filter_config_id, ids_not_started):
        csv_rows.append(variant_row)
        worksheet_rows.append(variant_row)

    for warning_row in get_warning_rows(session, ids_not_started):
        csv_rows.append(warning_row)
        worksheet_rows.append(warning_row)

    # sort by date, project name, sample_number, genomic pos
    def sort_function(r):
        return (r[0], r[1], r[2], r[4])

    worksheet_rows.sort(key=sort_function)
    csv_rows.sort(key=sort_function)
    csv.extend(csv_rows)

    if csv_file_obj:
        for cols in csv:
            csv_file_obj.write(
                "\t".join(map(lambda c: str(c) if not isinstance(c, str) else c, cols))
            )
            csv_file_obj.write("\n")

    for i, r in enumerate(worksheet_rows):
        sanger_worksheet.write_row(i + 1, 0, r)  # Start on row 2, col 1

    workbook.close()
    return True
