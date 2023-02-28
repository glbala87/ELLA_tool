#!/usr/bin/env python3

import json
import os
from collections import OrderedDict
from functools import cmp_to_key

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import column, table

GenepanelTranscript = table(
    "genepanel_transcript",
    column("genepanel_name", sa.String()),
    column("genepanel_version", sa.String()),
    column("transcript_id", sa.Integer()),
)

Transcript = table(
    "transcript",
    column("id", sa.Integer()),
    column("gene_id", sa.Integer()),
    column("transcript_name", sa.String()),
    column("type", sa.String()),
    column("corresponding_refseq", sa.String()),
    column("corresponding_ensembl", sa.String()),
    column("corresponding_lrg", sa.String()),
    column("genome_reference", sa.String()),
    column("chromosome", sa.String()),
    column("tx_start", sa.Integer()),
    column("tx_end", sa.Integer()),
    column("strand", sa.String()),
    column("cds_start", sa.Integer()),
    column("cds_end", sa.Integer()),
    column("exon_starts", postgresql.ARRAY(sa.Integer())),
    column("exon_ends", postgresql.ARRAY(sa.Integer())),
)

GenepanelPhenotype = table(
    "genepanel_phenotype",
    column("genepanel_name", sa.String()),
    column("genepanel_version", sa.String()),
    column("phenotype_id", sa.Integer()),
)

Phenotype = table(
    "phenotype",
    column("id", sa.Integer()),
    column("gene_id", sa.Integer()),
    column("description", sa.String()),
    column("inheritance", sa.String()),
    column("omim_id", sa.Integer()),
)

Gene = table(
    "gene",
    column("hgnc_id", sa.Integer()),
    column("hgnc_symbol", sa.String()),
    column("ensembl_gene_id", sa.String()),
    column("omim_entry_id", sa.Integer()),
)


def get_connection(host):
    engine = create_engine(host, client_encoding="utf8")

    conn = engine.connect()

    return conn


def get_transcripts(conn, genepanel_name, genepanel_version):
    res = conn.execute(
        sa.select(list(Transcript.c) + list(Gene.c)).where(
            sa.and_(
                sa.tuple_(
                    GenepanelTranscript.c.genepanel_name, GenepanelTranscript.c.genepanel_version
                )
                == (genepanel_name, genepanel_version),
                GenepanelTranscript.c.transcript_id == Transcript.c.id,
                Transcript.c.gene_id == Gene.c.hgnc_id,
            )
        )
    )

    transcripts = [dict(t) for t in list(res)]
    return transcripts


def get_phenotypes(conn, genepanel_name, genepanel_version):
    res = conn.execute(
        sa.select(list(Phenotype.c) + list(Gene.c)).where(
            sa.and_(
                sa.tuple_(
                    GenepanelPhenotype.c.genepanel_name, GenepanelPhenotype.c.genepanel_version
                )
                == (genepanel_name, genepanel_version),
                GenepanelPhenotype.c.phenotype_id == Phenotype.c.id,
                Gene.c.hgnc_id == Phenotype.c.gene_id,
            )
        )
    )
    return list(res)


chr_int_map = dict(list(zip([str(x) for x in range(1, 23)] + ["X", "Y", "MT"], list(range(1, 26)))))


def sort_rows(r1, r2):
    if r1[0] != r2[0]:
        return chr_int_map[r1[0]] - chr_int_map[r2[0]]
    else:
        return int(r1[1]) - int(r2[1])


def _get_phenotype_data(phenotypes):
    phenotypes_columns = OrderedDict()
    phenotypes_columns["#gene symbol"] = lambda p: p.hgnc_symbol
    phenotypes_columns["HGNC"] = lambda p: str(p.hgnc_id)
    phenotypes_columns["phenotype"] = lambda p: p.description
    phenotypes_columns["inheritance"] = lambda p: p.inheritance
    phenotypes_columns["omim_number"] = lambda p: str(p.omim_id)
    phenotypes_columns["pmid"] = lambda p: ""
    phenotypes_columns["inheritance info"] = lambda p: ""
    phenotypes_columns["comment"] = lambda p: ""

    phenotypes_data = "#\n" + "\t".join(list(phenotypes_columns.keys()))

    for p in phenotypes:
        row = [v(p) for v in list(phenotypes_columns.values())]
        phenotypes_data += "\n" + "\t".join(row)
    return phenotypes_data


