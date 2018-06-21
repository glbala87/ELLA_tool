#!/usr/bin/env python

import os
import json
from collections import OrderedDict

import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects import postgresql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


GenepanelTranscript = table('genepanel_transcript',
                            column('genepanel_name', sa.String()),
                            column('genepanel_version', sa.String()),
                            column('transcript_id', sa.Integer())
                            )

Transcript = table('transcript',
                   column('id', sa.Integer()),
                   column('gene_id', sa.Integer()),
                   column('transcript_name', sa.String()),
                   column('type', sa.String()),
                   column('corresponding_refseq', sa.String()),
                   column('corresponding_ensembl', sa.String()),
                   column('corresponding_lrg', sa.String()),
                   column('genome_reference', sa.String()),
                   column('chromosome', sa.String()),
                   column('tx_start', sa.Integer()),
                   column('tx_end', sa.Integer()),
                   column('strand', sa.String()),
                   column('cds_start', sa.Integer()),
                   column('cds_end', sa.Integer()),
                   column('exon_starts', postgresql.ARRAY(sa.Integer())),
                   column('exon_ends', postgresql.ARRAY(sa.Integer()))
                   )

GenepanelPhenotype = table('genepanel_phenotype',
                            column('genepanel_name', sa.String()),
                            column('genepanel_version', sa.String()),
                            column('phenotype_id', sa.Integer())
                            )

Phenotype = table('phenotype',
                  column('id', sa.Integer()),
                  column('gene_id', sa.Integer()),
                  column('description', sa.String()),
                  column('inheritance', sa.String()),
                  column('omim_id', sa.Integer()),
                  )

Gene = table('gene',
             column('hgnc_id', sa.Integer()),
             column('hgnc_symbol', sa.String()),
             column('ensembl_gene_id', sa.String()),
             column('omim_entry_id', sa.Integer())
             )


def get_connection(host):
    engine = create_engine(
        host,
        client_encoding='utf8',
    )

    conn = engine.connect()

    return conn





def get_transcripts(conn, genepanel_name, genepanel_version):
    res = conn.execute(
        sa.select(
            list(Transcript.c)+list(Gene.c)
        ).where(
            sa.and_(
                sa.tuple_(GenepanelTranscript.c.genepanel_name,
                          GenepanelTranscript.c.genepanel_version) == (genepanel_name, genepanel_version),
                GenepanelTranscript.c.transcript_id == Transcript.c.id,
                Transcript.c.gene_id == Gene.c.hgnc_id
            )
        ),
    )

    # Database transcripts are zero-based, while anno-scripts use 1-based transcripts
    transcripts_one_based = []
    for t in list(res):
        t = dict(t)
        t["tx_start"] = t["tx_start"] + 1
        t["tx_end"] = t["tx_end"] + 1
        t["cds_start"] = t["cds_start"] + 1
        t["cds_end"] = t["cds_end"] + 1
        t["exon_starts"] = [es+1 for es in t["exon_starts"]]
        t["exon_ends"] = [ee+1 for ee in t["exon_ends"]]
        transcripts_one_based.append(t)

    return transcripts_one_based


def get_phenotypes(conn, genepanel_name, genepanel_version):
    res = conn.execute(
        sa.select(
            list(Phenotype.c)+list(Gene.c)
        ).where(
            sa.and_(
                sa.tuple_(GenepanelPhenotype.c.genepanel_name,
                          GenepanelPhenotype.c.genepanel_version) == (genepanel_name, genepanel_version),
                GenepanelPhenotype.c.phenotype_id == Phenotype.c.id,
                Gene.c.hgnc_id == Phenotype.c.gene_id
            )
        )
    )
    return list(res)


