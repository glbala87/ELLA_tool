from collections import defaultdict
import pytest
import uuid

from hypothesis import given, example, settings, reproduce_failure, assume
import hypothesis.strategies as st

from sqlalchemy import Table, Column, Boolean, Integer, Enum, Float
from sqlalchemy.schema import CreateTable
from vardb.datamodel import allele, annotation, gene, annotationshadow, Base
from api.allelefilter.segregationfilter import SegregationFilter, PAR1_START, PAR1_END, PAR2_START, PAR2_END


GLOBAL_CONFIG = {
    'transcripts': {
        'inclusion_regex': "NM_.*"
    }
}


class Sample:

    name = None
    sex = None
    proband = False
    father = False
    mother = False
    affected_sibling = False
    unaffected_sibling = False
    genotype = None
    allele_ratio = 0.0

    def __repr__(self):
        return '<{}: {} {:.2f}>'.format(self.name, self.genotype, self.allele_ratio)


def ps(gt, sex='Female', ar=0.0):
    s = Sample()
    s.name = 'Proband'
    s.sex = sex
    s.proband = True
    s.genotype = gt
    s.allele_ratio = ar
    return s


def fs(gt, ar=0.0):
    s = Sample()
    s.name = 'Father'
    s.sex = 'Male'
    s.father = True
    s.genotype = gt
    s.allele_ratio = ar
    return s


def ms(gt, ar=0.0):
    s = Sample()
    s.name = 'Mother'
    s.sex = 'Female'
    s.mother = True
    s.genotype = gt
    s.allele_ratio = ar
    return s


def uss(gt, num=1, sex='Female', ar=0.0):
    s = Sample()
    s.name = 'Unaffected {sex} sibling #{num}'.format(num=num, sex=sex)
    s.sex = sex
    s.unaffected_sibling = True
    s.genotype = gt
    s.allele_ratio = ar
    return s


def ass(gt, num=1, sex='Female', ar=0.0):
    s = Sample()
    s.name = 'Affected {sex} sibling #{num}'.format(num=num, sex=sex)
    s.sex = sex
    s.affected_sibling = True
    s.genotype = gt
    s.allele_ratio = ar
    return s


def get_sample_names(samples):
    result = dict()
    for s in samples:
        if s.proband:
            result['proband'] = s.name
        if s.father:
            result['father'] = s.name
        if s.mother:
            result['mother'] = s.name
        if s.unaffected_sibling:
            if 'unaffected_siblings' not in result:
                result['unaffected_siblings'] = list()
            result['unaffected_siblings'].append(s.name)
        if s.affected_sibling:
            if 'affected_siblings' not in result:
                result['affected_siblings'] = list()
            result['affected_siblings'].append(s.name)
    return result


allele_strategy = st.sampled_from([
    (10001, 'X', PAR1_START-2, PAR1_START-1),
    (10001, 'X', PAR1_START-1, PAR1_START),
    (10001, 'X', PAR1_START, PAR1_START+1),
    (10001, 'X', PAR1_START+1, PAR1_START+2),
    (10001, 'X', PAR1_END-2, PAR1_END-1),
    (10001, 'X', PAR1_END-1, PAR1_END),
    (10001, 'X', PAR1_END, PAR1_END+1),
    (10001, 'X', PAR1_END+1, PAR1_END+2),
    (10001, 'X', PAR2_START-2, PAR2_START-1),
    (10001, 'X', PAR2_START-1, PAR2_START),
    (10001, 'X', PAR2_START, PAR2_START+1),
    (10001, 'X', PAR2_START+1, PAR2_START+2),
    (10001, 'X', PAR2_END-2, PAR2_END-1),
    (10001, 'X', PAR2_END-1, PAR2_END),
    (10001, 'X', PAR2_END, PAR2_END+1),
    (10001, 'X', PAR2_END+1, PAR2_END+2),
    (10001, '1', 1, 1),  # Not in X
])


genotype_strategy = st.sampled_from(['Homozygous', 'Heterozygous', 'Reference', 'No coverage', None])
sex_strategy = st.sampled_from(['Male', 'Female'])
gene_strategy = st.sampled_from(['GENE1', 'GENE2'])


