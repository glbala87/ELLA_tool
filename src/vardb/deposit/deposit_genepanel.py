#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import argparse
import io
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator
from sqlalchemy import and_

from vardb.datamodel import DB
from vardb.datamodel import gene as gm
from vardb.deposit.importers import bulk_insert_nonexisting

log = logging.getLogger(__name__)


class TranscriptRecord(BaseModel):
    chromosome: str = Field(alias="chromosome")
    start: int = Field(alias="read start")
    end: int = Field(alias="read end")
    name: str = Field(alias="name")
    # score: float = Field(default=0.0, alias="score")
    strand: str = Field(default="+", alias="strand")
    source: str = Field(default="custom", alias="source")
    hgnc_id: int = Field(default=None, alias="HGNC id")
    gene_symbol: str = Field(default=None, alias="HGNC symbol")
    gene_aliases: str = Field(default=None, alias="gene aliases")
    inheritance: str = Field(alias="inheritance")
    coding_start: Optional[int] = Field(default=None, alias="coding start")
    coding_end: Optional[int] = Field(default=None, alias="coding end")
    exon_starts: List[int] = Field(default=None, alias="exon starts")
    exon_ends: List[int] = Field(default=None, alias="exon ends")
    # metadata: Optional[str] = Field(default=None, alias="metadata")

    @validator("exon_starts", "exon_ends", pre=True)
    def validate_exon_starts_ends(cls, v):
        if v is None:
            return None
        return [int(x) for x in v.split(",") if x]

    class Config:
        extra = "ignore"


def load_phenotypes(phenotypes_path: Path):
    return []
    if not phenotypes_path:
        return None
    with io.open(os.path.abspath(os.path.normpath(phenotypes_path)), encoding="utf-8") as f:
        phenotypes = []
        header = None
        for line in f:
            if line.startswith("gene symbol") or line.startswith("#gene symbol"):
                if line.startswith("#gene symbol"):
                    line = line.replace("#gene", "gene")
                header = line.strip().split("\t")
                continue
            if line.startswith("#") or line.isspace():
                continue
            if not header:
                raise RuntimeError(
                    "Found no valid header in {}. Header should start with 'gene symbol'. ".format(
                        phenotypes_path
                    )
                )

            data = dict(list(zip(header, [l.strip() for l in line.split("\t")])))

            null_fields = ["pmid", "omim_number"]
            for n in null_fields:
                if n in data and data[n] == "":
                    data[n] = None
            phenotypes.append(data)
        return phenotypes


def load_transcripts(transcripts_path: Path):
    header = None
    transcripts = []
    with transcripts_path.open() as f:
        for l in f:
            if l.startswith("#chromosome"):
                header = l.strip().split("\t")
                header[0] = header[0][1:]  # strip leading '#'
            if l.startswith("#"):
                continue
            if not header:
                raise RuntimeError(
                    f"No valid header found in {transcripts_path}. "
                    "Make sure the file header starts with '#chromosome'."
                )

            data = dict(zip(header, [l.strip() for l in l.split("\t")]))
            tx_record = TranscriptRecord.parse_obj(data)
            transcripts.append(tx_record)
    return transcripts


class DepositGenepanel(object):
    def __init__(self, session):
        self.session = session

    def insert_genes(self, transcript_data: List[TranscriptRecord]):
        # Avoid duplicate genes
        distinct_genes = set()
        for t in transcript_data:
            distinct_genes.add((t.hgnc_id, t.gene_symbol))

        gene_rows = list()
        for d in list(distinct_genes):
            gene_rows.append({"hgnc_id": d[0], "hgnc_symbol": d[1]})

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
        self,
        transcript_data: List[TranscriptRecord],
        genepanel_name: str,
        genepanel_version: str,
        genome_ref: str,
        replace: bool = False,
    ):
        transcript_rows = list()
        inheritances: Dict[str, str] = {}
        for t in transcript_data:
            inheritances[t.name] = t.inheritance
            transcript_rows.append(
                {
                    "gene_id": t.hgnc_id,  # foreign key to gene
                    "transcript_name": t.name,
                    "type": "RefSeq",
                    "chromosome": t.chromosome,
                    "tx_start": t.start,
                    "tx_end": t.end,
                    "strand": t.strand,
                    "source": t.source,
                    "cds_start": t.coding_start,
                    "cds_end": t.coding_end,
                    "exon_starts": t.exon_starts,
                    "exon_ends": t.exon_ends,
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
            for tx in existing + created:
                junction_values.append(
                    {
                        "genepanel_name": genepanel_name,
                        "genepanel_version": genepanel_version,
                        "transcript_id": tx["id"],
                        "inheritance": inheritances[tx["transcript_name"]],
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
                "gene_id": int(ph["HGNC"]),
                "description": ph["phenotype"],
                "inheritance": ph["inheritance"],
                "omim_id": int(ph["omim_number"])
                if ph.get("omim_number") and ph["omim_number"].isalnum()
                else None,
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
    """
    Example:
        ./deposit_genepanel.py \
            --transcripts=./clinicalGenePanels/HBOC/HBOC_genes_transcripts_regions.tsv \
            --phenotypes=./clinicalGenePanels/HBOC/HBOC_phenotypes.tsv \
    """
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
