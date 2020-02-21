from itertools import chain
from sqlalchemy import or_
import hypothesis as ht
import hypothesis.strategies as st
from vardb.datamodel import sample, allele, genotype, gene, annotationshadow
from datalayer.alleledataloader.alleledataloader import AlleleDataLoader
from datalayer import queries


def test_get_formatted_genotypes(test_database, session):

    test_database.refresh()

    # Just get a random sample id that exists, doesn't matter which one
    sample_id = session.query(sample.Sample.id).limit(1).scalar()
    # Also get two random allele id
    allele1, allele2 = session.query(allele.Allele).limit(2).all()

    ref1 = allele1.change_from or "-"
    ref2 = allele2.change_from or "-"
    alt1 = allele1.change_to or "-"
    alt2 = allele2.change_to or "-"

    adl = AlleleDataLoader(session)

    fixtures = [
        # Proband single allele cases
        [
            # (multiallelic, type)
            (False, "Homozygous"),
            # (gt1, gt2)
            (alt1, alt1),
        ],
        [(False, "Heterozygous"), (ref1, alt1)],
        [(False, "Reference"), (ref1, ref1)],
        [(False, "No coverage"), (".", ".")],
        # Multiallelic single allele cases
        [
            # proband allele 1 './1'
            (True, "Heterozygous"),
            (alt1, "?"),
        ],
        [
            # proband allele 1 './.'
            (True, "Reference"),
            ("?", "?"),
        ],
        # Multiallelic two alleles cases
        [
            # proband allele 1 './1'
            # proband allele 2 './1'
            (True, "Heterozygous"),
            (True, "Heterozygous"),
            (alt1, alt2),
        ],
        [
            # not imported since not in proband: './1'
            # proband allele 1 './.'
            # proband allele 2 './1'
            (True, "Reference"),
            (True, "Heterozygous"),
            (alt2, "?"),
        ],
        [
            # flipped of above case
            # not imported since not in proband: './1'
            # proband allele 1 './1'
            # proband allele 2 './.'
            (True, "Heterozygous"),
            (True, "Reference"),
            (alt1, "?"),
        ],
        [
            # not imported since not in proband: './1'
            # not imported since not in proband: './1'
            # proband allele 1 './.'
            # proband allele 2 './.'
            (True, "Reference"),
            (True, "Reference"),
            ("?", "?"),
        ],
        [
            # proband allele 1 './.'
            # proband allele 2 '0/0'
            (True, "Reference"),
            (False, "Reference"),
            (ref2, ref2),
        ],
        [
            # proband allele 1 './.'
            # proband allele 2 '0/1'
            (True, "Reference"),
            (False, "Heterozygous"),
            (ref2, alt2),
        ],
        [
            # flip above case
            # proband allele 1 '0/1'
            # proband allele 2 './.'
            (False, "Heterozygous"),
            (True, "Reference"),
            (ref1, alt1),
        ],
        [(False, "No coverage"), (False, "No coverage"), (".", ".")],
    ]

    for fixture in fixtures:
        session.execute("DELETE FROM genotypesampledata WHERE sample_id = {}".format(sample_id))
        session.execute("DELETE FROM genotype WHERE sample_id = {}".format(sample_id))
        f1 = fixture[0]
        f2 = None
        if len(fixture) > 2:
            f2 = fixture[1]
        gt = genotype.Genotype(
            allele_id=allele1.id, secondallele_id=allele2.id if f2 else None, sample_id=sample_id
        )
        session.add(gt)
        session.flush()
        gsd1 = genotype.GenotypeSampleData(
            sample_id=sample_id,
            genotype_id=gt.id,
            secondallele=False,
            multiallelic=f1[0],
            type=f1[1],
        )
        session.add(gsd1)
        if f2:
            gsd2 = genotype.GenotypeSampleData(
                sample_id=sample_id,
                genotype_id=gt.id,
                secondallele=True,
                multiallelic=f2[0],
                type=f2[1],
            )
            session.add(gsd2)
        session.commit()

        target = fixture[-1]
        target_gt = "/".join(target)
        actual_gt = adl.get_formatted_genotypes([allele1.id], sample_id)[gt.id]
        assert actual_gt == target_gt, fixture


