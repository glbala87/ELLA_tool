#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import os
import sys
import argparse
import logging
from jsonschema import validate
import json

from vardb.datamodel import gene as gm

log = logging.getLogger(__name__)


class Phenotype(object):
    """
    Helper class for reading phenotype info from file. Not a model class.
    """

    def __init__(self, description, geneSymbol, inheritance, omim, pmid, inheritance_info, comment):
        self.geneSymbol = geneSymbol
        self.description = description
        self.inheritance = inheritance
        self.omim = omim
        self.pmid = pmid
        self.inheritance_info = inheritance_info
        self.comment = comment


class Transcript(object):
    """
    Helper class for reading transcript info from file. Not a model class.
    """

    def __init__(self, chromosome, txStart, txEnd, refseqName, score, strand,
                 geneSymbol, geneAlias, eGene, eTranscript, cdsStart, cdsEnd,
                 exonStarts, exonEnds, inheritance, disease):

        self.chromosome = chromosome
        self.txStart = txStart
        self.txEnd = txEnd
        self.refseq = refseqName
        self.strand = strand
        self.geneSymbol = geneSymbol
        self.geneAlias = geneAlias
        self.eGene = eGene # Ensembl GeneID
        self.eTranscript = eTranscript
        self.cdsStart = cdsStart
        self.cdsEnd = cdsEnd
        self.exonStarts = exonStarts
        self.exonEnds = exonEnds
        self.inheritance = inheritance
        self.disease = disease


def load_phenotypes(phenotypes_path):
    if not phenotypes_path:
        return None
    with open(os.path.abspath(os.path.normpath(phenotypes_path))) as f:
        phenotypes = []
        for line in f:
            if line.startswith('#') or line.isspace():
                continue
            parts = line.strip().split('\t')
            (geneSymbol, description, inheritance, omim, pmid, inheritance_info, comment) = parts[:7]
            phenotypes.append(
                Phenotype(description, geneSymbol, inheritance, omim, pmid, inheritance_info, comment)
                           )
        return phenotypes


def load_transcripts(transcripts_path):
    with open(os.path.abspath(os.path.normpath(transcripts_path))) as f:
        transcripts = []
        for line in f:
            if line.startswith('#') or line.isspace():
                continue
            parts = line.strip().split('\t')
            (chromosome, txStart, txEnd, refseqName, score, strand,
             geneSymbol, geneAlias, eGene, eTranscript, cdsStart, cdsEnd,
             exonStarts, exonEnds, inheritance, disease) = parts
            txStart, txEnd, = int(txStart), int(txEnd)
            cdsStart, cdsEnd = int(cdsStart), int(cdsEnd)
            exonStarts = map(int, exonStarts.split(','))
            exonEnds = map(int, exonEnds.split(','))
            disease = disease.strip()

            transcripts.append(
                Transcript(chromosome, txStart, txEnd, refseqName, score, strand,
                           geneSymbol, geneAlias, eGene, eTranscript, cdsStart, cdsEnd,
                           exonStarts, exonEnds, inheritance, disease)
            )
        return transcripts


def config_valid(config):
    filename = 'src/vardb/datamodel/genap-genepanel-config-schema.json'

    if config:
        with open(filename) as schema_file:
            my_schema = json.load(schema_file)
            validate(config, my_schema)

    return True

