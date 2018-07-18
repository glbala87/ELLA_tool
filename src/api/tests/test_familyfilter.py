from collections import defaultdict
import pytest
import uuid

from hypothesis import given, example, settings, reproduce_failure
import hypothesis.strategies as st

from sqlalchemy import Table, Column, Boolean, Integer, Enum
from sqlalchemy.schema import CreateTable
from vardb.datamodel import allele, annotation, gene, annotationshadow, Base
from api.allelefilter.familyfilter import FamilyFilter, PAR1_START, PAR1_END, PAR2_START, PAR2_END


GLOBAL_CONFIG = {
    'transcripts': {
        'inclusion_regex': "NM_.*"
    }
}

allele_strategy = st.sampled_from([
    (10001, 'X', PAR1_START-2, PAR1_START-1),
    (10001, 'X', PAR1_START-1, PAR1_START),
    (10001, 'X', PAR1_START, PAR1_START+1),
    (10001, 'X', PAR1_START+1, PAR1_START+2),
    (10001, 'X', PAR1_START+2, PAR1_START+3),
    (10001, 'X', PAR1_END-2, PAR1_END-1),
    (10001, 'X', PAR1_END-1, PAR1_END),
    (10001, 'X', PAR1_END, PAR1_END+1),
    (10001, 'X', PAR1_END+1, PAR1_END+2),
    (10001, 'X', PAR1_END+2, PAR1_END+3),
    (10001, 'X', PAR2_START-2, PAR2_START-1),
    (10001, 'X', PAR2_START-1, PAR2_START),
    (10001, 'X', PAR2_START, PAR2_START+1),
    (10001, 'X', PAR2_START+1, PAR2_START+2),
    (10001, 'X', PAR2_START+2, PAR2_START+3),
    (10001, 'X', PAR2_END-2, PAR2_END-1),
    (10001, 'X', PAR2_END-1, PAR2_END),
    (10001, 'X', PAR2_END, PAR2_END+1),
    (10001, 'X', PAR2_END+1, PAR2_END+2),
    (10001, 'X', PAR2_END+2, PAR2_END+3),
    (10001, '1', 1, 1),  # Not in X
])


genotype_strategy = st.sampled_from(['Homozygous', 'Heterozygous', 'Reference', 'No coverage', None])
sex_strategy = st.sampled_from(['Male', 'Female'])
gene_strategy = st.sampled_from(['GENE1', 'GENE2'])


@st.composite
def compound_recessive_strategy(draw):
    entries = []
    for allele_count in xrange(draw(st.integers(min_value=1, max_value=5))):
        entries.append({
            'gene': draw(gene_strategy),
            'genotypes': (draw(genotype_strategy), draw(genotype_strategy), draw(genotype_strategy))
        })

    return entries


def x_minus_par(chrom, start_position, open_end_position):
    x_minus_par = False
    if (chrom == 'X'):
        if open_end_position <= PAR1_START:  # end < start
            x_minus_par = True
        elif start_position > PAR1_END and open_end_position <= PAR2_START:
            x_minus_par = True
        elif start_position > PAR2_END:
            x_minus_par = True
    return x_minus_par


def create_genotype_table(session, samples, entries):
    type = Enum("Homozygous", "Heterozygous", "Reference", "No coverage", name="genotypemetadata_genotype")
    sex = Enum("Male", "Female", name="sample_sex")
    sample_columns = []
    for s in samples:
        sample_columns.extend([
            Column(s[0] + '_type', type),
            Column(s[0] + '_sex', sex)
        ])

    genotype_table_definition = Table(
        str(uuid.uuid4()),
        Base.metadata,
        Column('allele_id', Integer),
        *sample_columns
    )

    rows = []
    for e in entries:
        row = [e[0]]
        for idx, s in enumerate(samples):
            row.extend([e[idx + 1], s[1]])  # e.g. ['Homozygous', 'Male']
        rows.append(row)

    session.execute('DROP TABLE IF EXISTS genotype_test_table')
    session.execute(CreateTable(genotype_table_definition))
    session.execute(genotype_table_definition.insert().values(rows))
    return session.query(genotype_table_definition)


def replace_allele_table(session, entries):
    allele_ids = [a[0] for a in entries]
    session.execute('DELETE FROM allele WHERE id IN ({})'.format(','.join([str(i) for i in allele_ids])))
    for entry in entries:
        allele_id, chromosome, start_position, open_end_position = entry
        data = {
            'id': allele_id,
            'chromosome': chromosome,
            'start_position': start_position,
            'open_end_position': open_end_position,
            'genome_reference': 'GRCh37',
            'vcf_pos': start_position,
            'vcf_ref': 'DUMMY',
            'vcf_alt': 'DUMMY',
            'change_from': 'DUMMY',
            'change_to': 'DUMMY',
            'change_type': 'SNP'
        }
        al = allele.Allele(**data)
        session.add(al)
    session.flush()


