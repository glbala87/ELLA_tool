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
from vardb.datamodel import DB
from vardb.datamodel import gene as gm

log = logging.getLogger(__name__)


def load_phenotypes(phenotypes_path):
    if not phenotypes_path:
        return None
    with open(os.path.abspath(os.path.normpath(phenotypes_path))) as f:
        phenotypes = []
        header = None
        for line in f:
            if line.startswith('gene symbol') or line.startswith('#gene symbol'):
                if line.startswith('#gene symbol'):
                    line = line.replace('#gene', 'gene')
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


def load_config(config_path):
    if not config_path:
        return None
    with open(os.path.abspath(os.path.normpath(config_path))) as f:
        config = json.load(f)
        config_valid(config['config'])
        return config['config']


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
    name_of_schema_file = '../datamodel/genap-genepanel-config-schema.json'
    abs_filename = os.path.join(os.path.dirname(__file__), name_of_schema_file)

    with open(abs_filename) as schema_file:
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
                      configPath=None,
                      replace=False):

        existing_panel = None
        if self.session.query(gm.Genepanel).filter(
            gm.Genepanel.name == genepanelName,
            gm.Genepanel.version == genepanelVersion
        ).count():
            existing_panel = self.session.query(gm.Genepanel).filter(
                gm.Genepanel.name == genepanelName,
                gm.Genepanel.version == genepanelVersion).one()
            if replace:
                log.info("Genepanel {} {} exists in database, will overwrite.".format(genepanelName, genepanelVersion))
            else:
                log.info("Genepanel {} {} exists in database, backing out. Use the 'replace' to force overwrite."
                         .format(genepanelName, genepanelVersion))
                return

        db_transcripts = []
        db_phenotypes = []
        transcripts = load_transcripts(transcripts_path) if transcripts_path else None
        phenotypes = load_phenotypes(phenotypes_path) if phenotypes_path else None
        config = load_config(configPath) if configPath else None

        if transcripts:
            genes = {}
            for transcript in transcripts:
                db_gene, created = gm.Gene.get_or_create(
                    self.session,
                    hugo_symbol=transcript['geneSymbol'],
                    ensembl_gene_id=transcript['eGeneID']
                )

                genes[db_gene.hugo_symbol] = db_gene
                if created:
                    log.info('Gene {} created.'.format(db_gene))
                else:
                    log.info("Gene {} already in database, not creating/updating.".format(db_gene))

                db_transcript, created = self.do_transcript(db_gene, genomeRef, transcript, replace)

                if created:
                    log.info("Transcript {} created".format(db_transcript))
                else:
                    log.info("Transcript {} already in database, {}.".format(db_transcript, "updated" if replace else "not created"))
                db_transcripts.append(db_transcript)

        if phenotypes:
            # get the genes:
            genes = {}
            db_genes = self.session.query(gm.Gene)
            for db_gene in db_genes:
                genes[db_gene.hugo_symbol] = db_gene

            if replace: # remove all phenotypes
                count = self.session.query(gm.Phenotype)\
                    .filter(gm.Phenotype.genepanel_name == genepanelName,
                            gm.Phenotype.genepanel_version == genepanelVersion)\
                    .delete()
                log.info("Removed {} phenotypes from {} {}".format(count, genepanelName, genepanelVersion))

            for ph in phenotypes:
                if ph['gene symbol'] not in genes:
                    raise Exception("Cannot add phenotype '{}' for panel {}, the gene {} wasn't found in database"
                                    .format(ph['phenotype'], genepanelName, ph['gene symbol']))

                # always create new:
                db_phenotype, created,  = self.do_phenotype(genepanelName,
                                                            genepanelVersion,
                                                            genes[ph['gene symbol']],
                                                            ph)
                if 'omim_gene_entry' in ph:
                    genes[ph['gene symbol']]['omim_gene_entry'] = ph['omim_gene_entry']

                log.info("{} phenotype '{}'".format("Created" if created else "Loaded", ph['phenotype']))

                db_phenotypes.append(db_phenotype)

        if existing_panel:
            if len(db_transcripts) > 0:
                existing_panel.transcripts =  db_transcripts
            if len(db_phenotypes) > 0:
                existing_panel.phenotypes = db_phenotypes
            if config:
                existing_panel.config = config

        else:
            # new panel
            genepanel = gm.Genepanel(
                name=genepanelName,
                version=genepanelVersion,
                genome_reference=genomeRef,
                transcripts=db_transcripts if len(db_transcripts) > 0 else [],
                phenotypes=db_phenotypes if len(db_phenotypes) > 0 else [],
                config=config)
            self.session.merge(genepanel)

        self.session.commit()
        log.info('Added {} {} with {} transcripts and {} phenotypes to database'
                 .format(genepanelName, genepanelVersion, len(db_transcripts), len(db_phenotypes)))
        return 0

    def do_phenotype(self, genepanelName, genepanelVersion, gene, ph):
        return gm.Phenotype.get_or_create(  # phenotypes are never updated
            self.session,
            genepanel_name=genepanelName,
            genepanel_version=genepanelVersion,
            gene=gene,
            description=ph['phenotype'],
            inheritance=ph['inheritance'],
            inheritance_info=ph.get('inheritance info'),
            omim_id=ph.get('omim_number'),
            pmid=ph.get('pmid'),
            comment=ph.get('comment')
        )

    def do_transcript(self, db_gene, genomeRef, t, replace):
        if replace:
            return gm.Transcript.update_or_create(
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
        else:
            return gm.Transcript.get_or_create(
                self.session,
                defaults={
                    'chromosome': t['chromosome'],
                    'tx_start': t['txStart'],
                    'tx_end': t['txEnd'],
                    'strand': t['strand'],
                    'cds_start': t['cdsStart'],
                    'cds_end': t['cdsEnd'],
                    'exon_starts': t['exonsStarts'],
                    'exon_ends': t['exonEnds']
                },
                gene=db_gene,
                refseq_name=t['refseq'],
                ensembl_id=t['eTranscriptID'],
                genome_reference=genomeRef
            )


def main(argv=None):
    """Example: ./deposit_genepanel.py --transcripts=./clinicalGenePanels/HBOC/HBOC.transcripts.csv"""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="""Adds or updates gene panels in varDB.
                       Use any or all of --transcripts/phenotypes/config.
                       If the panel exists you must add the --replace option.\n
                       When creating a new panel, use -transcripts and --phenotypes without --replace""")
    parser.add_argument("--transcripts", action="store", dest="transcriptsPath",
                        required=False, default=None,
                        help="Path to gene panel transcripts file")
    parser.add_argument("--phenotypes", action="store", dest="phenotypesPath",
                        required=False, default=None,
                        help="Path to gene panel phenotypes file")
    parser.add_argument("--config", action="store", dest="configPath",
                        required=False, default=None,
                        help="Path to gene panel config file")
    parser.add_argument("--genepanelname", action="store", dest="genepanelName",
                        required=True, help="Name for gene panel")
    parser.add_argument("--genepanelversion", action="store", dest="genepanelVersion",
                        required=True, help="Version of this gene panel")
    parser.add_argument("--genomeref", action="store", dest="genomeRef",
                        required=False, default="GRCh37",
                        help="Genomic reference sequence name")
    parser.add_argument("--replace", action="store_true", dest="replace",
                        required=False, default=False,
                        help="Overwrite existing data in database")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)

    genepanelName = args.genepanelName
    genepanelVersion = args.genepanelVersion
    assert genepanelVersion.startswith('v')

    db = DB()
    db.connect()

    dg = DepositGenepanel(db.session)
    return dg.add_genepanel(args.transcriptsPath,
                            args.phenotypesPath,
                            genepanelName,
                            genepanelVersion,
                            genomeRef=args.genomeRef,
                            configPath=args.configPath,
                            replace=args.replace)


if __name__ == "__main__":
    sys.exit(main())

