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

log = logging.getLogger(__name__)


class DepositGenepanel(object):

    def __init__(self):
        self.session = vardb.datamodel.Session()

    def load_transcripts(self, transcripts_path):
        with open(os.path.abspath(os.path.normpath(transcripts_path))) as f:
            return tm.load_transcripts_from_genepanel_file(f)

    def add_genepanel(self, transcripts_path, genepanelName, genepanelVersion, genomeRef='GRCh37', force_yes=False):
        if self.session.query(gm.Genepanel).filter(gm.Genepanel.name == genepanelName,
                                                   gm.Genepanel.version == genepanelVersion).count():
            log.warning("{} {} already in database".format(genepanelName, genepanelVersion))
            if not force_yes and not raw_input("Update this genepanel (Y/n)?") == 'Y':
                log.warning("Aborting and rolling back")
                self.session.rollback()
                return -1

        continue_input = ''
        db_transcripts = []
        transcripts = self.load_transcripts(transcripts_path)
        for t in transcripts:
            gene, created = gm.Gene.update_or_create(
                self.session,
                hugoSymbol=t.geneSymbol,
                ensemblGeneID=t.eGene,
                defaults={'dominance': t.inheritance}
            )
            if not created:
                log.info('Updated gene {}'.format(gene))

            db_transcript = self.session.query(gm.Transcript).filter(
                gm.Transcript.refseqName == t.refseq
            ).first()
            if db_transcript:
                log.warning('An {} transcript is already in database! Will not add/update this.'.format(t.refseq))
                if not force_yes and not continue_input == 'A':
                    continue_input = raw_input('Continue anyway? [Y] Yes, [A] Yes to All, [n] No) ?')
                if not force_yes and continue_input not in ['Y', 'A']:
                    log.warning('Aborting and rolling back.')
                    self.session.rollback()
                    return -1
            else:
                db_transcript, _ = gm.Transcript.update_or_create(
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

        genepanel = gm.Genepanel(
            name=genepanelName,
            version=genepanelVersion,
            genomeReference=genomeRef,
            transcripts=db_transcripts)
        self.session.merge(genepanel)
        self.session.commit()
        log.info('Added {} version {} to database'.format(genepanelName, genepanelVersion))
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
    return dg.add_genepanel(args.transcriptsPath, genepanelName, genepanelVersion, genomeRef=args.genomeRef, force_yes=args.force)


if __name__ == "__main__":
    sys.exit(main())