@st.composite
def sample_strategy(draw, include_father=None, include_mother=None, affected_siblings_num=None, affected_siblings_sex=None, unaffected_siblings_num=None, unaffected_siblings_sex=None, allele_ratio_sample_from=None):
    """
    allele_ratio_sample_from: Generating floats using st.floats() doesn't play with postgres since
      precision changes between Python and PostgreSQL, which breaks any threshold tests.
      Therefore, make a manual list of values to sample from, which are somewhat smaller/larger
      than threshold values of interest.
    """
    if include_father is None:
        include_father = draw(st.booleans())
    if include_mother is None:
        include_mother = draw(st.booleans())
    if affected_siblings_num is None:
        assert affected_siblings_sex is None
        affected_siblings_num = draw(st.integers(min_value=0, max_value=2))
        affected_siblings_sex = [draw(sex_strategy) for _ in xrange(affected_siblings_num)]
    if unaffected_siblings_num is None:
        assert unaffected_siblings_sex is None
        unaffected_siblings_num = draw(st.integers(min_value=0, max_value=2))
        unaffected_siblings_sex = [draw(sex_strategy) for _ in xrange(unaffected_siblings_num)]

    # If only proband, don't bother to run tests
    assume(any([include_father, include_mother, bool(affected_siblings_num), bool(unaffected_siblings_num)]))

    def get_allele_ratio():
        if allele_ratio_sample_from:
            return draw(st.sampled_from(allele_ratio_sample_from))
        else:
            return 0.0

    samples = [ps(draw(genotype_strategy), ar=get_allele_ratio())]
    if include_father:
        samples.append(
            fs(draw(genotype_strategy), ar=get_allele_ratio())
        )
    if include_mother:
        samples.append(
            ms(draw(genotype_strategy), ar=get_allele_ratio())
        )
    if affected_siblings_num:
        for idx in xrange(affected_siblings_num):
            samples.append(
                ass(draw(genotype_strategy), num=idx + 1, sex=affected_siblings_sex[idx], ar=get_allele_ratio())
            )
    if unaffected_siblings_num:
        for idx in xrange(unaffected_siblings_num):
            samples.append(
                uss(draw(genotype_strategy), num=idx + 1, sex=unaffected_siblings_sex[idx], ar=get_allele_ratio())
            )

    return samples


