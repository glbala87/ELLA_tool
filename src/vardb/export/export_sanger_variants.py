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
from openpyxl.writer.write_only import WriteOnlyCell
from openpyxl import Workbook
from openpyxl.styles import Font


from api.util import alleledataloader
from api.util.alleledataloader import AlleleDataLoader
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

HAS_CONTENT = True

ANALYSIS_NAME_RE = re.compile('(?P<project_name>Diag-.+)-(?P<prove>.+)-(?P<genepanel_name>.+)-(?P<genepanel_version>.+)')


def extract_meta_from_name(analysis_name):
    matches = re.match(ANALYSIS_NAME_RE, analysis_name)
    if matches and len(matches.groupdict()) == 4:
        return matches.group('project_name'), matches.group('prove')
    else:
        return analysis_name,'?'


#Column header and width
COLUMN_PROPERTIES = [
    (u'Prosjektnummer', 14),
    (u'Prøvenummer', 10),
    (u'Genpanel', 20),  # navn(versjon)
    (u'Gen', 8),
    (u'Transkript', 14),
    (u'HGVSc', 12),
    (u'HGVSg', 12),
    (u'Klasse', 6)
    ]


def create_variant_row(default_transcript, analysis_info, allele_info):
    found_transcript = next(ifilter(lambda t: t['transcript'] == default_transcript,
                               get_nested(allele_info, ['annotation', 'transcripts'])),
                            None)
    classification = get_nested(allele_info, ['allele_assessment', 'classification'], "Ny")
    return [
        analysis_info['project_name'],
        analysis_info['prove_number'],
        "{name} ({version})".format(name=analysis_info['genepanel_name'],
                                    version=analysis_info['genepanel_version']),
        found_transcript['symbol'],
        found_transcript['transcript'],
        found_transcript.get('HGVSc_short', '?'),
        found_transcript.get('HGVSg', '?'),
        classification
    ]


def export_variants(session, filename):
    """
    Put alleles belonging to unfinished analyses in file

    :param session: An sqlalchemy session
    :param filename:
    """

    if not filename:
        raise RuntimeError("Filename for export is mandatory")

    ids_not_started = queries.workflow_analyses_not_started(session).all()
    if len(ids_not_started) < 1:
        return False

    analyses = session.query(sample.Analysis).filter(sample.Analysis.id.in_(ids_not_started)).all()
    analysis_names = {analysis.id: analysis.name for analysis in analyses}

    allele_ids_analysis_ids = session.query(allele.Allele.id, sample.Analysis.id).join(
        genotype.Genotype.alleles,
        sample.Sample,
        sample.Analysis,
    ).filter(
        sample.Analysis.id.in_(ids_not_started)
    ).all()

    all_allele_ids = []
    allele_analysis_mapping = {}  # allele_id => {'analysis_id': _ , 'analysis_name':  _}

    for tup in allele_ids_analysis_ids:
        al_id, an_id = tup
        all_allele_ids.append(al_id)
        allele_analysis_mapping[al_id] = {'analysis_id': an_id, 'analysis_name': analysis_names[an_id]}

    allele_ids_grouped_by_genepanel_and_filter_status = filter_result_of_alleles(session, all_allele_ids)

    # Datastructure for collecting file content:
    workbook = Workbook(write_only=True)  # Write only: Constant memory usage
    worksheet = workbook.create_sheet()
    csv = []

    # File headings
    csv_heading = []
    excel_heading = []
    for i, column_tuple in enumerate(COLUMN_PROPERTIES):
        label, width = column_tuple
        csv_heading.append('#' + label if i == 0 else label)
        title = WriteOnlyCell(worksheet, value=label)
        title.font = Font(bold=True)
        excel_heading.append(title)
        # chr(65) is 'A', chr(66) is 'B', etc
        worksheet.column_dimensions[chr(i+65)].width = width

    worksheet.append(excel_heading)
    csv.append(csv_heading)

    adl = AlleleDataLoader(session)
    genepanels = session.query(gene.Genepanel)
    genepanels_by_key = {(g.name, g.version):g for g in genepanels}

    # loop through genepanels and load allele data:
    for gp_key, allele_ids_for_genepanel in allele_ids_grouped_by_genepanel_and_filter_status.items():
        allele_ids_not_filtered_away = allele_ids_for_genepanel['allele_ids']
        alleles = session.query(allele.Allele).filter(allele.Allele.id.in_(allele_ids_not_filtered_away)).all()
        loaded_alleles = adl.from_objs(
            alleles,
            genepanel=genepanels_by_key.get(gp_key, None),
            include_allele_assessment=True
        )

        for allele_info in loaded_alleles:
            # import pdb; pdb.set_trace()
            project_name, prove_number = extract_meta_from_name(allele_analysis_mapping[allele_info['id']]['analysis_name'])
            analysis_info = {'genepanel_name': gp_key[0],
                             'genepanel_version': gp_key[1],
                             'project_name': project_name,
                             'prove_number': prove_number
                             }

            default_transcript = get_nested(allele_info, ['annotation', 'filtered_transcripts'])[0]
            variant_row = create_variant_row(default_transcript, analysis_info, allele_info)
            csv.append(variant_row)
            worksheet.append(variant_row)

    with open(filename + '.csv', 'w') as csv_file:
        for cols in csv:
            csv_file.write("\t".join(map(lambda c: c.encode('utf-8') if isinstance(c, (str, unicode)) else str(c), cols)))
            csv_file.write("\n")

    workbook.save(filename + ".xls")

    return True
