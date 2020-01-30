#!/usr/bin/env python

import logging
from sqlalchemy import tuple_, func
from openpyxl.writer.write_only import WriteOnlyCell
from openpyxl.styles import Font
from openpyxl import Workbook

from vardb.datamodel import DB, assessment, allele, sample
from datalayer import AlleleFilter


log = logging.getLogger(__name__)

CLASSIFICATIONS = ["1", "2", "3", "4", "5", "U", "DR"]

# (field name, [Column header, Column width])
COLUMN_PROPERTIES = [("Genepanel", 20), ("Analyses", 13), ("Unfiltered", 13), ("Per analyses", 13)]

for C in CLASSIFICATIONS:
    COLUMN_PROPERTIES.append(("Class {}".format(C), 15))


def export_variants_per_panel(session, output):

    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet()

    titles = []
    for ii, cp in enumerate(COLUMN_PROPERTIES):
        title = WriteOnlyCell(worksheet, value=cp[0])
        title.font = Font(bold=True)
        titles.append(title)
        # chr(65) is 'A', chr(66) is 'B', etc
        worksheet.column_dimensions[chr(ii + 65)].width = cp[1]

    worksheet.append(titles)

    genepanels = (
        session.query(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version)
        .distinct()
        .all()
    )

    gp_keys = [(g[0], g[1]) for g in genepanels]

    gp_allele_ids = dict()
    gp_analysis_cnt = dict()
    for gp_key in gp_keys:

        # Get analysis count

        analyses_cnt = (
            session.query(sample.Analysis.id)
            .filter(
                tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version) == gp_key
            )
            .distinct()
            .count()
        )
        gp_analysis_cnt[gp_key] = analyses_cnt

        allele_ids = (
            session.query(allele.Allele.id)
            .join(allele.Allele.genotypes, sample.Sample, sample.Analysis)
            .filter(
                tuple_(sample.Analysis.genepanel_name, sample.Analysis.genepanel_version) == gp_key
            )
            .distinct()
            .all()
        )
        gp_allele_ids[gp_key] = [a[0] for a in allele_ids]

    filtered_results, _ = AlleleFilter(session).filter_alleles(gp_allele_ids, None)
    for gp_key, data in filtered_results.items():
        row = []
        # Write filtered numbers
        allele_ids = data["allele_ids"]
        analyses_cnt = gp_analysis_cnt[gp_key]
        unfiltered_cnt = len(allele_ids)
        row += [
            WriteOnlyCell(worksheet, value="_".join(gp_key)),
            WriteOnlyCell(worksheet, value=analyses_cnt),
            WriteOnlyCell(worksheet, value=unfiltered_cnt),
            WriteOnlyCell(worksheet, value=float(unfiltered_cnt) / analyses_cnt),
        ]

        # Write classification numbers

        allele_classification = (
            session.query(
                assessment.AlleleAssessment.classification,
                func.count(assessment.AlleleAssessment.classification).over(
                    partition_by=assessment.AlleleAssessment.classification
                ),
            )
            .filter(assessment.AlleleAssessment.allele_id.in_(allele_ids))
            .distinct()
            .all()
        )

        allele_classification_cnt = dict()
        for r in allele_classification:
            allele_classification_cnt[r[0]] = r[1]

        for c in CLASSIFICATIONS:
            row.append(WriteOnlyCell(worksheet, allele_classification_cnt.get(c, 0)))
        worksheet.append(row)

    workbook.save(output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", required=True, action="store", dest="output", help="Name of output file"
    )

    args = parser.parse_args()

    db = DB()
    db.connect()
    session = db.session
    export_variants_per_panel(session, args.output)