@st.composite
def compound_heterozygous_strategy(draw):
    entries = []
    include_father = draw(st.booleans())
    include_mother = draw(st.booleans())

    # Adjust test to generate siblings at lower rate
    r = draw(st.randoms())
    if r.random() > 0.2:
        affected_siblings_num = 0
        unaffected_siblings_num = 0
    else:
        affected_siblings_num = draw(st.integers(min_value=0, max_value=2))
        unaffected_siblings_num = draw(st.integers(min_value=0, max_value=2))

    # If only proband, don't bother to run tests
    assume(any([include_father, include_mother, bool(affected_siblings_num), bool(unaffected_siblings_num)]))

    affected_siblings_sex = [draw(sex_strategy) for _ in xrange(affected_siblings_num)]
    unaffected_siblings_sex = [draw(sex_strategy) for _ in xrange(unaffected_siblings_num)]

    per_gene = dict()
    for allele_count in xrange(draw(st.integers(min_value=1, max_value=4))):
        samples = draw(
            sample_strategy(
                include_father=include_father,
                include_mother=include_mother,
                affected_siblings_num=affected_siblings_num,
                affected_siblings_sex=affected_siblings_sex,
                unaffected_siblings_num=unaffected_siblings_num,
                unaffected_siblings_sex=unaffected_siblings_sex
            )
        )
        entry = {
            'gene': draw(gene_strategy),
            'genotypes': samples
        }
        if entry['gene'] not in per_gene:
            per_gene[entry['gene']] = list()
        per_gene[entry['gene']].append(entry)
        entries.append(entry)

    # Adjust towards generating compund heterozygous-like cases
    # There will be lots of cases generated not fitting the assumes below,
    # but more will have multiple hits per gene with some genotypes being heterozygous
    # This makes us hit the last part (rule_four_five) of the compound heterozygous test more often,
    # while still allowing all possible cases to be generated
    if r.random() > 0.05:
        is_multiple_gene = next((k for k, v in per_gene.iteritems() if len(v) > 2), None)
        assume(is_multiple_gene)
        assume(include_father and include_mother)
        proband_heterozygous = next(
            (e for e in per_gene[is_multiple_gene] for g in e['genotypes'] if g.genotype == 'Heterozygous' and g.proband), None
        )
        father_heterozygous = next(
            (e for e in per_gene[is_multiple_gene] for g in e['genotypes'] if g.genotype == 'Heterozygous' and g.father), None
        )
        mother_heterozygous = next(
            (e for e in per_gene[is_multiple_gene] for g in e['genotypes'] if g.genotype == 'Heterozygous' and g.mother), None
        )
        assume(proband_heterozygous and father_heterozygous and mother_heterozygous and mother_heterozygous != father_heterozygous)

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
    type = Enum("Homozygous", "Heterozygous", "Reference", "No coverage", name="genotypesampledata_type")
    sex = Enum("Male", "Female", name="sample_sex")
    sample_columns = []
    for s in samples:
        sample_columns.extend([
            Column(s[0] + '_type', type),
            Column(s[0] + '_sex', sex),
            Column(s[0] + '_ar', Float)
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
            idx = 2 * idx + 1
            row.extend([e[idx], s[1], e[idx + 1]])  # e.g. ['Homozygous', 'Male', 0.0]
        rows.append(row)

    session.execute('DROP TABLE IF EXISTS genotype_test_table')
    session.execute(CreateTable(genotype_table_definition))
    session.execute(genotype_table_definition.insert().values(rows))
    return genotype_table_definition


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
    @example(  # AD denovo
        (10001, '1', 1, 2),
        (ps('Heterozygous', sex='Male'), fs('Reference'), ms('Reference'))
    )
    @example(  # AD denovo
        (10001, '1', 1, 2),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Reference'))
    )
    @example(  # AD denovo
        (10001, '1', 1, 2),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous'))
    )
    @example(  # AD denovo
        (10001, '1', 1, 2),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('Reference'))
    )
    @example(  # X-linked female
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Heterozygous'), fs('Reference'), ms('Reference'))
    )
    @example(  # X-linked female
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous'), fs('Reference'), ms('Reference'))
    )
    @example(  # X-linked female
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous'), fs('Reference'), ms('Heterozygous'))
    )
    @example(  # X-linked male
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Reference'))
    )
    # Denovo negative examples
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Reference'))
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Heterozygous', sex='Male'), fs('Reference'), ms('Reference'))
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous'))
    )
    @example(
        (10001, '1', 1, 2),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('No coverage'))
    )
    @example(
        (10001, '1', 1, 2),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous'))
    )
    @example(
        (10001, '1', 1, 2),
        (ps('Homozygous', sex='Male'), fs('Homozygous'), ms('Heterozygous'))
    )
    @example(
        (10001, '1', 1, 2),
        (ps('Homozygous', sex='Male'), fs('No coverage'), ms('Heterozygous'))
    )
    @example(
        (10001, '1', 1, 2),
        (ps('Homozygous', sex='Male'), fs('No coverage'), ms('Heterozygous'))
    )
    @given(
        allele_strategy,
        sample_strategy(
            include_father=True,
            include_mother=True,
            unaffected_siblings_num=0,
            affected_siblings_num=0
        )
    )
    @settings(deadline=None)
    def test_denovo(self, session, allele_data, entry):
        # Hypothesis reuses session, make sure it's rolled back

        session.rollback()

        allele_id, chrom, start_position, open_end_position = allele_data
        is_x_minus_par = x_minus_par(chrom, start_position, open_end_position)

        replace_allele_table(session, [allele_data])
        samples = [(s.name, s.sex) for s in entry]
        genotype_data = [allele_id]
        for s in entry:
            genotype_data += [s.genotype, 0.0]

        genotype_table = create_genotype_table(session, samples, [genotype_data])

        sample_names = get_sample_names(entry)
        result_allele_ids = SegregationFilter(session, GLOBAL_CONFIG).denovo(
            genotype_table,
            sample_names['proband'],
            sample_names['father'],
            sample_names['mother']
        )

        ps = next(s for s in entry if s.name == sample_names['proband'])
        fs = next(s for s in entry if s.name == sample_names['father'])
        ms = next(s for s in entry if s.name == sample_names['mother'])
        genotypes = (ps.genotype, fs.genotype, ms.genotype)

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
            if ps.sex == 'Male':
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
        {'gene': 'GENE1', 'genotypes': (ps('Homozygous'), fs('Heterozygous'), ms('Heterozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Reference'), ms('Heterozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Heterozygous'), ms('Reference'))},
        {'gene': 'GENE2', 'genotypes': (ps('Homozygous'), fs('Heterozygous'), ms('Heterozygous'))},
    ], [1, 2])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Heterozygous'), ms('Reference'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Reference'), ms('Heterozygous'))},
        {'gene': 'GENE2', 'genotypes': (ps('Homozygous'), fs('Heterozygous'), ms('Heterozygous'))},
    ], [0, 1])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Homozygous'), fs('Heterozygous'), ms('Heterozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Reference'), ms('Heterozygous'))},
        {'gene': 'GENE2', 'genotypes': (ps('Heterozygous'), fs('Heterozygous'), ms('Reference'))},
        {'gene': 'GENE2', 'genotypes': (ps('Homozygous'), fs('Heterozygous'), ms('Heterozygous'))},
    ], [])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Homozygous'), fs('Reference'), ms('Reference'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('No coverage'), ms('Heterozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Heterozygous'), ms('Reference'))},
        {'gene': 'GENE2', 'genotypes': (ps('Homozygous'), fs('Heterozygous'), ms('Heterozygous'))},
    ], [])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Reference'), ms('Heterozygous'), uss('Heterozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Heterozygous'), ms('Reference'), uss('Reference'))},
    ], [0, 1])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Reference'), ms('Heterozygous'), ass('Reference'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Heterozygous'), ms('Reference'), ass('Heterozygous'))},
    ], [])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Reference'), ms('Heterozygous'), ass('Heterozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), fs('Heterozygous'), ms('Reference'), ass('Heterozygous'))},
    ], [0, 1])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'),  uss('Homozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), uss('Homozygous'))},
    ], [])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'),  ass('Heterozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), ass('Heterozygous'))},
    ], [0, 1])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'),  ass('Heterozygous'))},
        {'gene': 'GENE2', 'genotypes': (ps('Heterozygous'), ass('Heterozygous'))},
    ], [])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'),  uss('Heterozygous'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), uss('Reference'))},
        {'gene': 'GENE2', 'genotypes': (ps('Heterozygous'), uss('Heterozygous'))},
        {'gene': 'GENE2', 'genotypes': (ps('Heterozygous'), uss('Reference'))},
    ], [0, 1, 2, 3])
    @example([
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'),  ass('Reference'))},
        {'gene': 'GENE1', 'genotypes': (ps('Heterozygous'), ass('Heterozygous'))},
    ], [])
    @given(compound_heterozygous_strategy(), st.just(None))
    @settings(deadline=None)
    def test_compound_heterozygous(self, session, entries, manually_curated_result):
        # Hypothesis reuses session, make sure it's rolled back
        session.rollback()

        # Samples have to match over all entries
        samples = [(s.name, s.sex) for s in entries[0]['genotypes']]
        # Generate dummy alleles so we have an id to link the annotationshadowtable to
        # Positions are irrelevant
        entries_allele_ids = list()
        allele_entries = list()
        genotype_entries = list()
        annotationshadow_entries = list()
        for idx, entry in enumerate(entries):
            allele_id = 1000 + idx
            entries_allele_ids.append(allele_id)
            allele_entries.append((allele_id, '1', 1 + idx, 2 + idx))
            genotype_entry = [allele_id]
            for s in entry['genotypes']:
                genotype_entry += [s.genotype, 0.0]
            genotype_entries.append(genotype_entry)
            annotationshadow_entries.append((1000 + idx, allele_id, entry['gene']))

        replace_allele_table(session, allele_entries)
        replace_annotationshadowtranscript_table(session, annotationshadow_entries)
        genotype_table = create_genotype_table(session, samples, genotype_entries)

        sample_names = get_sample_names(entries[0]['genotypes'])
        result_allele_ids = SegregationFilter(session, GLOBAL_CONFIG).compound_heterozygous(
            genotype_table,
            sample_names['proband'],
            sample_names.get('father'),
            sample_names.get('mother'),
            affected_sibling_samples=sample_names.get('affected_siblings'),
            unaffected_sibling_samples=sample_names.get('unaffected_siblings'),
        )

        if manually_curated_result is not None:
            # Manual tests
            matched_allele_ids = set([entries_allele_ids[idx] for idx in manually_curated_result])
            assert result_allele_ids == matched_allele_ids

        # Parallell implementation of the five rules to compare against database queries
        # in the actual implementation
        affected_samples = [sample_names['proband']] + sample_names.get('affected_siblings', [])
        unaffected_samples = sample_names.get('unaffected_siblings', [])
        if sample_names.get('father'):
            unaffected_samples.append(sample_names['father'])
        if sample_names.get('mother'):
            unaffected_samples.append(sample_names['mother'])

        candidates = set(entries_allele_ids)

        rule_one_result = set()
        # 1. A variant has to be in a heterozygous state in all affected individuals.
        for allele_id, entry in zip(entries_allele_ids, entries):
            het_in_affected = True
            for name in affected_samples:
                es = next(s for s in entry['genotypes'] if s.name == name)
                if es.genotype != 'Heterozygous':
                    het_in_affected = False
            if het_in_affected:
                rule_one_result.add(allele_id)

        candidates = candidates & rule_one_result

        # 2. A variant must not occur in a homozygous state in any of the unaffected individuals.
        rule_two_result = set()
        for allele_id, entry in zip(entries_allele_ids, entries):
            not_hom_in_unaffected = True
            for name in unaffected_samples:
                es = next(s for s in entry['genotypes'] if s.name == name)
                if es.genotype == 'Homozygous':
                    not_hom_in_unaffected = False
            if not_hom_in_unaffected:
                rule_two_result.add(allele_id)

        candidates = candidates & rule_two_result

        # 3. A variant that is heterozygous in an affected child must be heterozygous in exactly one of the parents.
        if sample_names.get('father') and sample_names.get('mother'):
            rule_three_result = set()
            for allele_id, entry in zip(entries_allele_ids, entries):
                fs = next(s for s in entry['genotypes'] if s.name == sample_names['father'])
                ms = next(s for s in entry['genotypes'] if s.name == sample_names['mother'])
                if (fs.genotype == 'Heterozygous' and ms.genotype == 'Reference') or \
                   (fs.genotype == 'Reference' and ms.genotype == 'Heterozygous'):
                    rule_three_result.add(allele_id)
        else:
            # If no parents, all entries "pass" this rule
            rule_three_result = set(entries_allele_ids)

        candidates = candidates & rule_three_result

        # 4. A gene must have two or more heterozygous variants in each of the affected individuals.
        #  Rule 1 checked for heterozygous in affected already.
        #  We just need to check that we have two or more variants in the gene left in candidates
        # 5. There must be at least one variant transmitted from the paternal side and one transmitted from the maternal side.
        allele_ids_per_gene = defaultdict(set)
        father_per_gene = defaultdict(int)
        mother_per_gene = defaultdict(int)
        for allele_id, entry in zip(entries_allele_ids, entries):
            if allele_id not in candidates:
                continue
            allele_ids_per_gene[entry['gene']].add(allele_id)
            if sample_names.get('father') and sample_names.get('mother'):
                fs = next(s for s in entry['genotypes'] if s.name == sample_names['father'])
                # Homozygous is checked already per rule 2
                if fs.genotype == 'Heterozygous':
                    father_per_gene[entry['gene']] += 1
                ms = next(s for s in entry['genotypes'] if s.name == sample_names['mother'])
                if ms.genotype == 'Heterozygous':
                    mother_per_gene[entry['gene']] += 1

        rule_four_five_result = set()
        for gene_symbol, allele_ids in allele_ids_per_gene.iteritems():
            if len(allele_ids) > 1:
                if sample_names.get('father') and sample_names.get('mother'):
                    if father_per_gene[gene_symbol] > 0 and mother_per_gene[gene_symbol] > 0:
                        rule_four_five_result.update(allele_ids)
                else:
                    rule_four_five_result.update(allele_ids)

        final_candidates = candidates & rule_four_five_result

        assert result_allele_ids == final_candidates

    # Outside PAR
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Heterozygous', sex='Male'), fs('Reference'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Heterozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Reference', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Reference')),
        False
    )
    #Inside PAR
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        True
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Heterozygous', sex='Male'), fs('Reference'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Heterozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Reference', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Reference')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous'), ass('Homozygous')),
        True
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous'), ass('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous'), uss('Homozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous'), uss('Heterozygous')),
        True
    )
    @given(
        allele_strategy,
        sample_strategy(),
        st.just(None)
    )
    @settings(deadline=None)
    def test_autosomal_recessive_homozygous(self, session, allele_data, entry, manually_curated_result):
        # Hypothesis reuses session, make sure it's rolled back
        session.rollback()

        allele_id, chrom, start_position, open_end_position = allele_data
        is_x_minus_par = x_minus_par(chrom, start_position, open_end_position)

        replace_allele_table(session, [allele_data])

        samples = [(s.name, s.sex) for s in entry]
        genotype_table_data = [allele_id]
        for s in entry:
            genotype_table_data += [s.genotype, 0.0]
        genotype_table = create_genotype_table(session, samples, [genotype_table_data])
        sample_names = get_sample_names(entry)
        result_allele_ids = SegregationFilter(session, GLOBAL_CONFIG).autosomal_recessive_homozygous(
            genotype_table,
            sample_names['proband'],
            sample_names.get('father'),
            sample_names.get('mother'),
            unaffected_sibling_samples=sample_names.get('unaffected_siblings'),
            affected_sibling_samples=sample_names.get('affected_siblings'),
        )

        if manually_curated_result is not None:
            if manually_curated_result:
                assert result_allele_ids == set([allele_id])
            else:
                assert result_allele_ids == set([])

        # - Homozygous in proband
        # - Heterozygous in both parents
        # - Not homozygous in unaffected siblings
        # - Homozygous in affected siblings
        # - In chromosome 1-22 or X pseudoautosomal region (PAR1, PAR2)

        if is_x_minus_par:
            assert set(result_allele_ids) == set([])
            return

        if not (sample_names.get('father') and sample_names.get('mother')):
            assert set(result_allele_ids) == set([])
            return

        ps = next(e for e in entry if e.name == sample_names['proband'])
        fs = next(e for e in entry if e.name == sample_names['father'])
        ms = next(e for e in entry if e.name == sample_names['mother'])
        uss = [e for e in entry if e.name in sample_names.get('unaffected_siblings', [])]
        ass = [e for e in entry if e.name in sample_names.get('affected_siblings', [])]

        proband_homozygous = ps.genotype == 'Homozygous'
        heterozygous_parents = fs.genotype == 'Heterozygous' and ms.genotype == 'Heterozygous'
        not_homozygous_unaffected_siblings = all(e.genotype != 'Homozygous' for e in uss)
        homozygous_affected_siblings = all(e.genotype == 'Homozygous' for e in ass)
        if proband_homozygous and \
           heterozygous_parents and \
           not_homozygous_unaffected_siblings and \
           homozygous_affected_siblings:
            assert set(result_allele_ids) == set([allele_id])
        else:
            assert set(result_allele_ids) == set([])

    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous')),
        True
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Heterozygous', sex='Male'), fs('Reference'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Heterozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Reference', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Reference')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Heterozygous', sex='Male'), fs('Reference'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Heterozygous', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Reference', sex='Male'), fs('Heterozygous'), ms('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START, PAR1_START+1),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Reference')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous'), uss('Heterozygous')),
        True
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous'), uss('Homozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous'), ass('Heterozygous')),
        False
    )
    @example(
        (10001, 'X', PAR1_START-1, PAR1_START),
        (ps('Homozygous', sex='Male'), fs('Reference'), ms('Heterozygous'), ass('Homozygous')),
        True
    )
    @given(
        allele_strategy,
        sample_strategy(),
        st.just(None)
    )
    @settings(deadline=None)
    def test_xlinked_recessive_homozygous(self, session, allele_data, entry, manually_curated_result):
        # Hypothesis reuses session, make sure it's rolled back
        session.rollback()

        allele_id, chrom, start_position, open_end_position = allele_data
        is_x_minus_par = x_minus_par(chrom, start_position, open_end_position)

        replace_allele_table(session, [allele_data])

        samples = [(s.name, s.sex) for s in entry]
        genotype_table_data = [allele_id]
        for s in entry:
            genotype_table_data += [s.genotype, 0.0]
        genotype_table = create_genotype_table(session, samples, [genotype_table_data])
        sample_names = get_sample_names(entry)
        result_allele_ids = SegregationFilter(session, GLOBAL_CONFIG).xlinked_recessive_homozygous(
            genotype_table,
            sample_names['proband'],
            sample_names.get('father'),
            sample_names.get('mother'),
            unaffected_sibling_samples=sample_names.get('unaffected_siblings'),
            affected_sibling_samples=sample_names.get('affected_siblings'),
        )

        if manually_curated_result is not None:
            if manually_curated_result:
                assert result_allele_ids == set([allele_id])
            else:
                assert result_allele_ids == set([])

        # - Homozygous in proband (for girls this requires a denovo, but still valid case)
        # - Heterozygous in mother
        # - Not present in father
        # - Not homozygous in unaffected siblings
        # - Homozygous in affected siblings
        # - In chromosome X, but not pseudoautosomal region (PAR1, PAR2)

        if not is_x_minus_par:
            assert set(result_allele_ids) == set([])
            return

        if not (sample_names.get('father') and sample_names.get('mother')):
            assert set(result_allele_ids) == set([])
            return

        ps = next(e for e in entry if e.name == sample_names['proband'])
        fs = next(e for e in entry if e.name == sample_names['father'])
        ms = next(e for e in entry if e.name == sample_names['mother'])
        uss = [e for e in entry if e.name in sample_names.get('unaffected_siblings', [])]
        ass = [e for e in entry if e.name in sample_names.get('affected_siblings', [])]

        proband_homozygous = ps.genotype == 'Homozygous'
        heterozygous_mother = ms.genotype == 'Heterozygous'
        not_present_fater = fs.genotype == 'Reference'
        not_homozygous_unaffected_siblings = all(e.genotype != 'Homozygous' for e in uss)
        homozygous_affected_siblings = all(e.genotype == 'Homozygous' for e in ass)
        if proband_homozygous and \
           heterozygous_mother and \
           not_present_fater and \
           not_homozygous_unaffected_siblings and \
           homozygous_affected_siblings:
            assert set(result_allele_ids) == set([allele_id])
        else:
            assert set(result_allele_ids) == set([])

    @example((ps('Homozygous', sex='Male'), uss('Homozygous')))
    @example((ps('Homozygous', sex='Male'), uss('Heterozygous')))
    @example((ps('Heterozygous', sex='Male'), uss('Heterozygous')))
    @given(
        sample_strategy(
            include_father=False,
            include_mother=False,
            affected_siblings_num=0
        )
    )
    @settings(deadline=None)
    def test_homozygous_unaffected_siblings(self, session, entry):
        # Hypothesis reuses session, make sure it's rolled back
        session.rollback()

        # Position is irrelevant, but we need to insert something
        allele_data = (10001, 'X', PAR1_START-1, PAR1_START)
        allele_id = allele_data[0]

        replace_allele_table(session, [allele_data])

        samples = [(s.name, s.sex) for s in entry]
        genotype_table_data = [allele_id]
        for s in entry:
            genotype_table_data += [s.genotype, 0.0]
        genotype_table = create_genotype_table(session, samples, [genotype_table_data])
        sample_names = get_sample_names(entry)
        result_allele_ids = SegregationFilter(session, GLOBAL_CONFIG).homozygous_unaffected_siblings(
            genotype_table,
            sample_names['proband'],
            sample_names.get('unaffected_siblings')
        )

        all_homozygous = all([s.genotype == 'Homozygous' for s in entry])
        if all_homozygous:
            assert result_allele_ids == set([allele_id])
        else:
            assert result_allele_ids == set([])

    # Autosomal
    @example('A', (ps('Heterozygous', ar=0.31), ms('Reference', ar=0.3), fs('Reference', ar=0.0)), True)
    @example('A', (ps('Heterozygous', ar=0.3), ms('Reference', ar=0.3), fs('Reference', ar=0.0)), False)
    @example('A', (ps('Heterozygous', ar=0.31), ms('No coverage', ar=0.3), fs('Reference', ar=0.0)), False)
    @example('A', (ps('Heterozygous', ar=0.3), ms('Heterozygous', ar=0.3), fs('Reference', ar=0.0)), False)
    @example('A', (ps('Heterozygous', ar=0.31), ms('Reference', ar=0.0), fs('Reference', ar=0.3)), True)
    @example('A', (ps('Heterozygous', ar=0.3), ms('Reference', ar=0.0), fs('Reference', ar=0.3)), False)
    @example('A', (ps('Heterozygous', ar=0.31), ms('Reference', ar=0.0), fs('No coverage', ar=0.3)), False)
    @example('A', (ps('Heterozygous', ar=0.3), ms('Reference', ar=0.0), fs('Heterozygous', ar=0.3)), False)
    @example('A', (ps('Reference', ar=0.8), ms('Reference', ar=0.3), fs('Reference', ar=0.0)), False)
    # X-linked (proband sex is not considered)
    @example('X', (ps('Heterozygous', ar=0.5), ms('Reference', ar=0.3), fs('Reference', ar=0.0)), True)
    @example('X', (ps('Homozygous', ar=0.5), ms('Reference', ar=0.3), fs('Reference', ar=0.0)), True)
    @example('X', (ps('Heterozygous', ar=0.5), ms('Reference', ar=0.0), fs('Reference', ar=0.8)), True)
    @example('X', (ps('Homozygous', ar=0.5), ms('Reference', ar=0.0), fs('Reference', ar=0.5)), True)
    @given(
        st.sampled_from(['A', 'X']),
        sample_strategy(
            include_father=True,
            include_mother=True,
            allele_ratio_sample_from=[0.0, 0.29, 0.3, 0.31, 0.79, 0.8, 0.81, 1.0]
        ),
        st.just(None)
    )
    @settings(deadline=None)
    def test_inherited_mosaicism(self, session, a_or_x, entry, manually_curated_result):
        # Hypothesis reuses session, make sure it's rolled back
        session.rollback()

        if a_or_x == 'A':
            allele_data = (10001, '1', 1, 2)
        elif a_or_x == 'X':
            allele_data = (10001, 'X', PAR1_START-10, PAR1_START-9)
        else:
            raise RuntimeError("Invalid type {}".format(a_or_x))

        allele_id = allele_data[0]

        replace_allele_table(session, [allele_data])

        samples = [(s.name, s.sex) for s in entry]
        genotype_table_data = [allele_id]
        for s in entry:
            genotype_table_data += [s.genotype, s.allele_ratio]
        genotype_table = create_genotype_table(session, samples, [genotype_table_data])
        sample_names = get_sample_names(entry)

        result_allele_ids = SegregationFilter(session, GLOBAL_CONFIG).inherited_mosaicism(
            genotype_table,
            sample_names['proband'],
            sample_names['father'],
            sample_names['mother']
        )

        if manually_curated_result is not None:
            if manually_curated_result:
                assert result_allele_ids == set([allele_id])
            else:
                assert result_allele_ids == set()

        MOSAICISM_HETEROZYGOUS_THRESHOLD = [0, 0.3]  # (start, end]
        MOSAICISM_HOMOZYGOUS_THRESHOLD = [0, 0.8]  # (start, end]

        NON_MOSAICISM_THRESHOLD = 0.3

        ps = next(e for e in entry if e.name == sample_names['proband'])
        fs = next(e for e in entry if e.name == sample_names['father'])
        ms = next(e for e in entry if e.name == sample_names['mother'])

        # - In autosomal regions:
        #     - Proband has variant
        #     - Father or mother has allele_ratio between given heterozygous thresholds
        # - In X:
        #     - Proband has variant
        #     - Father or mother has allele_ratio between given (mother: heterozygous, father: homozygous) thresholds

        proband_not_mosacism = ps.allele_ratio > NON_MOSAICISM_THRESHOLD
        mother_has_coverage = ms.genotype not in ['No coverage', None]
        father_has_coverage = fs.genotype not in ['No coverage', None]
        if a_or_x == 'A':
            proband_has_variant = ps.genotype == 'Heterozygous'
            mother_mosaicism = ms.allele_ratio > MOSAICISM_HETEROZYGOUS_THRESHOLD[0] and ms.allele_ratio <= MOSAICISM_HETEROZYGOUS_THRESHOLD[1]
            father_mosaicism = fs.allele_ratio > MOSAICISM_HETEROZYGOUS_THRESHOLD[0] and fs.allele_ratio <= MOSAICISM_HETEROZYGOUS_THRESHOLD[1]
        else:
            proband_has_variant = ps.genotype in ['Heterozygous', 'Homozygous']
            mother_mosaicism = ms.allele_ratio > MOSAICISM_HETEROZYGOUS_THRESHOLD[0] and ms.allele_ratio <= MOSAICISM_HETEROZYGOUS_THRESHOLD[1]
            father_mosaicism = fs.allele_ratio > MOSAICISM_HOMOZYGOUS_THRESHOLD[0] and fs.allele_ratio <= MOSAICISM_HOMOZYGOUS_THRESHOLD[1]

        if proband_has_variant and \
           proband_not_mosacism and \
           mother_has_coverage and \
           father_has_coverage and \
           (mother_mosaicism or father_mosaicism):
            assert result_allele_ids == set([allele_id])
        else:
            assert result_allele_ids == set()

