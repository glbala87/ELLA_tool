#!/usr/bin/env python

from vardb.datamodel import DB, assessment
from api.util import alleledataloader
from sqlalchemy.orm import subqueryload, joinedload
import logging
import time
from openpyxl import Workbook
from openpyxl.writer.write_only import WriteOnlyCell
from openpyxl.styles import Font
from os import path, mkdir
from collections import defaultdict, OrderedDict
import argparse

"""
Dump current classification, i.e. alleleassessments for which
AlleleAssessment.date_superceeded == None, to an Excel file
"""

BATCH_SIZE = 200
SCRIPT_DIR = path.abspath(path.dirname(__file__))
log = logging.getLogger(__name__)

TRANSCRIPT_FORMAT = "{transcript}.{version}:{hgvsc_short}"

REF_FORMAT = "{title} (Pubmed {pmid}): {evaluation}"

REF_ORDER = ['relevance', 'ref_auth_classification', 'comment']
# Ref evaluation fields, order not specified:
# ['ref_prot', 'ref_population', 'ref_prediction',
#  'ref_prediction_tool', 'ref_segregation',
#  'ref_segregation_quality', 'ref_quality',
#  'ref_prot_quality', 'ref_rna', 'ref_rna_quality', 'sources']

CHROMOSOME_FORMAT = "{chromosome}:{start_position}-{open_end_position}"

DATE_FORMAT = "%Y-%m-%d"

# (field name, [Column header, Column width])
COLUMN_PROPERTIES = OrderedDict([
    ('gene', ['Genes', 6]),
    ('class', ['Class', 5]),
    ('hgvsc', ['HGVSc', 26]),
    ('date', ['Date', 10]),
    ('hgvsp', ['HGVSp', 26]),
    ('exon', ['Exon/Intron', 11]),
    ('rsnum', ['RS number', 11]),
    ('user', ['User', 20]),
    ('consequence', ['Consequence', 20]),
    ('coordinate', ['Coordinate', 20]),
    ('n_samples', ['# samples', 6]),
    ('classification_eval', ['Evaluation', 20]),
    ('acmg_eval', ['ACMG evaluation', 20]),
    ('freq_eval', ['Frequency comment', 20]),
    ('extdb_eval', ['External DB comment', 20]),
    ('pred_eval', ['Prediction comment', 20]),
    ('ref_eval', ['Reference evaluations', 20])
])


def get_batch(alleleassessments):
    """
    Generates lists of AlleleAssessment objects
    :param alleleassessments: An sqlalchemy.orm.query object
    :yield : a list of max BATCH_SIZE AlleleAssessments
    """
    i_batch = 0
    while True:
        batch = alleleassessments.slice(
            i_batch*BATCH_SIZE, (i_batch+1)*BATCH_SIZE
        ).all()

        if batch:
            yield batch
        else:
            raise StopIteration
        i_batch += 1


def format_transcripts(allele_annotation):
    """
    Make dict with info about a transcript for each
    filtered transcript in allele_annotation
    :param allele_annotation: an allele_dict['annotation'] dict
    :return : a dict with info about transcript
    """
    keys = {'gene': 'SYMBOL',
            'hgvsc': 'HGVSc',
            'hgvsp': 'HGVSp',
            'exon': 'EXON',
            'intron': 'INTRON',
            'rsnum': 'Existing_variation',
            'consequence': 'Consequence'}

    formatted_transcripts = defaultdict(list)
    for filtered_transcript in allele_annotation['filtered_transcripts']:
        for transcript in allele_annotation['transcripts']:
            if filtered_transcript == transcript['Transcript']:
                for key, allele_key in keys.items():
                    formatted_transcript = transcript.get(allele_key)
                    if hasattr(formatted_transcript, '__iter__'):
                        formatted_transcript = ', '.join(formatted_transcript)
                    if formatted_transcript:
                        formatted_transcripts[key].append(formatted_transcript)

    return {key: ' | '.join(value) for key, value in formatted_transcripts.items()}


