from vardb.datamodel import sample, allele, genotype
from api.util.alleledataloader import AlleleDataLoader


def test_get_formatted_genotypes(test_database, session):

    test_database.refresh()

    # Just get a random sample id that exists, doesn't matter which one
    sample_id = session.query(sample.Sample.id).limit(1).scalar()
    # Also get two random allele id
    allele1, allele2 = session.query(allele.Allele).limit(2).all()

    ref1 = allele1.change_from or '-'
    ref2 = allele2.change_from or '-'
    alt1 = allele1.change_to or '-'
    alt2 = allele2.change_to or '-'

    adl = AlleleDataLoader(session)

    fixtures = [
        # Proband single allele cases
        [
            # (multiallelic, type)
            (False, 'Homozygous'),
            # (gt1, gt2)
            (alt1, alt1)
        ],
        [
            (False, 'Heterozygous'),
            (ref1, alt1)
        ],
        [
            (False, 'Reference'),
            (ref1, ref1)
        ],
        [
            (False, 'No coverage'),
            ('.', '.')
        ],
        # Multiallelic single allele cases
        [
            # proband allele 1 './1'
            (True, 'Heterozygous'),
            (alt1, '?')
        ],
        [
            # proband allele 1 './.'
            (True, 'Reference'),
            ('?', '?')
        ],
        # Multiallelic two alleles cases
        [
            # proband allele 1 './1'
            # proband allele 2 './1'
            (True, 'Heterozygous'),
            (True, 'Heterozygous'),
            (alt1, alt2)
        ],
        [
            # not imported since not in proband: './1'
            # proband allele 1 './.'
            # proband allele 2 './1'
            (True, 'Reference'),
            (True, 'Heterozygous'),
            (alt2, '?')
        ],
        [
            # flipped of above case
            # not imported since not in proband: './1'
            # proband allele 1 './1'
            # proband allele 2 './.'
            (True, 'Heterozygous'),
            (True, 'Reference'),
            (alt1, '?')
        ],
        [
            # not imported since not in proband: './1'
            # not imported since not in proband: './1'
            # proband allele 1 './.'
            # proband allele 2 './.'
            (True, 'Reference'),
            (True, 'Reference'),
            ('?', '?')
        ],
        [
            # proband allele 1 './.'
            # proband allele 2 '0/0'
            (True, 'Reference'),
            (False, 'Reference'),
            (ref2, ref2)
        ],
        [
            # proband allele 1 './.'
            # proband allele 2 '0/1'
            (True, 'Reference'),
            (False, 'Heterozygous'),
            (ref2, alt2)
        ],
        [
            # flip above case
            # proband allele 1 '0/1'
            # proband allele 2 './.'
            (False, 'Heterozygous'),
            (True, 'Reference'),
            (ref1, alt1)
        ],
        [
            (False, 'No coverage'),
            (False, 'No coverage'),
            ('.', '.')
        ]

    ]

    for fixture in fixtures:
        session.execute('DELETE FROM genotypesampledata WHERE sample_id = {}'.format(sample_id))
        session.execute('DELETE FROM genotype WHERE sample_id = {}'.format(sample_id))
        f1 = fixture[0]
        f2 = None
        if len(fixture) > 2:
            f2 = fixture[1]
        gt = genotype.Genotype(
            allele_id=allele1.id,
            secondallele_id=allele2.id if f2 else None,
            sample_id=sample_id
        )
        session.add(gt)
        session.flush()
        gsd1 = genotype.GenotypeSampleData(
            sample_id=sample_id,
            genotype_id=gt.id,
            secondallele=False,
            multiallelic=f1[0],
            type=f1[1]
        )
        session.add(gsd1)
        if f2:
            gsd2 = genotype.GenotypeSampleData(
                sample_id=sample_id,
                genotype_id=gt.id,
                secondallele=True,
                multiallelic=f2[0],
                type=f2[1]
            )
            session.add(gsd2)
        session.commit()

        target = fixture[-1]
        target_gt = '/'.join(target)
        actual_gt = adl.get_formatted_genotypes([allele1.id], sample_id)[gt.id]
        assert actual_gt == target_gt, fixture
