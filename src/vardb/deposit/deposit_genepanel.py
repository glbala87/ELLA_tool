#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List
from sqlalchemy import and_
from vardb.datamodel import DB
from vardb.datamodel import gene as gm
from vardb.deposit.importers import bulk_insert_nonexisting

log = logging.getLogger(__name__)


def load_phenotypes(phenotypes_path: Path):
    converters: Dict[str, Callable] = {
        "gene symbol": str,
        "HGNC": int,
        "phenotype": str,
        "inheritance": str,
        "omim_number": int,
        "pmid": int,
        "info": str,
        "comment": str,
    }
    with phenotypes_path.open("rt") as f:
        phenotypes = []
        header = None
        for line in f:
            if line.startswith("gene symbol") or line.startswith("#gene symbol"):
                if line.startswith("#gene symbol"):
                    line = line.replace("#gene", "gene")
                header = line.strip().split("\t")
                if set(header) - set(converters.keys()):
                    log.debug(
                        f"Missing converters for phenotype columns {','.join(set(header)-set(converters.keys()))}"
                    )
                continue
            if line.startswith("#") or line.isspace():
                continue
            if not header:
                raise RuntimeError(
                    "Found no valid header in {}. Header should start with 'gene symbol'. ".format(
                        phenotypes_path
                    )
                )

            data = dict(
                {
                    k: converters[k](v.strip()) if v.strip() else None
                    for k, v in zip(header, line.split("\t"))
                    if k in converters
                }
            )
            phenotypes.append(data)
        return phenotypes


def load_transcripts(transcripts_path: Path):
    converters: Dict[str, Callable] = {
        "chromosome": str,
        "txStart": int,
        "txEnd": int,
        "refseq": str,
        "source": str,
        "score": str,
        "strand": str,
        "geneSymbol": str,
        "HGNC": int,
        "OMIM gene entry": int,
        "geneAlias": str,
        "inheritance": str,
        "cdsStart": int,
        "cdsEnd": int,
        "exonStarts": lambda x: list(map(int, x.split(","))),
        "exonEnds": lambda x: list(map(int, x.split(","))),
    }
    with open(transcripts_path, "rt") as f:
        transcripts = []
        header = None
        for line in f:
            if line.startswith("#chromosome"):
                header = line.strip().split("\t")
                header[0] = header[0][1:]  # Strip leading '#'
                if set(header) - set(converters.keys()):
                    log.debug(
                        f"Missing converters for transcript columns {','.join(set(header)-set(converters.keys()))}"
                    )
            if line.startswith("#") or line.isspace():
                continue
            if not header:
                raise RuntimeError(
                    "Found no valid header in {}. Header should start with '#chromosome'. ".format(
                        transcripts_path
                    )
                )

            data = dict(
                {
                    k: converters[k](v.strip()) if v.strip() else None
                    for k, v in zip(header, line.split("\t"))
                    if k in converters
                }
            )
            transcripts.append(data)
        return transcripts