def format_classification(alleleassessment, adl):
    """
    Make list of the filtered transcripts of an AlleleAssessment
    :param alleleassessment: an AlleleAssessment object
    :param adl: an AlleleDataLoader object
    :return : list of formatted strings for filtered transcripts
    """
    allele_dict = adl.from_objs([alleleassessment.allele],
                                genepanel=alleleassessment.genepanel,
                                include_annotation=[alleleassessment.annotation],
                                include_custom_annotation=False,
                                include_allele_assessment=False,
                                include_reference_assessments=False,
                                include_allele_report=False)[0]

    date = alleleassessment.date_last_update.strftime(DATE_FORMAT)
    user = ' '.join(
        [alleleassessment.user.first_name, alleleassessment.user.last_name]
    )
    acmg_evals = ' | '.join(
        [': '.join([ae['code'], ae['comment']]) if ae['comment'] else ae['code']
         for ae in alleleassessment.evaluation['acmg']['included']]
    )

    # Note that the order of the first ref evaluation fields are specified by
    # REF_ORDER. In order to include all refs, the remaining evaluation keys
    # are added using a set-operation:
    ref_evals = ' | '.join(
        [REF_FORMAT.format(
            title=re.reference.title,
            pmid=re.reference.pubmed_id,
            evaluation=', '.join(
                ['='.join(map(str, [key, re.evaluation[key]]))
                 for key in REF_ORDER+list(set(re.evaluation.keys())-set(REF_ORDER))
                 if key in re.evaluation]
            )
        ) for re in alleleassessment.referenceassessments if len(re.evaluation)]
    )

    coordinate = CHROMOSOME_FORMAT.format(
        chromosome=allele_dict['chromosome'],
        start_position=allele_dict['start_position'],
        open_end_position=allele_dict['open_end_position']
    )

    formatted_transcript = format_transcripts(allele_dict['annotation'])

    n_samples = len(alleleassessment.allele.genotypes)
    log.debug('Allele %s, %s is found in samples %s' %
              (alleleassessment.allele_id,
               formatted_transcript.get('hgvsc'),
               '|'.join([','.join(map(str, [g.sample_id]))
                         for g in alleleassessment.allele.genotypes])
              )
    )

    classification_values = {
        'gene': formatted_transcript.get('gene'),
        'class': alleleassessment.classification,
        'hgvsc': formatted_transcript.get('hgvsc'),
        'date': date,
        'hgvsp': formatted_transcript.get('hgvsp'),
        'exon': formatted_transcript.get('exon') or formatted_transcript.get('intron'),
        'rsnum': formatted_transcript.get('rsnum'),
        'user': user,
        'consequence': formatted_transcript.get('consequence'),
        'coordinate': coordinate,
        'n_samples': n_samples,
        'classification_eval': alleleassessment.evaluation['classification']['comment'],
        'acmg_eval': acmg_evals,
        'freq_eval': alleleassessment.evaluation['frequency']['comment'],
        'extdb_eval': alleleassessment.evaluation['external']['comment'],
        'pred_eval': alleleassessment.evaluation['prediction']['comment'],
        'ref_eval': ref_evals
    }
    return [classification_values[key] for key in COLUMN_PROPERTIES]


def dump_alleleassessments(session, filename=None):
    """
    Save all current alleleassessments to Excel document
    :param session: An sqlalchemy session
    :param filename: Filename ending with .xlsx
    """
    alleleassessments = session.query(assessment.AlleleAssessment).order_by(
        assessment.AlleleAssessment.allele_id).options(
            joinedload(assessment.AlleleAssessment.user),
            subqueryload(assessment.AlleleAssessment.annotation).
            subqueryload('allele').joinedload('genotypes'),
            joinedload(assessment.AlleleAssessment.genepanel),
            subqueryload(assessment.AlleleAssessment.referenceassessments).
            joinedload('reference')
        ).filter(assessment.AlleleAssessment.date_superceeded.is_(None))

    adl = alleledataloader.AlleleDataLoader(session)

    if filename:
        # Write only: Constant memory usage
        workbook = Workbook(write_only=True)
        worksheet = workbook.create_sheet()

        titles = []
        for ii, cp in enumerate(COLUMN_PROPERTIES.itervalues()):
            title = WriteOnlyCell(worksheet, value=cp[0])
            title.font = Font(bold=True)
            titles.append(title)
            # chr(65) is 'A', chr(66) is 'B', etc
            worksheet.column_dimensions[chr(ii+65)].width = cp[1]

        worksheet.append(titles)

    t_start = time.time()
    t_total = 0
    for batch_alleleassessments in get_batch(alleleassessments):
        t_query = time.time()
        log.info("Loaded %s allele assessments in %s seconds" %
                 (len(batch_alleleassessments), str(t_query-t_start)))

        for alleleassessment in batch_alleleassessments:
            classification = format_classification(alleleassessment, adl)
            if filename:
                worksheet.append(classification)

        t_get = time.time()
        log.info("Read the allele assessments in %s seconds" %
                 str(t_get-t_query))
        t_total += t_get-t_start
        t_start = time.time()

    log.info("Dumped database in %s seconds" % t_total)

    if filename:
        workbook.save(filename)
        log.info("Wrote database to %s" % filename)


def main(session):
    LOG_FILENAME = path.join(SCRIPT_DIR, 'log/dump.log')

    parser = argparse.ArgumentParser(
        description="Dump current classifications to Excel file")
    parser.add_argument('-l', '--log', action='store_true',
                        help='Save log to file log/dump.log [Default: False]')
    parser.add_argument('excel_file', help='Name of file to store database')
    args = parser.parse_args()

    if args.log:
        if not path.exists(LOG_FILENAME):
            mkdir(path.dirname(LOG_FILENAME))
        logging.basicConfig(filename=LOG_FILENAME, filemode='w',
                            level=logging.DEBUG)

    if not args.excel_file.endswith('.xlsx'):
        args.excel_file += '.xlsx'

    filename = path.join(SCRIPT_DIR, args.excel_file)
    dump_alleleassessments(session, filename=filename)

if __name__ == '__main__':
    db = DB()
    db.connect()
    main(db.session)
