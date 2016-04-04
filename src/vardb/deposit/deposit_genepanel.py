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
from regions import transcript as tm
from regions import phenotype as ph

log = logging.getLogger(__name__)


class DepositGenepanel(object):

    def __init__(self, session):
        self.session = session

    def load_transcripts(self, transcripts_path):
        with open(os.path.abspath(os.path.normpath(transcripts_path))) as f:
            return tm.load_transcripts_from_genepanel_file(f)

    def load_phenotypes(self, phenotypes_path):
        with open(os.path.abspath(os.path.normpath(phenotypes_path))) as f:
            return ph.load_phenotypes_from_genepanel_file(f)

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
        transcripts = self.load_transcripts(transcripts_path)
        phenotypes = self.load_phenotypes(phenotypes_path) if phenotypes_path else None
        genes = {}
        for t in transcripts:
            gene, created = gm.Gene.update_or_create(
                self.session,
                hugoSymbol=t.geneSymbol,
                ensemblGeneID=t.eGene,
                defaults={'dominance': t.inheritance}
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
                gene = None
                print "ph.geneSymbol" + ph.geneSymbol
                # db_phenotype = gm.Phenotype(
                #     gene_id=ph.geneSymbol,
                #     gene=gene,  # TODO: not relevant for INSERT ?
                #     description='hardcoded',
                #     dominance='dom'
                # )
                db_phenotype, created = gm.Phenotype.update_or_create(
                    self.session,
                    genepanelName=genepanelName,
                    genepanelVersion=genepanelVersion,
                    gene_id=ph.geneSymbol,
                    gene=genes[ph.geneSymbol],  # TODO: not relevant for INSERT ?
                    description='hardcoded',
                    dominance='dom'
                )
                db_phenotypes.append(db_phenotype)

        genepanel = gm.Genepanel(
            name=genepanelName,
            version=genepanelVersion,
            genomeReference=genomeRef,
            transcripts=db_transcripts,
            phenotypes=db_phenotypes)
        print db_transcript
        print db_phenotypes
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
