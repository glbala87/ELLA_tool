#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import os
import sys
import argparse
import logging
from jsonschema import validate, FormatChecker
import json

from vardb.datamodel import gene as gm

log = logging.getLogger(__name__)


def load_phenotypes(phenotypes_path):
    if not phenotypes_path:
        return None
    with open(os.path.abspath(os.path.normpath(phenotypes_path))) as f:
        phenotypes = []
        header = None
        for line in f:
            if line.startswith('gene symbol'):
                header = line.strip().split('\t')
                continue
            if line.startswith('#') or line.isspace():
                continue
            if not header:
                raise RuntimeError("Found no valid header in {}. Header should start with 'gene symbol'. ".format(phenotypes_path))

            data = dict(zip(header, [l.strip() for l in line.split('\t')]))

            null_fields = ['pmid', 'omim_number']
            for n in null_fields:
                if n in data and data[n] == '':
                    data[n] = None
            phenotypes.append(data)
        return phenotypes


def load_transcripts(transcripts_path):
    with open(os.path.abspath(os.path.normpath(transcripts_path))) as f:
        transcripts = []
        header = None
        for line in f:
            if line.startswith('#chromosome'):
                header = line.strip().split('\t')
                header[0] = header[0][1:]  # Strip leading '#'
            if line.startswith('#') or line.isspace():
                continue
            if not header:
                raise RuntimeError("Found no valid header in {}. Header should start with '#chromosome'. ".format(transcripts_path))

            data = dict(zip(header, [l.strip() for l in line.split('\t')]))
            data['txStart'], data['txEnd'], = int(data['txStart']), int(data['txEnd'])
            data['cdsStart'], data['cdsEnd'] = int(data['cdsStart']), int(data['cdsEnd'])
            data['exonsStarts'] = map(int, data['exonsStarts'].split(','))
            data['exonEnds'] = map(int, data['exonEnds'].split(','))
            transcripts.append(data)
        return transcripts


def config_valid(config):
    filename = 'src/vardb/datamodel/genap-genepanel-config-schema.json'

    with open(filename) as schema_file:
        my_schema = json.load(schema_file)
        # see doc http://python-jsonschema.readthedocs.io/en/latest/validate/#validating-formats
        validate(config, my_schema, format_checker=FormatChecker())

    return True


class DepositGenepanel(object):

    def __init__(self, session):
        self.session = session

    def add_genepanel(self,
                      transcripts_path,
                      phenotypes_path,
                      genepanelName,
                      genepanelVersion,
                      genomeRef='GRCh37',
                      config=None,
                      force_yes=False):

        if self.session.query(gm.Genepanel).filter(
            gm.Genepanel.name == genepanelName,
            gm.Genepanel.version == genepanelVersion
        ).count():
            log.info("Genepanel {} {} already in database, not updating...".format(genepanelName, genepanelVersion))
            return

        if config:
            config_valid(config)  # raises exception

        db_transcripts = []
        db_phenotypes = []
        transcripts = load_transcripts(transcripts_path)
        phenotypes = load_phenotypes(phenotypes_path) if phenotypes_path else None
        genes = {}
        for t in transcripts:
            db_gene, created = gm.Gene.get_or_create(
                self.session,
                hugo_symbol=t['geneSymbol'],
                ensembl_gene_id=t['eGeneID']
            )
            genes[db_gene.hugo_symbol] = db_gene
            if created:
                log.info('Gene {} created.'.format(db_gene))
            else:
                log.debug("Gene {} already in database, not creating/updating.".format(db_gene))


            db_transcript, created = gm.Transcript.get_or_create(
                self.session,
                gene=db_gene,
                refseq_name=t['refseq'],
                ensembl_id=t['eTranscriptID'],
                genome_reference=genomeRef,
                defaults={
                    'chromosome': t['chromosome'],
                    'tx_start': t['txStart'],
                    'tx_end': t['txEnd'],
                    'strand': t['strand'],
                    'cds_start': t['cdsStart'],
                    'cds_end': t['cdsEnd'],
                    'exon_starts': t['exonsStarts'],
                    'exon_ends': t['exonEnds']
                }
            )
            if created:
                log.info("Transcript {} created".format(db_transcript))
            else:
                log.debug("Transcript {} already in database, not creating/updating.".format(db_transcript))
            db_transcripts.append(db_transcript)

        if phenotypes:
            for ph in phenotypes:
                # TODO: remove all phenotypes for the panel, we'll reinsert all
                if ph['gene symbol'] not in genes:
                    raise Exception("Cannot add phenotype '{}' for panel {}, the gene {} wasn't found in database"
                                    .format(ph.description, genepanelName, ph.geneSymbol))
                db_phenotype, created = gm.Phenotype.update_or_create(
                    self.session,
                    genepanel_name=genepanelName,
                    genepanel_version=genepanelVersion,
                    gene_id=ph['gene symbol'],
                    gene=genes[ph['gene symbol']],  # TODO: not relevant for INSERT ?
                    description=ph['phenotype'],
                    inheritance=ph['inheritance'],
                    inheritance_info=ph.get('inheritance info'),
                    omim_id=ph.get('omim_number'),
                    pmid=ph.get('pmid'),
                    comment=ph.get('comment')
                )
                log.info("{} phenotype '{}'".format("Created" if created else "Updated", ph['phenotype']))

                db_phenotypes.append(db_phenotype)

        genepanel = gm.Genepanel(
            name=genepanelName,
            version=genepanelVersion,
            genome_reference=genomeRef,
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
    return dg.add_genepanel(args.transcriptsPath, None, genepanelName, genepanelVersion, genomeRef=args.genomeRef, config=None, force_yes=args.force)


if __name__ == "__main__":
    sys.exit(main())

