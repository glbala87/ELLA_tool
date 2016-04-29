#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import os
import sys
import argparse
import logging

import vardb.datamodel
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


class DepositGenepanel(object):

    def __init__(self, session):
        self.session = session

    def add_genepanel(self, transcripts_path, phenotypes_path, genepanelName, genepanelVersion, genomeRef='GRCh37', force_yes=False):
        if self.session.query(gm.Genepanel).filter(gm.Genepanel.name == genepanelName,
                                                   gm.Genepanel.version == genepanelVersion).count():
            log.warning("{} {} already in database".format(genepanelName, genepanelVersion))
            if not force_yes and not raw_input("Update this genepanel (Y/n)?") == 'Y':
                log.warning("Aborting and rolling back")
                self.session.rollback()
                return -1

        db_transcripts = []
        db_phenotypes = []
        transcripts = load_transcripts(transcripts_path)
        phenotypes = load_phenotypes(phenotypes_path) if phenotypes_path else None
        genes = {}
        for t in transcripts:
            gene, created = gm.Gene.update_or_create(
                self.session,
                hugoSymbol=t['geneSymbol'],
                ensemblGeneID=t['eGeneID']
            )
            genes[gene.hugoSymbol] = gene
            if not created:
                log.info('Updated gene {}'.format(gene))

            db_transcript, created = gm.Transcript.update_or_create(
                self.session,
                gene=gene,
                refseqName=t['refseq'],
                ensemblID=t['eTranscriptID'],
                genomeReference=genomeRef,
                # Could wrap the rest in defaults{} for updating
                chromosome=t['chromosome'],
                txStart=t['txStart'],
                txEnd=t['txEnd'],
                strand=t['strand'],
                cdsStart=t['cdsStart'],
                cdsEnd=t['cdsEnd'],
                exonStarts=t['exonsStarts'],
                exonEnds=t['exonEnds']
            )
            db_transcripts.append(db_transcript)

            if not created:
                log.info('Updated transcript {}'.format(db_transcript))

        if phenotypes:
            for ph in phenotypes:
                # TODO: remove all phenotypes for the panel, we'll reinsert all
                if ph['gene symbol'] not in genes:
                    raise Exception("Cannot add phenotype '{}' for panel {}, the gene {} wasn't found in database"
                    .format(ph['phenotype'], genepanelName, ph['gene symbol']))
                db_phenotype, created = gm.Phenotype.update_or_create(
                    self.session,
                    genepanelName=genepanelName,
                    genepanelVersion=genepanelVersion,
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
            genomeReference=genomeRef,
            transcripts=db_transcripts,
            phenotypes=db_phenotypes)
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

