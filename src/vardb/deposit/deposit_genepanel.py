#!/usr/bin/env python
"""
Code for adding or modifying gene panels in varDB.
"""

import os
import sys
import argparse
import logging
import json
from sqlalchemy import tuple_, and_
from vardb.datamodel import DB
from vardb.datamodel import gene as gm
from vardb.deposit.genepanel_config_validation import config_valid

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
            data['HGNC'] = int(data['HGNC'])
            data['txStart'], data['txEnd'], = int(data['txStart']), int(data['txEnd'])
            data['cdsStart'], data['cdsEnd'] = int(data['cdsStart']), int(data['cdsEnd'])
            data['exonsStarts'] = map(int, data['exonsStarts'].split(','))
            data['exonEnds'] = map(int, data['exonEnds'].split(','))
            transcripts.append(data)
        return transcripts


def batch(iterable, n):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def bulk_insert_nonexisting(session, model, rows, include_pk=None, compare_keys=None, replace=False, batch_size=1000):
    """
    Inserts data in bulk according to batch_size.

    :param model: Model to insert data into
    :type model: SQLAlchemy model
    :param rows: List of dict with data. Keys must correspond to attributes on model
    :param include_pk: Key for which to get primary key for created and existing objects.
                       Slows down performance by a lot, since we must query for the keys.
    :type include_pk: str
    :param compare_keys: Keys to be used for comparing whether an object exists already.
                         If none is provided, all keys from rows[0] will be used.
    :type compare_keys: List
    :param replace: Whether to replace (update) existing data. Requires include_pk and compare_keys.
    :param batch_size: Size of each batch that should be inserted into database. Affects memory usage.
    :yields: Type of (existing_objects, created_objects), each entry being a list of dictionaries.
             If include_pk is set, a third list is returned containing all the primary keys for the input rows.
    """

    if replace and compare_keys is None:
        raise RuntimeError("Using replace=True with no supplied compare_keys makes no sense, as there can be no data to replace.")
    if replace and not include_pk:
        raise RuntimeError("You must supply include_pk argument when replace=True.")

    if compare_keys is None:
        compare_keys = rows[0].keys()

    def get_fields_filter(model, rows, compare_keys):
        batch_values = [[b[k] for k in compare_keys] for b in rows]
        q_fields = [getattr(model, k) for k in compare_keys]
        q_filter = tuple_(*q_fields).in_(batch_values)
        return q_fields, q_filter

    for batch_rows in batch(rows, batch_size):

        q_fields, q_filter = get_fields_filter(model, batch_rows, compare_keys)
        if include_pk:
            q_fields.append(getattr(model, include_pk))

        db_existing = session.query(*q_fields).filter(q_filter).all()
        db_existing = [r._asdict() for r in db_existing]
        created = list()
        input_existing = list()

        if db_existing:
            # Filter our batch_rows based on existing in db to see which objects we need to insert
            for row in batch_rows:
                should_create = True
                for e in db_existing:
                    if all(e[k] == row[k] for k in compare_keys):
                        if include_pk:  # Copy over primary key if applicable
                            row[include_pk] = e[include_pk]
                        input_existing.append(row)
                        should_create = False
                if should_create:
                    created.append(row)
        else:
            created = batch_rows
        if replace and input_existing:
            # Reinsert all existing data
            log.debug("Replacing {} objects on {}".format(len(input_existing), str(model)))
            session.bulk_update_mappings(model, input_existing)

        session.bulk_insert_mappings(model, created)

        if include_pk:
            pks = session.query(getattr(model, include_pk)).filter(q_filter).all()
            assert len(pks) == len(created) + len(input_existing)
            yield input_existing, created, pks
        else:
            yield input_existing, created