def _get_transcript_data(transcripts):
    transcript_columns = OrderedDict()
    transcript_columns["#chromosome"] = lambda t: t["chromosome"]
    transcript_columns["txStart"] = lambda t: str(t["tx_start"])
    transcript_columns["txEnd"] = lambda t: str(t["tx_end"])
    transcript_columns["refseq"] = lambda t: t["transcript_name"]
    transcript_columns["score"] = lambda t: "0"
    transcript_columns["strand"] = lambda t: t["strand"]
    transcript_columns["geneSymbol"] = lambda t: t["hgnc_symbol"]
    transcript_columns["HGNC"] = lambda t: str(t["hgnc_id"])
    transcript_columns["geneAlias"] = lambda t: ""
    transcript_columns["eGeneID"] = lambda t: t["ensembl_gene_id"]
    transcript_columns["eTranscriptID"] = lambda t: t["corresponding_ensembl"]
    transcript_columns["cdsStart"] = lambda t: str(t["cds_start"])
    transcript_columns["cdsEnd"] = lambda t: str(t["cds_end"])
    transcript_columns["exonsStarts"] = lambda t: ",".join(str(es) for es in t["exon_starts"])
    transcript_columns["exonEnds"] = lambda t: ",".join(str(ee) for ee in t["exon_ends"])

    transcript_data = "#\n" + "\t".join(list(transcript_columns.keys()))

    rows = []
    for t in transcripts:
        row = [v(t) for v in list(transcript_columns.values())]
        rows.append(row)

    for r in sorted(rows, key=cmp_to_key(sort_rows)):
        transcript_data += "\n" + "\t".join(r)
    return transcript_data


def _get_exon_regions(transcripts):
    exon_columns = OrderedDict()
    exon_columns["#chromosome"] = lambda t, *args: t["chromosome"]
    exon_columns["start"] = lambda t, start, end, *args: str(start)
    exon_columns["end"] = lambda t, start, end, *args: str(end)
    exon_columns["exon"] = lambda t, start, end, exon_no: "%s__%s__exon%d" % (
        t["hgnc_symbol"],
        t["transcript_name"],
        exon_no,
    )
    exon_columns["someValue"] = lambda t, *args: "0"
    exon_columns["strand"] = lambda t, *args: t["strand"]

    exon_regions_data = "\t".join(list(exon_columns.keys()))
    rows = []

    for t in transcripts:
        # SLOP is created from cds start and cds end, for exons containing these
        ranges = []
        strand = t["strand"]
        cds_start = t["cds_start"]
        cds_end = t["cds_end"]
        num_exons = len(t["exon_starts"])
        for exon_no, (es, ee) in enumerate(zip(t["exon_starts"], t["exon_ends"])):
            end = False
            if ee < cds_start:
                continue
            elif es < cds_start:
                es = cds_start
            elif es > cds_end:
                break

            if ee > cds_end:
                ee = cds_end
                end = True

            if strand == "-":
                ranges.append((es, ee, num_exons - exon_no))
            else:
                ranges.append((es, ee, exon_no + 1))
            if end:
                break
        for es, ee, exon_no in ranges:
            row = [v(t, es, ee, exon_no) for v in list(exon_columns.values())]
            rows.append(row)

    for r in sorted(rows, key=cmp_to_key(sort_rows)):
        exon_regions_data += "\n" + "\t".join(r)

    return exon_regions_data


def preimport(
    sample_id, usergroup, genepanel_name, genepanel_version, transcripts, phenotypes, priority
):
    files = dict()
    basename = "%s_%s" % (genepanel_name, genepanel_version)

    import tempfile

    transcripts_file = os.path.join(tempfile.gettempdir(), basename + "_transcripts.csv")
    with open(transcripts_file, "w") as f:
        f.write(_get_transcript_data(transcripts))

    files["TRANSCRIPTS"] = transcripts_file

    phenotypes_file = os.path.join(tempfile.gettempdir(), basename + "_phenotypes.csv")
    with open(phenotypes_file, "w") as f:
        f.write(_get_phenotype_data(phenotypes))
    files["PHENOTYPES"] = phenotypes_file

    exon_regions_file = os.path.join(tempfile.gettempdir(), basename + "_exons.bed")
    with open(exon_regions_file, "w") as f:
        f.write(_get_exon_regions(transcripts))
    files["EXON_REGIONS"] = exon_regions_file

    report_config_file = os.path.join(tempfile.gettempdir(), basename + "_report_config.txt")
    with open(report_config_file, "w") as f:
        f.write(
            "[DEFAULT]\ntitle={gp_name}\nversion={gp_version}".format(
                gp_name=genepanel_name, gp_version=genepanel_version
            )
        )

    files["REPORT_CONFIG"] = report_config_file

    variables = {
        "target": "ella",
        "GP_NAME": genepanel_name,
        "GP_VERSION": genepanel_version,
        "PRIORITY": priority,
    }

    print(json.dumps({"files": files, "variables": variables}, indent=4))


if __name__ == "__main__":
    host = os.environ["DB_URL"]
    conn = get_connection(host)
    sample_id = os.environ["SAMPLE_ID"]
    genepanel_name = os.environ["GENEPANEL_NAME"]
    genepanel_version = os.environ["GENEPANEL_VERSION"]
    usergroup = os.environ["USERGROUP"]
    priority = os.environ["PRIORITY"]

    phenotypes = get_phenotypes(conn, genepanel_name, genepanel_version)

    transcripts = get_transcripts(conn, genepanel_name, genepanel_version)
    preimport(
        sample_id, usergroup, genepanel_name, genepanel_version, transcripts, phenotypes, priority
    )
