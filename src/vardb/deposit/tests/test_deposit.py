import os
import tempfile
from collections import defaultdict
from contextlib import contextmanager

import hypothesis as ht
from sqlalchemy import or_
from vardb.deposit.deposit_analysis import DepositAnalysis
from vardb.datamodel.analysis_config import AnalysisConfigData
from vardb.datamodel import genotype, sample, allele
from .vcftestgenerator import vcf_strategy

import logging
log = logging.getLogger()
# Supress importer input, comment out when debugging
log.setLevel(logging.WARNING)


@contextmanager
def tempinput(data):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data)
    temp.close()
    try:
        yield temp.name
    finally:
        os.unlink(temp.name)


ANALYSIS_NUM = 0

@ht.given(vcf_strategy(6))
@ht.settings(deadline=None, max_examples=300)
def test_analysis_multiple(test_database, session, vcf_data):
    global ANALYSIS_NUM
    ANALYSIS_NUM += 1
    analysis_name = 'TEST_ANALYSIS {}'.format(ANALYSIS_NUM)

    vcf_string, ped_string, meta = vcf_data

    # Import generated analysis
    with tempinput(vcf_string) as vcf_file:
        with tempinput(ped_string or '') as ped_file:
            acd = AnalysisConfigData(vcf_file, analysis_name, 'HBOCUTV', 'v01', 1)
            da = DepositAnalysis(session)
            da.import_vcf(acd, ped_file=ped_file if ped_string else None)

    # Preload all data
    analysis = session.query(sample.Analysis).filter(
        sample.Analysis.name == analysis_name
    ).one()

    samples = session.query(sample.Sample).filter(
        sample.Sample.analysis_id == analysis.id
    ).all()

    genotypes = session.query(genotype.Genotype).filter(
        genotype.Genotype.sample_id.in_([s.id for s in samples])
    ).all()

    genotypesampledata = session.query(genotype.GenotypeSampleData).filter(
        genotype.GenotypeSampleData.genotype_id.in_([g.id for g in genotypes])
    ).all()

    alleles = session.query(allele.Allele).filter(
        or_(
            allele.Allele.id.in_([g.allele_id for g in genotypes]),
            allele.Allele.id.in_([g.secondallele_id for g in genotypes if g.secondallele_id]),
        )
    ).all()

    proband_variants = [v for v in meta['variants'] if '1' in v['samples'][0]['GT']]
    no_coverage_samples = list()
    for idx, sample_name in enumerate(meta['sample_names']):
        if all(v['samples'][idx]['GT'] == './.' for v in meta['variants']):
            no_coverage_samples.append(sample_name)

    # Start checking data
    # Samples
    proband_sample = None
    for sample_name, ped in meta['ped_info'].iteritems():
        sa = next(sa for sa in samples if sa.identifier == sample_name)
        if ped['sex'] is not None:
            assert sa.sex == ('Female' if ped['sex'] == '2' else 'Male')
        else:
            assert sa.sex is None
        assert sa.affected is (ped['affected'] == '2')
        is_proband = ped['proband'] == '1'
        assert sa.proband is is_proband
        if is_proband:
            assert proband_sample is None
            proband_sample = sa
        assert sa.family_id == ped.get('fam')

        father_name = ped['father'] if 'father' in ped and ped['father'] != '0' else None
        mother_name = ped['mother'] if 'mother' in ped and ped['mother'] != '0' else None
        if father_name:
            fsa = next(sa for sa in samples if sa.identifier == father_name)
            assert sa.father_id == fsa.id
        if mother_name:
            msa = next(sa for sa in samples if sa.identifier == mother_name)
            assert sa.mother_id == msa.id

        # Samples are ordered, so we know proband is already processed..
        if not is_proband and father_name and mother_name:
            assert sa.sibling_id == proband_sample.id

    # Variants
    if not proband_variants:
        assert not alleles
        assert not genotypes
        assert not genotypesampledata
    else:
        assert len(proband_variants) in [1, 2]
        fixtures = {
            'allele': {},
            'secondallele': {}
        }
        for variant in proband_variants:
            sample_data = {k: v for k, v in zip(meta['sample_names'], variant['samples'])}
            al = next(
                a for a in alleles if \
                a.vcf_pos == variant['pos'] and \
                a.vcf_ref == variant['ref'] and \
                a.vcf_alt == variant['alt'] and \
                a.chromosome == variant['chromosome']
            )
            key = 'allele'
            if sample_data['PROBAND']['GT'] == './1':
                key = 'secondallele'

            fixtures[key]['sample_data'] = sample_data
            fixtures[key]['variant'] = variant
            fixtures[key]['allele'] = al
            for sample_name in sample_data:
                sa = next(sa for sa in samples if sa.identifier == sample_name)
                gsds = [gsd for gsd in genotypesampledata if gsd.sample_id == sa.id and gsd.secondallele is (True if key == 'secondallele' else False)]
                assert len(gsds) == 1
                gsd = gsds[0]
                if 'genotypesampledata' not in fixtures[key]:
                    fixtures[key]['genotypesampledata'] = dict()
                fixtures[key]['genotypesampledata'][sample_name] = gsd

        gt = next(g for g in genotypes if g.allele_id == fixtures['allele']['allele'].id \
                  and g.secondallele_id == (fixtures['secondallele']['allele'].id if fixtures['secondallele'] else None))

        assert gt.variant_quality == 5000
        assert gt.filter_status == 'PASS'

        # Allele depth
        sample_allele_depth = defaultdict(dict)
        for variant in meta['variants']:
            for sample_name, sample_data in zip(meta['sample_names'], variant['samples']):
                sample_allele_depth[sample_name].update(
                    {k: v for k, v in zip(
                        ['REF ({})'.format(variant['ref']), variant['alt']],
                        [int(a) for a in sample_data['AD'].split(',')]
                    )}
                )


        # Check that genotypesampledata is set correctly
        for key in ['allele', 'secondallele']:
            if key == 'secondallele' and not fixtures[key]:
                continue
            for sample_name, data in fixtures[key]['sample_data'].iteritems():
                gsd = fixtures[key]['genotypesampledata'][sample_name]
                if data['GT'] == '1/1':
                    gsd_type = 'Homozygous'
                elif data['GT'] in ['0/1', '1/.', './1']:
                    gsd_type = 'Heterozygous'
                elif data['GT'] in ['0/0', '0/.', './0']:
                    gsd_type = 'Reference'
                elif data['GT'] == './.':
                    # Proband cannot be reference for it's own variants
                    assert sample_name != 'PROBAND'
                    if sample_name in no_coverage_samples:
                        gsd_type = 'No coverage'
                    else:
                        # 'Reference' doesn't mean vcf ref,
                        # but with regards to proband's variant
                        gsd_type = 'Reference'
                gsd_multiallelic = data['GT'] in ['./1', '1/.', '0/.', './0']
                assert gsd.type == gsd_type
                assert gsd.multiallelic == gsd_multiallelic
                assert gsd.sequencing_depth == data['DP']
                if not gsd_multiallelic:
                    assert gsd.genotype_likelihood == [int(p) for p in data['PL'].split(',')]
                else:
                    assert gsd.genotype_likelihood is None
                assert gsd.allele_depth == sample_allele_depth[sample_name]