class DepositGenepanel(object):
    def __init__(self, session):
        self.session = session

    def insert_genes(self, transcript_data: List[Dict[str, Any]]):

        # Avoid duplicate genes
        distinct_genes = set()
        for t in transcript_data:
            distinct_genes.add((t["HGNC"], t["geneSymbol"], t["OMIM gene entry"]))

        gene_rows = list()
        for d in list(distinct_genes):
            gene_rows.append({"hgnc_id": d[0], "hgnc_symbol": d[1], "omim_entry_id": d[2]})

        gene_inserted_count = 0
        gene_reused_count = 0
        for existing, created in bulk_insert_nonexisting(
            self.session,
            gm.Gene,
            gene_rows,
            compare_keys=["hgnc_id", "hgnc_symbol"],
        ):
            gene_inserted_count += len(created)
            gene_reused_count += len(existing)
        return gene_inserted_count, gene_reused_count

    def insert_transcripts(
        self, transcript_data, genepanel_name, genepanel_version, genome_ref, replace=False
    ):
        transcript_rows = list()
        for t in transcript_data:
            transcript_rows.append(
                {
                    "gene_id": t["HGNC"],  # foreign key to gene
                    "transcript_name": t["refseq"],
                    "type": "RefSeq",
                    "corresponding_refseq": None,
                    "corresponding_ensembl": None,
                    "corresponding_ensembl": None,
                    "corresponding_lrg": None,
                    "chromosome": t["chromosome"],
                    "tx_start": t["txStart"],
                    "tx_end": t["txEnd"],
                    "strand": t["strand"],
                    "inheritance": t["inheritance"],
                    "source": t["source"],
                    "cds_start": t["cdsStart"],
                    "cds_end": t["cdsEnd"],
                    "exon_starts": t["exonStarts"],
                    "exon_ends": t["exonEnds"],
                    "genome_reference": genome_ref,
                }
            )

        transcript_inserted_count = 0
        transcript_reused_count = 0

        # If replacing, delete old connections in junction table
        if replace:
            log.debug("Replacing transcripts connected to genepanel.")
            self.session.execute(
                gm.genepanel_transcript.delete().where(
                    and_(
                        gm.genepanel_transcript.columns.genepanel_name == genepanel_name,
                        gm.genepanel_transcript.columns.genepanel_version == genepanel_version,
                    )
                )
            )

        for existing, created in bulk_insert_nonexisting(
            self.session,
            gm.Transcript,
            transcript_rows,
            include_pk="id",
            compare_keys=["transcript_name"],
            replace=replace,
        ):
            transcript_inserted_count += len(created)
            transcript_reused_count += len(existing)

            # Connect to genepanel by inserting into the junction table
            junction_values = list()
            pks = [i["id"] for i in existing + created]
            for pk in pks:
                junction_values.append(
                    {
                        "genepanel_name": genepanel_name,
                        "genepanel_version": genepanel_version,
                        "transcript_id": pk,
                    }
                )
            self.session.execute(gm.genepanel_transcript.insert(), junction_values)

        return transcript_inserted_count, transcript_reused_count

    def insert_phenotypes(self, phenotype_data, genepanel_name, genepanel_version, replace=False):

        phenotype_rows = list()
        for ph in phenotype_data:

            if not ph.get("HGNC"):
                log.warning("Skipping phenotype {} since HGNC is empty".format(ph.get("phenotype")))
                continue
            # Database has unique constraint on (gene_id, description, inheritance)
            row_data = {
                "gene_id": ph["HGNC"],
                "description": ph["phenotype"],
                "inheritance": ph["inheritance"],
                "omim_id": ph["omim_number"],
            }

            is_duplicate = next(
                (
                    p
                    for p in phenotype_rows
                    if p["gene_id"] == row_data["gene_id"]
                    and p["description"] == row_data["description"]
                    and p["inheritance"] == row_data["inheritance"]
                ),
                None,
            )
            if is_duplicate:
                log.warning("Skipping duplicate phenotype {}".format(ph.get("phenotype")))
                continue

            phenotype_rows.append(row_data)

        phenotype_inserted_count = 0
        phenotype_reused_count = 0

        # If replacing, delete old connections in junction table
        if replace:
            log.debug("Replacing transcripts connected to genepanel.")
            self.session.execute(
                gm.genepanel_phenotype.delete().where(
                    and_(
                        gm.genepanel_phenotype.columns.genepanel_name == genepanel_name,
                        gm.genepanel_phenotype.columns.genepanel_version == genepanel_version,
                    )
                )
            )

        for existing, created in bulk_insert_nonexisting(
            self.session,
            gm.Phenotype,
            phenotype_rows,
            include_pk="id",
            compare_keys=["gene_id", "description", "inheritance"],
            replace=replace,
        ):
            phenotype_inserted_count += len(created)
            phenotype_reused_count += len(existing)
            # Connect to genepanel by inserting into the junction table
            junction_values = list()
            pks = [i["id"] for i in existing + created]
            for pk in pks:
                junction_values.append(
                    {
                        "genepanel_name": genepanel_name,
                        "genepanel_version": genepanel_version,
                        "phenotype_id": pk,
                    }
                )
            self.session.execute(gm.genepanel_phenotype.insert(), junction_values)

        return phenotype_inserted_count, phenotype_reused_count

    def add_genepanel(
        self,
        transcripts_path,
        phenotypes_path,
        genepanel_name,
        genepanel_version,
        genomeRef="GRCh37",
        replace=False,
    ):

        if not transcripts_path:
            raise RuntimeError("Missing mandatory argument: path to transcript file")
        if not phenotypes_path:
            raise RuntimeError("Missing mandatory argument: path to phenotypes file")

        # Insert genepanel
        existing_panel = (
            self.session.query(gm.Genepanel)
            .filter(gm.Genepanel.name == genepanel_name, gm.Genepanel.version == genepanel_version)
            .one_or_none()
        )

        if not existing_panel:
            # We connect transcripts and phenotypes to genepanel later
            genepanel = gm.Genepanel(
                name=genepanel_name,
                version=genepanel_version,
                genome_reference=genomeRef,
                official=True,
            )
            self.session.add(genepanel)

        else:
            if replace:
                log.info(
                    "Genepanel {} {} exists in database, will overwrite.".format(
                        genepanel_name, genepanel_version
                    )
                )
                existing_panel.genome_reference = genomeRef
            else:
                log.info(
                    "Genepanel {} {} exists in database, backing out. Use the 'replace' to force overwrite.".format(
                        genepanel_name, genepanel_version
                    )
                )
                return

        transcript_data = load_transcripts(transcripts_path)
        if not transcript_data:
            raise RuntimeError("Found no transcripts in file")
        phenotype_data = load_phenotypes(phenotypes_path)
        if not phenotypes_path:
            raise RuntimeError("Found no phenotypes in file")

        gene_inserted_count = 0
        gene_reused_count = 0
        transcript_inserted_count = 0
        transcript_reused_count = 0
        phenotype_inserted_count = 0
        phenotype_reused_count = 0

        # Genes
        gene_inserted_count, gene_reused_count = self.insert_genes(transcript_data)
        log.info("GENES: Created {}, reused {}".format(gene_inserted_count, gene_reused_count))

        # Transcripts
        transcript_inserted_count, transcript_reused_count = self.insert_transcripts(
            transcript_data, genepanel_name, genepanel_version, genomeRef, replace=replace
        )

        log.info(
            "TRANSCRIPTS: Created {}, reused {}".format(
                transcript_inserted_count, transcript_reused_count
            )
        )

        # Phenotypes
        phenotype_inserted_count, phenotype_reused_count = self.insert_phenotypes(
            phenotype_data, genepanel_name, genepanel_version, replace=replace
        )

        log.info(
            "PHENOTYPES: Created {}, reused {}".format(
                phenotype_inserted_count, phenotype_reused_count
            )
        )

        self.session.commit()
        log.info(
            "Added {} {} with {} genes, {} transcripts and {} phenotypes to database".format(
                genepanel_name,
                genepanel_version,
                gene_inserted_count + gene_reused_count,
                transcript_inserted_count + transcript_reused_count,
                phenotype_inserted_count + phenotype_reused_count,
            )
        )
        return 0