def get_analysis_alleles(session, analysis_id):
    return (
        session.query(allele.Allele)
        .join(
            genotype.Genotype,
            or_(
                genotype.Genotype.allele_id == allele.Allele.id,
                genotype.Genotype.secondallele_id == allele.Allele.id,
            ),
        )
        .join(sample.Sample)
        .join(sample.Analysis)
        .distinct()
    )


def get_analysis_genepanel(session, analysis_id):
    return (
        session.query(gene.Genepanel)
        .join(sample.Analysis)
        .filter(sample.Analysis.id == analysis_id)
        .one()
    )


@st.composite
def allele_position_strategy(draw):
    start_position = draw(st.integers(min_value=1, max_value=50))
    open_end_position = draw(st.integers(min_value=start_position, max_value=50))
    load_allele = draw(st.booleans())
    return (start_position, open_end_position, load_allele)


def create_analysis():
    return sample.Analysis(name="TestAnalysis", genepanel_name="HBOC", genepanel_version="v01")


def create_sample(analysis_id):
    return sample.Sample(
        identifier="TestSample",
        analysis_id=analysis_id,
        proband=True,
        affected=True,
        sample_type="HTS",
    )


def create_allele(start, end):
    return allele.Allele(
        genome_reference="GRCh37",
        chromosome="1",
        start_position=start,
        open_end_position=end,
        change_from="A",
        change_to="T",
        change_type="SNP",
        vcf_pos=start + 1,
        vcf_ref="A",
        vcf_alt="T",
    )


def add_genotype(session, allele_id, sample_id):
    gt = genotype.Genotype(allele_id=allele_id, sample_id=sample_id)
    session.add(gt)
    session.flush()

    gsd = genotype.GenotypeSampleData(
        genotype_id=gt.id,
        secondallele=False,
        multiallelic=False,
        sample_id=sample_id,
        type="Heterozygous",
    )
    session.add(gsd)
    session.flush()


@ht.example([(1, 100, True), (3, 10000, True)])  # start <-> start
@ht.example([(1, 3, True), (5, 100, True)])  # end <-> start
@ht.example([(1, 100, True), (50, 102, True)])  # end <-> end
@ht.example([(1, 2, True), (1, 7, False), (4, 10, True)])
@ht.given(st.lists(allele_position_strategy(), min_size=3, unique_by=lambda x: x[:2]))
def test_nearby_warning(session, allele_positions):
    session.rollback()

    an = create_analysis()
    session.add(an)
    session.flush()
    s = create_sample(an.id)
    session.add(s)
    session.flush()

    expected = []
    alleles = []

    for i, (start, end, load) in enumerate(allele_positions):
        a = create_allele(start, end)
        session.add(a)
        session.flush()

        add_genotype(session, a.id, s.id)

        other_start_end = chain.from_iterable(
            [ap[:2] for j, ap in enumerate(allele_positions) if i != j]
        )
        if load:
            alleles.append(a)
            if min(min([abs(start - se), abs(end - se)]) for se in other_start_end) < 3:
                expected.append(a.id)

    adl = AlleleDataLoader(session)
    loaded_alleles = adl.from_objs(alleles, analysis_id=an.id, genepanel=an.genepanel)
    actual = [
        a["id"]
        for a in loaded_alleles
        if a.get("warnings", {}).get("nearby_allele")
        == "Another variant is within 2 bp of this variant"
    ]
    assert set(actual) == set(expected), "Actual: {}. Expected: {}. Positions: {}".format(
        actual, expected, allele_positions
    )


def test_worse_consequence_warning(test_database, session):
    # TODO: Rewrite consequence check to use annotationshadowtranscript
    return


