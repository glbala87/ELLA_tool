#!/usr/bin/env python
# coding=utf-8

import datetime
import logging
import re
import time
from itertools import ifilter
from os import path, mkdir
from collections import defaultdict, OrderedDict
import argparse
import pytz
from sqlalchemy.orm import subqueryload, joinedload, noload
import xlsxwriter

from api.util import alleledataloader
from api.util.alleledataloader import AlleleDataLoader
from api.util.allelefilter import AlleleFilter
from api.util.util import get_nested
from api.v1.resources.overview import filter_result_of_alleles
from vardb.datamodel import DB, gene, genotype
from vardb.datamodel import sample, allele
from api.util import queries


"""
Dump variants that need Sanger verification to file
"""

SCRIPT_DIR = path.abspath(path.dirname(__file__))
log = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"

ANALYSIS_NAME_RE = re.compile('(?P<project_name>Diag-.+)-(?P<prove>.+)-(?P<genepanel_name>.+)-(?P<genepanel_version>.+)')


def extract_meta_from_name(analysis_name):
    matches = re.match(ANALYSIS_NAME_RE, analysis_name)
    if matches and len(matches.groupdict()) == 4:
        return matches.group('project_name'), matches.group('prove')
    else:
        return analysis_name, '?'

WARNING_COLUMN_PROPERTIES = [
    (u'Importdato', 12),
    (u'Prosjektnummer', 14),
    (u'Prøvenummer', 12),
    (u'Warning', 50),
]



# Column header and width
COLUMN_PROPERTIES = [
    (u'Importdato', 12),
    (u'Prosjektnummer', 14),
    (u'Prøvenummer', 12),
    (u'Genpanel', 20),  # navn(versjon)
    (u'Startposisjon (HGVSg)', 22),
    (u'Stopposisjon (HGVSg)', 22),
    (u'Gen', 10),
    (u'Transkript', 14),
    (u'HGVSc', 24),
    (u'Klasse', 6),
    (u'Må verifiseres?', 13)
    ]


def create_variant_row(default_transcript, analysis_info, allele_info, sanger_verify):
    found_transcript = next(ifilter(lambda t: t['transcript'] == default_transcript,
                               get_nested(allele_info, ['annotation', 'transcripts'])),
                            None)
    classification = get_nested(allele_info, ['allele_assessment', 'classification'], "Ny")
    return [
        analysis_info['deposit_date'],
        analysis_info['project_name'],
        analysis_info['prove_number'],
        "{name} ({version})".format(name=analysis_info['genepanel_name'],
                                    version=analysis_info['genepanel_version']),
        "chr{chr}:g.{start}N>N".format(chr=allele_info['chromosome'], start=allele_info['start_position']),
        "chr{chr}:g.{stop}N>N".format(chr=allele_info['chromosome'], stop=allele_info['open_end_position']),
        found_transcript['symbol'],
        found_transcript['transcript'],
        found_transcript.get('HGVSc_short', '?'),
        classification,
        "Ja" if sanger_verify else "Nei"
    ]