class DepositGenepanel(object):

    def __init__(self, session):
        self.session = session

    def add_genepanel(self, transcripts_path, phenotypes_path, genepanelName, genepanelVersion, genomeRef='GRCh37',
                      config=None, force_yes=False):
        if self.session.query(gm.Genepanel).filter(gm.Genepanel.name == genepanelName,
                                                   gm.Genepanel.version == genepanelVersion).count():
            log.warning("{} {} already in database".format(genepanelName, genepanelVersion))
            if not force_yes and not raw_input("Update this genepanel (Y/n)?") == 'Y':
                log.warning("Aborting and rolling back")
                self.session.rollback()
                return -1

        if not config_valid(config):
            log.error("Genepanel config not valid according to JSON schema")

        db_transcripts = []
        db_phenotypes = []
        transcripts = load_transcripts(transcripts_path)
        phenotypes = load_phenotypes(phenotypes_path) if phenotypes_path else None
        genes = {}
        for t in transcripts:
            gene, created = gm.Gene.update_or_create(
                self.session,
                hugoSymbol=t.geneSymbol,
                ensemblGeneID=t.eGene
            )
            genes[gene.hugoSymbol] = gene
            if not created:
                log.info('Updated gene {}'.format(gene))

            db_transcript, created = gm.Transcript.update_or_create(
                self.session,
                gene=gene,
                refseqName=t.refseq,
                ensemblID=t.eTranscript,
                genomeReference=genomeRef,
                # Could wrap the rest in defaults{} for updating
                chromosome=t.chromosome,
                txStart=t.txStart,
                txEnd=t.txEnd,
                strand=t.strand,
                cdsStart=t.cdsStart,
                cdsEnd=t.cdsEnd,
                exonStarts=t.exonStarts,
                exonEnds=t.exonEnds
            )
            db_transcripts.append(db_transcript)

            if not created:
                log.info('Updated transcript {}'.format(db_transcript))

        if phenotypes:
            for ph in phenotypes:
                # TODO: remove all phenotypes for the panel, we'll reinsert all
                if ph.geneSymbol not in genes:
                    raise Exception("Cannot add phenotype '{}' for panel {}, the gene {} wasn't found in database"
                    .format(ph.description, genepanelName, ph.geneSymbol))
                db_phenotype, created = gm.Phenotype.update_or_create(
                    self.session,
                    genepanelName=genepanelName,
                    genepanelVersion=genepanelVersion,
                    gene_id=ph.geneSymbol,
                    gene=genes[ph.geneSymbol],  # TODO: not relevant for INSERT ?
                    description=ph.description,
                    inheritance=ph.inheritance,
                    inheritance_info=ph.inheritance_info,
                    omim_id=ph.omim,
                    pmid=ph.pmid,
                    comment=ph.comment
                )
                log.info("{} phenotype '{}'".format("Created" if created else "Updated", ph.description))

                db_phenotypes.append(db_phenotype)

        genepanel = gm.Genepanel(
            name=genepanelName,
            version=genepanelVersion,
            genomeReference=genomeRef,
            transcripts=db_transcripts,
            phenotypes=db_phenotypes,
            config=config)
        self.session.merge(genepanel)
        self.session.commit()
        log.info('Added {} {} with {} transcripts and {} phenotypes to database'
                 .format(genepanelName, genepanelVersion, len(db_transcripts), len(db_phenotypes)))
        return 0


def main(argv=None):
    """Example: ./deposit_genepanel.py --transcripts=./clinicalGenePanels/HBOC/HBOC.transcripts.csv"""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="""Adds or updates gene panels (including genes and transcripts) in varDB.""")
    parser.add_argument("--transcripts", action="store", dest="transcriptsPath",
                        required=True, default=None,
                        help="Path to gene panel transcripts file")
    parser.add_argument("--genepanelname", action="store", dest="genepanelName",
                        required=False, help="Name for gene panel (default from transcripts filename)")
    parser.add_argument("--genepanelversion", action="store",
                        dest="genepanelVersion", required=False,
                        help="Version of this gene panel (default from transcripts filename)")

    parser.add_argument("--genomeref", action="store", dest="genomeRef",
                        required=False, default="GRCh37",
                        help="Genomic reference sequence name")
    parser.add_argument("--force", action="store_true", dest="force",
                        required=False, default=False,
                        help="Genomic reference sequence name")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)
    genepanelName = args.genepanelName if args.genepanelName is not None else os.path.split(args.transcriptsPath)[1].split('_')[0]
    genepanelVersion = args.genepanelVersion if args.genepanelVersion is not None else os.path.split(args.transcriptsPath)[1].split('_')[3]
    print genepanelVersion
    assert genepanelVersion.startswith('v')

    dg = DepositGenepanel()
    return dg.add_genepanel(args.transcriptsPath, None, genepanelName, genepanelVersion, genomeRef=args.genomeRef, force_yes=args.force)


if __name__ == "__main__":
    sys.exit(main())

