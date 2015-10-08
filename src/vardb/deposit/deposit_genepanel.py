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
from vardb.deposit.regions import transcript as tm


def add_genepanel(session, transcripts, genepanelName, genepanelVersion, genomeRef):
    if session.query(gm.Genepanel).filter(gm.Genepanel.name == genepanelName,
                                          gm.Genepanel.version == genepanelVersion).count():
        logging.warning("{} {} already in database".format(genepanelName, genepanelVersion))
        if not raw_input("Update this genepanel (Y/n)?") == 'Y':
            logging.warning("Aborting and rolling back")
            session.rollback()
            return -1

    continue_input = ''
    db_transcripts = []
    for t in transcripts:
        gene, created = gm.Gene.update_or_create(
            session,
            hugoSymbol=t.geneSymbol,
            ensemblGeneID=t.eGene,
            defaults={'dominance':t.inheritance}
        )
        if not created:
            logging.info('Updated gene {}'.format(gene))

        db_transcript = session.query(gm.Transcript).filter(
                gm.Transcript.refseqName == t.refseq).first()
        if db_transcript:
            logging.warning('An {} transcript is already in database! Will not add/update this.'.format(t.refseq))
            if not continue_input == 'A':
                continue_input = raw_input('Continue anyway? [Y] Yes, [A] Yes to All, [n] No) ?')
            if not continue_input in ['Y', 'A']:
                logging.warning('Aborting and rolling back.')
                session.rollback()
                return -1
        else:
            db_transcript, _ = gm.Transcript.update_or_create(
                session,
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
    session.merge(genepanel)
    session.commit()
    logging.info('Added {} version {} to database'.format(genepanelName, genepanelVersion))
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
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)
    genepanelName = args.genepanelName if args.genepanelName is not None else os.path.split(args.transcriptsPath)[1].split('_')[0]
    genepanelVersion = args.genepanelVersion if args.genepanelVersion is not None else os.path.split(args.transcriptsPath)[1].split('_')[3]
    print genepanelVersion
    assert genepanelVersion.startswith('v')
    with open(os.path.abspath(os.path.normpath(args.transcriptsPath))) as f:
        transcripts = tm.load_transcripts_from_genepanel_file(f)

    session = vardb.datamodel.Session()
    return add_genepanel(session, transcripts, genepanelName, genepanelVersion, args.genomeRef)


if __name__ == "__main__":
    sys.exit(main())