def export_variants(session, excel_file_obj, csv_file_obj=None):
    """
    Put alleles belonging to unfinished analyses in file

    :param session: An sqlalchemy session
    :param excel_file_obj: File obj in which to write excel data
    :param csv_file_obj: File obj in which to write csv data (optional)
    """

    if not excel_file_obj:
        raise RuntimeError("Argument 'excel_file_obj' must be specified")

    ids_not_started = queries.workflow_analyses_not_started(session).all()
    if len(ids_not_started) < 1:
        return False

    # Datastructure for collecting file content:
    workbook = xlsxwriter.Workbook(excel_file_obj, {'in_memory': True})
    header_format = workbook.add_format({'bold': True})
    sanger_worksheet = workbook.add_worksheet('Variants')
    csv = []
    # temporary data structure to sort:
    worksheet_rows = []
    csv_rows = []

    # File headings
    csv_heading = []
    for i, (label, width) in enumerate(COLUMN_PROPERTIES):
        csv_heading.append('#' + label if i == 0 else label)
        sanger_worksheet.write(0, i, label, header_format)
        sanger_worksheet.set_column(i, i, width)

    csv.append(csv_heading)

    analyses_allele_ids = session.query(sample.Analysis, allele.Allele.id).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis,
    ).filter(
        sample.Analysis.id.in_(ids_not_started)
    ).all()

    analyses_with_allele_id_list = {}
    for an, an_id in analyses_allele_ids:
        if an.id not in analyses_with_allele_id_list:
            analyses_with_allele_id_list[an.id] = {'analysis': an, 'alleles': [an_id]}
        else:
            analyses_with_allele_id_list[an.id]['alleles'].append(an_id)

    af = AlleleFilter(session)
    adl = AlleleDataLoader(session)

    for an_id, values in analyses_with_allele_id_list.items():
        analysis = values['analysis']
        gp_key = (analysis.genepanel_name, analysis.genepanel_version)
        gp_allele_ids = {gp_key: values['alleles']}
        allele_ids_grouped_by_genepanel_and_filter_status = af.filter_alleles(gp_allele_ids)

        # loop through genepanels (one, since we hand the allele filter a single genepanel) and load allele data:
        for gp_key, allele_ids_for_genepanel in allele_ids_grouped_by_genepanel_and_filter_status.items():
            allele_ids_not_filtered_away = allele_ids_for_genepanel['allele_ids']
            alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids_not_filtered_away) if allele_ids_not_filtered_away else False).all()
            loaded_alleles = adl.from_objs(
                alleles,
                include_genotype_samples=[s.id for s in analysis.samples],
                genepanel=analysis.genepanel,
                include_allele_assessment=True
            )

            for allele_info in loaded_alleles:
                sanger_verify = allele_info['samples'][0]['genotype'].get('needs_verification', True)
                project_name, prove_number = extract_meta_from_name(analysis.name)
                analysis_info = {'genepanel_name':    gp_key[0],
                                 'genepanel_version': gp_key[1],
                                 'project_name':      project_name,
                                 'prove_number':      prove_number,
                                 'deposit_date':       analysis.deposit_date.strftime(DATE_FORMAT)
                                 }

                default_transcript = get_nested(allele_info, ['annotation', 'filtered_transcripts'])[0]
                variant_row = create_variant_row(default_transcript, analysis_info, allele_info, sanger_verify)
                csv_rows.append(variant_row)
                worksheet_rows.append(variant_row)

    # sort by first three columns:
    sort_function = lambda r: (r[0], r[1], r[2])
    worksheet_rows.sort(key=sort_function)
    csv_rows.sort(key=sort_function)
    csv.extend(csv_rows)

    if csv_file_obj:
        for cols in csv:
            csv_file_obj.write("\t".join(map(lambda c: c.encode('utf-8') if isinstance(c, (str, unicode)) else str(c), cols)))
            csv_file_obj.write("\n")

    for i, r in enumerate(worksheet_rows):
        sanger_worksheet.write_row(i+1, 0, r)  # Start on row 2, col 1

    #
    # Add warnings page
    #
    # TODO: Refactor this mess! Need to get this in before release...
    analyses_with_warnings = session.query(sample.Analysis.deposit_date, sample.Analysis.name, sample.Analysis.warnings).filter(
        sample.Analysis.id.in_(ids_not_started),
        ~sample.Analysis.warnings.is_(None),
        sample.Analysis.warnings != ''
    ).order_by(sample.Analysis.deposit_date).all()

    warnings_worksheet = workbook.add_worksheet('Warnings')

    for i, (label, width) in enumerate(WARNING_COLUMN_PROPERTIES):
        warnings_worksheet.write(0, i, label, header_format)
        warnings_worksheet.set_column(i, i, width)

    worksheet_rows = []
    for idx, (deposit_date, analysis_name, warning) in enumerate(analyses_with_warnings):
        project_name, prove_number = extract_meta_from_name(analysis_name)
        worksheet_rows.append([
            deposit_date.strftime(DATE_FORMAT),
            project_name,
            prove_number,
            warning.strip()
        ])

    worksheet_rows.sort(key=sort_function)
    for idx, r in enumerate(worksheet_rows):
        warnings_worksheet.set_row(idx+1, 70)
        warnings_worksheet.write_row(idx+1, 0, r)

    workbook.close()
    return True