def _get_phenotype_data(phenotypes):
    phenotypes_columns = OrderedDict()
    phenotypes_columns["#gene symbol"] = lambda p: p.hgnc_symbol
    phenotypes_columns["HGNC"] = lambda p: str(p.hgnc_id)
    phenotypes_columns["phenotype"] = lambda p: p.description
    phenotypes_columns["inheritance"] = lambda p: p.inheritance
    phenotypes_columns["omim_number"] = lambda p: str(p.omim_id)
    phenotypes_columns["pmid"] = lambda p: ''
    phenotypes_columns["inheritance info"] = lambda p: ''
    phenotypes_columns["comment"] = lambda p: ''

    phenotypes_data = "#\n"+"\t".join(phenotypes_columns.keys())

    for p in phenotypes:
        row = [v(p) for v in phenotypes_columns.values()]
        phenotypes_data += "\n"+"\t".join(row)
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
    transcript_columns["exonsStarts"] = lambda t: ",".join(
        str(es) for es in t["exon_starts"])
    transcript_columns["exonEnds"] = lambda t: ",".join(
        str(ee) for ee in t["exon_ends"])

    transcript_data = "#\n"+"\t".join(transcript_columns.keys())

    for t in transcripts:
        row = [v(t) for v in transcript_columns.values()]
        transcript_data += "\n"+"\t".join(row)
    return transcript_data


def _get_slop(transcripts, slop):
    slop_columns = OrderedDict()
    slop_columns["#chromosome"] = lambda t, *args: t["chromosome"]
    slop_columns["start"] = lambda t, start, end, slop, *args: str(start-slop)
    slop_columns["end"] = lambda t, start, end, slop, *args: str(end+slop)
    slop_columns["exon"] = lambda t, start, end, slop, exon_no: "%s__%s__exon%d" % (
        t["hgnc_symbol"], t["transcript_name"], exon_no)
    slop_columns["someValue"] = lambda t, *args: "0"
    slop_columns["strand"] = lambda t, *args: t["strand"]

    slop_data = "\t".join(slop_columns.keys())
    starts = []
    ends = []
    names = []

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
                ranges.append((es, ee, num_exons-exon_no))
            else:
                ranges.append((es, ee, exon_no+1))
            if end:
                break
        for (es, ee, exon_no) in ranges:
            row = [v(t, es, ee, slop, exon_no) for v in slop_columns.values()]
            slop_data += "\n" + "\t".join(row)
            starts.append(int(row[1]))
            ends.append(int(row[2]))
            names.append(row[3])

    return slop_data


def preimport(sample_id, usergroup, genepanel_name, genepanel_version, transcripts, phenotypes):
    files = dict()
    basename = "%s_%s" % (genepanel_name, genepanel_version)

    import tempfile
    transcripts_file = os.path.join(
        tempfile.gettempdir(), basename+'_transcripts.csv')
    with open(transcripts_file, 'w') as f:
        f.write(_get_transcript_data(transcripts))

    files["TRANSCRIPTS"] = transcripts_file

    phenotypes_file = os.path.join(
        tempfile.gettempdir(), basename+"_phenotypes.csv")
    with open(phenotypes_file, 'w') as f:
        f.write(_get_phenotype_data(phenotypes))
    files["PHENOTYPES"] = phenotypes_file

    for slop in [0, 2, 20]:
        slop_file = os.path.join(
            tempfile.gettempdir(), basename+"_slop%d.bed" % slop)
        with open(slop_file, 'w') as f:
            f.write(_get_slop(transcripts, slop))
        files["SLOP%d" % slop] = slop_file

    report_config_file = os.path.join(
        tempfile.gettempdir(), basename+"_report_config.txt")
    with open(report_config_file, 'w') as f:
        f.write("[DEFAULT]\ntitle={gp_name}\nversion={gp_version}".format(
            gp_name=genepanel_name, gp_version=genepanel_version))

    files["REPORT_CONFIG"] = report_config_file
    variables = dict()
    if usergroup == "EGG" or usergroup == 'testgroup02':
        variables['targets'] = 'excel'
    else:
        variables['targets'] = 'ella'

    variables["GP_NAME"] = genepanel_name
    variables["GP_VERSION"] = genepanel_version

    print json.dumps(
        {
            "files": files,
            'variables': variables
        },
        indent=4,
    )


if __name__ == "__main__":
    host = os.environ['DB_URL']
    conn = get_connection(host)
    sample_id = os.environ["SAMPLE_ID"]
    genepanel_name = os.environ["GENEPANEL_NAME"]
    genepanel_version = os.environ["GENEPANEL_VERSION"]
    usergroup = os.environ["USERGROUP"]

    phenotypes = get_phenotypes(conn, genepanel_name, genepanel_version)

    transcripts = get_transcripts(conn, genepanel_name, genepanel_version)
    preimport(sample_id, usergroup, genepanel_name,
              genepanel_version, transcripts, phenotypes)