def main(argv=None):
    """Example: ./deposit_genepanel.py --transcripts=./clinicalGenePanels/HBOC/HBOC.transcripts.csv"""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="""Adds or updates gene panels in varDB.
                       Use any or all of --transcripts/phenotypes.
                       If the panel exists you must add the --replace option.\n
                       When creating a new panel, use -transcripts and --phenotypes without --replace"""
    )
    parser.add_argument(
        "--transcripts",
        action="store",
        dest="transcriptsPath",
        required=True,
        help="Path to gene panel transcripts file",
    )
    parser.add_argument(
        "--phenotypes",
        action="store",
        dest="phenotypesPath",
        required=True,
        help="Path to gene panel phenotypes file",
    )
    parser.add_argument(
        "--genepanelname",
        action="store",
        dest="genepanelName",
        required=True,
        help="Name for gene panel",
    )
    parser.add_argument(
        "--genepanelversion",
        action="store",
        dest="genepanelVersion",
        required=True,
        help="Version of this gene panel",
    )
    parser.add_argument(
        "--genomeref",
        action="store",
        dest="genomeRef",
        required=False,
        default="GRCh37",
        help="Genomic reference sequence name",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        dest="replace",
        required=False,
        default=False,
        help="Overwrite existing data in database",
    )
    args = parser.parse_args(argv)

    from applogger import setup_logger

    setup_logger()

    genepanel_name = args.genepanelName
    genepanel_version = args.genepanelVersion
    assert genepanel_version.startswith("v")

    db = DB()
    db.connect()

    dg = DepositGenepanel(db.session)
    return dg.add_genepanel(
        args.transcriptsPath,
        args.phenotypesPath,
        genepanel_name,
        genepanel_version,
        genomeRef=args.genomeRef,
        replace=args.replace,
    )


if __name__ == "__main__":
    sys.exit(main())