class DepositGenepanel(object):

    def __init__(self, session):
        self.session = session

    def insert_genes(self, transcript_data):

        # Avoid duplicate genes
        distinct_genes = set()
        for t in transcript_data:
            distinct_genes.add((
                t['HGNC'],
                t['geneSymbol'],
                t['eGeneID'],
                int(t['Omim gene entry']) if t.get('Omim gene entry') else None
            ))

        gene_rows = list()
        for d in list(distinct_genes):
            gene_rows.append({
                'hgnc_id': d[0],
                'hgnc_symbol': d[1],
                'ensembl_gene_id': d[2],
                'omim_entry_id': d[3]
            })

        gene_inserted_count = 0
        gene_reused_count = 0
        for existing, created in bulk_insert_nonexisting(self.session,
                                                         gm.Gene,
                                                         gene_rows,
                                                         compare_keys=['hgnc_id', 'hgnc_symbol', 'ensembl_gene_id']):
            gene_inserted_count += len(created)
            gene_reused_count += len(existing)
        return gene_inserted_count, gene_reused_count

    def insert_transcripts(self, transcript_data, genepanel_name, genepanel_version, genome_ref, replace=False):
        transcript_rows = list()
        for t in transcript_data:
            transcript_rows.append({
                'gene_id': t['HGNC'],  # foreign key to gene
                'transcript_name': t['refseq'],  # TODO: Support other than RefSeq
                'type': 'RefSeq',
                'corresponding_refseq': None,
                'corresponding_ensembl': t['eTranscriptID'],
                'corresponding_lrg': None,
                'ensembl_id': t['eTranscriptID'],
                'chromosome': t['chromosome'],
                'tx_start': t['txStart'],
                'tx_end': t['txEnd'],
                'strand': t['strand'],
                'cds_start': t['cdsStart'],
                'cds_end': t['cdsEnd'],
                'exon_starts': t['exonsStarts'],
                'exon_ends': t['exonEnds'],
                'genome_reference': genome_ref
            })

        transcript_inserted_count = 0
        transcript_reused_count = 0

        # If replacing, delete old connections in junction table
        if replace:
            log.debug("Replacing transcripts connected to genepanel.")
            self.session.execute(gm.genepanel_transcript.delete().where(
                and_(
                    gm.genepanel_transcript.columns.genepanel_name == genepanel_name,
                    gm.genepanel_transcript.columns.genepanel_version == genepanel_version
                )
            ))

        for existing, created, pks in bulk_insert_nonexisting(self.session,
                                                              gm.Transcript,
                                                              transcript_rows,
                                                              include_pk='id',
                                                              compare_keys=['transcript_name'],
                                                              replace=replace):
            transcript_inserted_count += len(created)
            transcript_reused_count += len(existing)

            # Connect to genepanel by inserting into the junction table
            junction_values = list()
            for pk in pks:
                junction_values.append({
                    'genepanel_name': genepanel_name,
                    'genepanel_version': genepanel_version,
                    'transcript_id': pk
                })
            self.session.execute(gm.genepanel_transcript.insert(), junction_values)

        return transcript_inserted_count, transcript_reused_count

    def insert_phenotypes(self, phenotype_data, genepanel_name, genepanel_version, replace=False):

        if replace:
            # Phenotypes can be replaced in their entirety, since they're not shared.
            count = self.session.query(gm.Phenotype).filter(
                gm.Phenotype.genepanel_name == genepanel_name,
                gm.Phenotype.genepanel_version == genepanel_version
            ).delete()
            log.debug("Removed {} phenotypes from {} {}".format(count, genepanel_name, genepanel_version))

        phenotype_rows = list()
        phenotype_inserted_count = 0
        phenotype_reused_count = 0
        for ph in phenotype_data:
            if not ph.get('HGNC'):
                log.warning('Skipping phenotype {} since HGNC is empty'.format(ph.get('phenotype')))
                continue
            phenotype_rows.append({
                'genepanel_name': genepanel_name,
                'genepanel_version': genepanel_version,
                'gene_id': int(ph['HGNC']),
                'description': ph['phenotype'],
                'inheritance': ph['inheritance'],
                'inheritance_info': ph.get('inheritance info'),
                'omim_id': int(ph['omim_number']) if ph.get('omim_number') else None,
                'pmid': int(ph['pmid']) if ph.get('pmid') else None,
                'comment': ph.get('comment')
            })

        for existing, created in bulk_insert_nonexisting(self.session, gm.Phenotype, phenotype_rows):
            phenotype_inserted_count += len(created)
            phenotype_reused_count += len(existing)

        return phenotype_inserted_count, phenotype_reused_count

    def add_genepanel(self,
                      transcripts_path,
                      phenotypes_path,
                      genepanel_name,
                      genepanel_version,
                      genomeRef='GRCh37',
                      configPath=None,
                      replace=False):

        if not transcripts_path:
            raise RuntimeError("Missing mandatory argument: path to transcript file")
        if not phenotypes_path:
            raise RuntimeError("Missing mandatory argument: path to phenotypes file")

        # Insert genepanel
        config = load_config(configPath) if configPath else None
        existing_panel = self.session.query(gm.Genepanel).filter(
            gm.Genepanel.name == genepanel_name,
            gm.Genepanel.version == genepanel_version
        ).one_or_none()

        if not existing_panel:
            # We connect transcripts and phenotypes to genepanel later
            genepanel = gm.Genepanel(
                name=genepanel_name,
                version=genepanel_version,
                genome_reference=genomeRef,
                config=config
            )
            self.session.add(genepanel)

        else:
            if replace:
                log.info("Genepanel {} {} exists in database, will overwrite.".format(genepanel_name, genepanel_version))
                existing_panel.config = config
                existing_panel.genome_reference = genomeRef
            else:
                log.info("Genepanel {} {} exists in database, backing out. Use the 'replace' to force overwrite."
                         .format(genepanel_name, genepanel_version))
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
        log.info('GENES: Created {}, reused {}'.format(gene_inserted_count, gene_reused_count))

        # Transcripts
        transcript_inserted_count, transcript_reused_count = self.insert_transcripts(
            transcript_data,
            genepanel_name,
            genepanel_version,
            genomeRef,
            replace=replace
        )

        log.info('TRANSCRIPTS: Created {}, reused {}'.format(transcript_inserted_count, transcript_reused_count))

        # Phenotypes
        phenotype_inserted_count, phenotype_reused_count = self.insert_phenotypes(
            phenotype_data,
            genepanel_name,
            genepanel_version,
            replace=replace
        )

        log.info('PHENOTYPES: Created {}, reused {}'.format(phenotype_inserted_count, phenotype_reused_count))

        self.session.commit()
        log.info(
            'Added {} {} with {} genes, {} transcripts and {} phenotypes to database'.format(
                genepanel_name,
                genepanel_version,
                gene_inserted_count + gene_reused_count,
                transcript_inserted_count + transcript_reused_count,
                phenotype_inserted_count + phenotype_reused_count
            )
        )
        return 0


def main(argv=None):
    """Example: ./deposit_genepanel.py --transcripts=./clinicalGenePanels/HBOC/HBOC.transcripts.csv"""
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="""Adds or updates gene panels in varDB.
                       Use any or all of --transcripts/phenotypes/config.
                       If the panel exists you must add the --replace option.\n
                       When creating a new panel, use -transcripts and --phenotypes without --replace""")
    parser.add_argument("--transcripts", action="store", dest="transcriptsPath",
                        required=True, help="Path to gene panel transcripts file")
    parser.add_argument("--phenotypes", action="store", dest="phenotypesPath",
                        required=True, help="Path to gene panel phenotypes file")
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

    genepanel_name = args.genepanelName
    genepanel_version = args.genepanelVersion
    assert genepanel_version.startswith('v')

    db = DB()
    db.connect()

    dg = DepositGenepanel(db.session)
    return dg.add_genepanel(args.transcriptsPath,
                            args.phenotypesPath,
                            genepanel_name,
                            genepanel_version,
                            genomeRef=args.genomeRef,
                            configPath=args.configPath,
                            replace=args.replace)


if __name__ == "__main__":
    sys.exit(main())