def test_inconsistent_ensembl_transcript(test_database, session):
    test_database.refresh()
    analysis_id = 1

    allele = get_analysis_alleles(session, analysis_id).limit(1).one()
    genepanel = get_analysis_genepanel(session, analysis_id)
    adl = AlleleDataLoader(session)
    loaded_alleles = adl.from_objs([allele], analysis_id=analysis_id, genepanel=genepanel)

    assert len(loaded_alleles) == 1
    assert "warnings" not in loaded_alleles[0]

    # Modify corresponding ensembl transcript to not match genepanel transcript annotation
    q = queries.annotation_transcripts_genepanel(
        session, [(genepanel.name, genepanel.version)], allele_ids=[allele.id]
    ).one()

    corr_ensembl = (
        session.query(gene.Transcript.corresponding_ensembl)
        .filter(gene.Transcript.transcript_name == q.genepanel_transcript)
        .scalar()
    )

    # Check mismatching HGVSc
    ast = (
        session.query(annotationshadow.AnnotationShadowTranscript)
        .filter(
            annotationshadow.AnnotationShadowTranscript.transcript == corr_ensembl,
            annotationshadow.AnnotationShadowTranscript.allele_id == allele.id,
        )
        .one()
    )
    ast.hgvsc = "c.xxxxxx"
    session.flush()

    loaded_alleles = adl.from_objs([allele], analysis_id=analysis_id, genepanel=genepanel)
    assert len(loaded_alleles) == 1
    assert loaded_alleles[0]["warnings"][
        "hgvs_consistency"
    ] == "Annotation for {} does not match corresponding transcript: {}:{} ({})".format(
        q.annotation_transcript, ast.transcript, ast.hgvsc, ast.hgvsp
    )

    session.rollback()

    # Check mismatching HGVSp
    ast = (
        session.query(annotationshadow.AnnotationShadowTranscript)
        .filter(
            annotationshadow.AnnotationShadowTranscript.transcript == corr_ensembl,
            annotationshadow.AnnotationShadowTranscript.allele_id == allele.id,
        )
        .one()
    )

    ast.hgvsp = "p.xxxxxx"
    session.flush()
    loaded_alleles = adl.from_objs([allele], analysis_id=analysis_id, genepanel=genepanel)
    assert len(loaded_alleles) == 1
    assert loaded_alleles[0]["warnings"][
        "hgvs_consistency"
    ] == "Annotation for {} does not match corresponding transcript: {}:{} ({})".format(
        q.annotation_transcript, ast.transcript, ast.hgvsc, ast.hgvsp
    )

    session.rollback()

    # Check case where refseq is the corresponding transcript
    # Flip refseq/ensembl
    tx = (
        session.query(gene.Transcript)
        .filter(gene.Transcript.transcript_name == q.genepanel_transcript)
        .one()
    )

    tx.corresponding_refseq = tx.transcript_name
    tx.transcript_name = tx.corresponding_ensembl
    tx.type = "Ensembl"
    tx.corresponding_ensembl = None

    session.flush()

    ast = (
        session.query(annotationshadow.AnnotationShadowTranscript)
        .filter(
            annotationshadow.AnnotationShadowTranscript.transcript == tx.corresponding_refseq,
            annotationshadow.AnnotationShadowTranscript.allele_id == allele.id,
        )
        .one()
    )

    ast.hgvsc = "c.xxxxxx"
    session.flush()

    q = queries.annotation_transcripts_genepanel(
        session, [(genepanel.name, genepanel.version)], allele_ids=[allele.id]
    ).one()
    loaded_alleles = adl.from_objs([allele], analysis_id=analysis_id, genepanel=genepanel)
    assert len(loaded_alleles) == 1
    assert loaded_alleles[0]["warnings"][
        "hgvs_consistency"
    ] == "Annotation for {} does not match corresponding transcript: {}:{} ({})".format(
        q.annotation_transcript, ast.transcript, ast.hgvsc, ast.hgvsp
    )