def replace_annotationshadowtranscript_table(session, entries):
    ids = [a[0] for a in entries]
    session.execute('DELETE FROM annotationshadowtranscript WHERE id IN ({})'.format(','.join([str(i) for i in ids])))
    for entry in entries:
        id, allele_id, symbol = entry
        data = {
            'id': id,
            'allele_id': allele_id,
            'hgnc_id': 0,
            'symbol': symbol,
            'transcript': 'NM_DUMMY',
            'hgvsc': 'DUMMY',
            'protein': 'DUMMY',
            'hgvsp': 'DUMMY',
            'consequences': ['DUMMY'],
            'exon_distance': 0,
            'coding_region_distance': 0,
        }
        ast = annotationshadow.AnnotationShadowTranscript(**data)
        session.add(ast)
    session.flush()


class TestInheritanceFilter(object):

    @pytest.mark.i(order=0)
    def test_reset_database(self, test_database):
        test_database.refresh()

    # All denovo positive cases
    @example((10001, '1', 1, 2), 'Male', ('Heterozygous', 'Reference', 'Reference'))  # AD denovo
    @example((10001, '1', 1, 2), 'Male', ('Homozygous', 'Reference', 'Reference'))  # AD denovo
    @example((10001, '1', 1, 2), 'Male', ('Homozygous', 'Reference', 'Heterozygous'))  # AD denovo
    @example((10001, '1', 1, 2), 'Male', ('Homozygous', 'Heterozygous', 'Reference'))  # AD denovo
    @example((10001, 'X', PAR1_START-1, PAR1_START), 'Female', ('Heterozygous', 'Reference', 'Reference'))  # X-linked female
    @example((10001, 'X', PAR1_START-1, PAR1_START), 'Female', ('Homozygous', 'Reference', 'Reference'))  # X-linked female
    @example((10001, 'X', PAR1_START-1, PAR1_START), 'Female', ('Homozygous', 'Reference', 'Heterozygous'))  # X-linked female
    @example((10001, 'X', PAR1_START-1, PAR1_START), 'Male', ('Homozygous', 'Reference', 'Reference'))  # X-linked male
    # Denovo negative examples
    @example((10001, 'X', PAR1_START, PAR1_START+1), 'Male', ('Homozygous', 'Reference', 'Reference'))
    @example((10001, 'X', PAR1_START-1, PAR1_START), 'Male', ('Heterozygous', 'Reference', 'Reference'))
    @example((10001, 'X', PAR1_START-1, PAR1_START), 'Male', ('Homozygous', 'Reference', 'Heterozygous'))
    @example((10001, '1', 1, 2), 'Male', ('Homozygous', 'Heterozygous', 'No coverage'))
    @example((10001, '1', 1, 2), 'Male', ('Homozygous', 'Heterozygous', 'Heterozygous'))
    @example((10001, '1', 1, 2), 'Male', ('Homozygous', 'Homozygous', 'Heterozygous'))
    @example((10001, '1', 1, 2), 'Male', ('Homozygous', 'No coverage', 'Heterozygous'))
    @example((10001, '1', 1, 2), 'Male', ('Homozygous', 'No coverage', 'Heterozygous'))
    @given(
        allele_strategy,
        sex_strategy,
        st.tuples(genotype_strategy, genotype_strategy, genotype_strategy)
    )
    @settings(deadline=None)
    def test_denovo(self, session, allele_data, proband_sex, genotypes):
        # Hypothesis reuses session, make sure it's rolled back

        session.rollback()

        allele_id, chrom, start_position, open_end_position = allele_data
        is_x_minus_par = x_minus_par(chrom, start_position, open_end_position)

        replace_allele_table(session, [allele_data])
        samples = [('Proband', proband_sex), ('Father', 'Male'), ('Mother', 'Female')]

        genotype_table = create_genotype_table(session, samples, [(allele_id,) + genotypes])

        result_allele_ids = FamilyFilter(session, GLOBAL_CONFIG).denovo(genotype_table, 'Proband', 'Father', 'Mother')

        if any(g is None or g == 'No coverage' for g in genotypes):
            assert set(result_allele_ids) == set([])

        # Autosomal:
        # 0/0 + 0/0 = 0/1
        # 0/0 + 0/0 = 1/1
        # 0/0 + 0/1 = 1/1
        # 0/1 + 0/0 = 1/1
        autosomal_denovo_genotypes = [
            ('Heterozygous', 'Reference', 'Reference'),
            ('Homozygous', 'Reference', 'Reference'),
            ('Homozygous', 'Reference', 'Heterozygous'),
            ('Homozygous', 'Heterozygous', 'Reference')
        ]
        # X-linked, child is boy:
        # 0 + 0/0 = 1
        xlinked_boy_genotypes = [
            ('Homozygous', 'Reference', 'Reference')
        ]
        # X-linked, child is girl:
        # 0 + 0/0 = 0/1
        # 0 + 0/0 = 1/1
        # 0 + 0/1 = 1/1
        xlinked_girl_genotypes = [
            ('Heterozygous', 'Reference', 'Reference'),
            ('Homozygous', 'Reference', 'Reference'),
            ('Homozygous', 'Reference', 'Heterozygous'),
        ]
        if not is_x_minus_par:
            if genotypes in autosomal_denovo_genotypes:
                assert set(result_allele_ids) == set([allele_id])
            else:
                assert set(result_allele_ids) == set([])
        else:
            if proband_sex == 'Male':
                if genotypes in xlinked_boy_genotypes:
                    assert set(result_allele_ids) == set([allele_id])
                else:
                    assert set(result_allele_ids) == set([])
            else:
                if genotypes in xlinked_girl_genotypes:
                    assert set(result_allele_ids) == set([allele_id])
                else:
                    assert set(result_allele_ids) == set([])

    @example([
        {'gene': 'GENE1', 'genotypes': ('Homozygous', 'Heterozygous', 'Heterozygous')},
        {'gene': 'GENE1', 'genotypes': ('Heterozygous', 'Reference', 'Heterozygous')},
        {'gene': 'GENE1', 'genotypes': ('Heterozygous', 'Heterozygous', 'Reference')},
        {'gene': 'GENE2', 'genotypes': ('Homozygous', 'Heterozygous', 'Heterozygous')},
    ], [1, 2])
    @example([
        {'gene': 'GENE1', 'genotypes': ('Heterozygous', 'Heterozygous', 'Reference')},
        {'gene': 'GENE1', 'genotypes': ('Heterozygous', 'Reference', 'Heterozygous')},
        {'gene': 'GENE2', 'genotypes': ('Homozygous', 'Heterozygous', 'Heterozygous')},
    ], [0, 1])
    @example([
        {'gene': 'GENE1', 'genotypes': ('Homozygous', 'Heterozygous', 'Heterozygous')},
        {'gene': 'GENE1', 'genotypes': ('Heterozygous', 'Reference', 'Heterozygous')},
        {'gene': 'GENE2', 'genotypes': ('Heterozygous', 'Heterozygous', 'Reference')},
        {'gene': 'GENE2', 'genotypes': ('Homozygous', 'Heterozygous', 'Heterozygous')},
    ], [])
    @example([
        {'gene': 'GENE1', 'genotypes': ('Homozygous', 'Reference', 'Reference')},
        {'gene': 'GENE1', 'genotypes': ('Heterozygous', 'No coverage', 'Heterozygous')},
        {'gene': 'GENE1', 'genotypes': ('Heterozygous', 'Heterozygous', 'Reference')},
        {'gene': 'GENE2', 'genotypes': ('Homozygous', 'Heterozygous', 'Heterozygous')},
    ], [])
    @given(compound_recessive_strategy(), st.just(None))
    @settings(deadline=None)
    def test_compund_recessive(self, session, entries, manually_curated_result):
        # Hypothesis reuses session, make sure it's rolled back
        session.rollback()

        # Sex is irrelevant
        samples = [('Proband', 'Male'), ('Father', 'Male'), ('Mother', 'Female')]

        # Generate dummy alleles so we have an id to link the annotationshadowtable to
        # Positions are irrelevant
        allele_ids = list()
        allele_entries = list()
        genotype_entries = list()
        annotationshadow_entries = list()
        for idx, entry in enumerate(entries):
            allele_id = 1000 + idx
            allele_ids.append(allele_id)
            allele_entries.append((allele_id, '1', 1 + idx, 2 + idx))
            genotype_entries.append((allele_id,) + entry['genotypes'])
            annotationshadow_entries.append((1000 + idx, allele_id, entry['gene']))

        replace_allele_table(session, allele_entries)
        replace_annotationshadowtranscript_table(session, annotationshadow_entries)
        genotype_table = create_genotype_table(session, samples, genotype_entries)

        result_allele_ids = FamilyFilter(session, GLOBAL_CONFIG).recessive_compound_heterozygous(
            genotype_table,
            'Proband',
            'Father',
            'Mother'
        )

        # Manual tests
        if manually_curated_result is not None:
            matched_allele_ids = set([allele_ids[idx] for idx in manually_curated_result])
            assert result_allele_ids == matched_allele_ids
        else:
            # The rules from recessive_compound_heterozygous() can be destilled down to
            # having two or more alleles in a gene with _both_ these combinations:
            # ('Heterozygous', 'Heterozygous', 'Reference'),
            # ('Heterozygous', 'Reference', 'Heterozygous')
            matches_per_gene = defaultdict(dict)
            for idx, entry in enumerate(entries):
                if entry['genotypes'] == ('Heterozygous', 'Heterozygous', 'Reference') or \
                   entry['genotypes'] == ('Heterozygous', 'Reference', 'Heterozygous'):
                    if not matches_per_gene[entry['gene']]:
                        matches_per_gene[entry['gene']]['allele_ids'] = set()
                        matches_per_gene[entry['gene']]['genotypes'] = set()

                    matches_per_gene[entry['gene']]['allele_ids'].add(allele_ids[idx])
                    matches_per_gene[entry['gene']]['genotypes'].add(entry['genotypes'])

            matched_allele_ids = set()
            for match in matches_per_gene.values():
                if len(match['genotypes']) > 1:
                    matched_allele_ids.update(match['allele_ids'])

            assert result_allele_ids == matched_allele_ids

    @example((10001, 'X', 59999, 60000), 'Male', ('Homozygous', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 59999, 60000), 'Male', ('Heterozygous', 'Reference', 'Heterozygous'))
    @example((10001, 'X', 59999, 60000), 'Male', ('Heterozygous', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 59999, 60000), 'Male', ('Reference', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 59999, 60000), 'Male', ('Homozygous', 'Reference', 'Reference'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Homozygous', 'Reference', 'Heterozygous'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Heterozygous', 'Reference', 'Heterozygous'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Heterozygous', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Reference', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Homozygous', 'Reference', 'Reference'))
    @given(
        allele_strategy,
        sex_strategy,
        st.tuples(genotype_strategy, genotype_strategy, genotype_strategy)
    )
    @settings(deadline=None)
    def test_autosomal_recessive_homozygous(self, session, allele_data, proband_sex, genotypes):
        # Hypothesis reuses session, make sure it's rolled back
        session.rollback()

        allele_id, chrom, start_position, open_end_position = allele_data
        is_x_minus_par = x_minus_par(chrom, start_position, open_end_position)

        replace_allele_table(session, [allele_data])
        samples = [('Proband', proband_sex), ('Father', 'Male'), ('Mother', 'Female')]

        genotype_table = create_genotype_table(session, samples, [(allele_id,) + genotypes])

        result_allele_ids = FamilyFilter(session, GLOBAL_CONFIG).autosomal_recessive_homozygous(genotype_table, 'Proband', 'Father', 'Mother')
        if genotypes == ('Homozygous', 'Heterozygous', 'Heterozygous') and not is_x_minus_par:
            assert set(result_allele_ids) == set([allele_id])
        else:
            assert set(result_allele_ids) == set([])

    @example((10001, 'X', 59999, 60000), 'Male', ('Homozygous', 'Reference', 'Heterozygous'))
    @example((10001, 'X', 59999, 60000), 'Male', ('Heterozygous', 'Reference', 'Heterozygous'))
    @example((10001, 'X', 59999, 60000), 'Male', ('Heterozygous', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 59999, 60000), 'Male', ('Reference', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 59999, 60000), 'Male', ('Homozygous', 'Reference', 'Reference'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Homozygous', 'Reference', 'Heterozygous'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Heterozygous', 'Reference', 'Heterozygous'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Heterozygous', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Reference', 'Heterozygous', 'Heterozygous'))
    @example((10001, 'X', 60000, 60001), 'Male', ('Homozygous', 'Reference', 'Reference'))
    @given(
        allele_strategy,
        sex_strategy,
        st.tuples(genotype_strategy, genotype_strategy, genotype_strategy)
    )
    @settings(deadline=None)
    def test_xlinked_recessive_homozygous(self, session, allele_data, proband_sex, genotypes):
        # Hypothesis reuses session, make sure it's rolled back
        session.rollback()

        allele_id, chrom, start_position, open_end_position = allele_data

        is_x_minus_par = x_minus_par(chrom, start_position, open_end_position)
        replace_allele_table(session, [allele_data])
        samples = [('Proband', proband_sex), ('Father', 'Male'), ('Mother', 'Female')]

        genotype_table = create_genotype_table(session, samples, [(allele_id,) + genotypes])

        result_allele_ids = FamilyFilter(session, GLOBAL_CONFIG).xlinked_recessive_homozygous(genotype_table, 'Proband', 'Father', 'Mother')
        if genotypes == ('Homozygous', 'Reference', 'Heterozygous') and is_x_minus_par:
            assert set(result_allele_ids) == set([allele_id])
        else:
            assert set(result_allele_ids) == set([])
