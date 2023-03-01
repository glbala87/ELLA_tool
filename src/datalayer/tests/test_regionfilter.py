"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy

import hypothesis as ht
import hypothesis.strategies as st
import pytest

from conftest import mock_allele, mock_allele_with_annotation
from datalayer.allelefilter.regionfilter import RegionFilter
from vardb.datamodel import gene

# prevent screen getting filled with output (useful when testing manually)
# import logging
# logging.getLogger('vardb.deposit.deposit_genepanel').setLevel(logging.CRITICAL)


FILTER_CONFIG = {"splice_region": [-10, 5], "utr_region": [-12, 20]}


@st.composite
def allele_positions(draw, chromosome, start, end):
    start_position = draw(st.integers(min_value=start, max_value=end))
    end_position = draw(st.integers(min_value=start_position + 1, max_value=start_position + 50))
    return (chromosome, start_position, end_position)


def create_genepanel(session):
    # Create fake genepanel for testing purposes
    genepanel = gene.Genepanel(name="testpanel", version="v01", genome_reference="GRCh37")
    session.add(genepanel)
    session.flush()

    # Create 6 genes
    genes = [gene.Gene(hgnc_id=i + 1, hgnc_symbol=f"GENE{i+1}") for i in range(6)]

    # Create 6 transcripts, one for each gene
    # The first 4 transcripts are on the positive strand, the last 2 on the negative strand
    # The transcripts are on different chromosomes, with positions increasing with hgnc_id
    #
    # The transcripts have the following properties:
    #
    # transcript NM_1.1 for gene 1:
    # chromosome 1, start-end 1000-1500 (strand +, cds 1230-1430, exons 1100-1160, 1200-1260, 1300-1360, 1400-1460)
    # transcript NM_2.1 for gene 2:
    # chromosome 2, start-end 2000-2500 (strand +, cds 2230-2430, exons 2100-2160, 2200-2260, 2300-2360, 2400-2460)
    # transcript NM_3.1 for gene 3:
    # chromosome 3, start-end 3000-3500 (strand +, cds 3230-3430, exons 3100-3160, 3200-3260, 3300-3360, 3400-3460)
    # transcript NM_4.1 for gene 4:
    # chromosome 4, start-end 4000-4500 (strand +, cds 4230-4430, exons 4100-4160, 4200-4260, 4300-4360, 4400-4460)
    # transcript NM_5.1 for gene 5:
    # chromosome 5, start-end 5000-5500 (strand -, cds 5230-5430, exons 5100-5160, 5200-5260, 5300-5360, 5400-5460)
    # transcript NM_6.1 for gene 6:
    # chromosome 6, start-end 6000-6500 (strand -, cds 6230-6430, exons 6100-6160, 6200-6260, 6300-6360, 6400-6460)
    #
    transcripts = [
        gene.Transcript(
            gene=g,
            transcript_name=f"NM_{g.hgnc_id}.1",
            type="RefSeq",
            genome_reference="",
            tags=None,
            chromosome=f"{g.hgnc_id}",
            tx_start=g.hgnc_id * 1000,
            tx_end=500 + g.hgnc_id * 1000,
            strand="+" if g.hgnc_id <= 4 else "-",
            cds_start=230 + g.hgnc_id * 1000,
            cds_end=430 + g.hgnc_id * 1000,
            exon_starts=[x + g.hgnc_id * 1000 for x in [100, 200, 300, 400]],
            exon_ends=[x + g.hgnc_id * 1000 for x in [160, 260, 360, 460]],
        )
        for g in genes
    ]
    session.add_all(transcripts)
    session.flush()
    session.execute(
        gene.genepanel_transcript.insert(),
        [
            {
                "transcript_id": tx.id,
                "genepanel_name": genepanel.name,
                "genepanel_version": genepanel.version,
                "inheritance": "AD/AR",
            }
            for tx in transcripts
        ],
    )

    return genepanel


class TestRegionFilter(object):
    @pytest.mark.aa(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

        create_genepanel(session)
        session.commit()

    @pytest.mark.aa(order=1)
    @ht.example(("1", 1600, 1601), True)  # Outside all genepanel transcripts
    @ht.example(("1", 1100, 1101), True)  # Within transcript, but outside coding region
    @ht.example(("1", 1451, 1452), True)  # Within transcript, but outside coding regio
    @ht.example(("1", 1289, 1290), True)  # Intronic variant (-11)
    @ht.example(("1", 1465, 1466), True)  # Intronic variant (+6) (in UTR)
    @ht.example(("1", 1265, 1266), True)  # Intronic variant (+6)
    @ht.example(("5", 5209, 5210), True)  # UTR variant [+21] on reverse transcript
    @ht.example(("5", 5443, 5444), True)  # UTR variant (-13) on reverse transcript
    @ht.example(("5", 5294, 5295), True)  # Intronic variant (+6) on reverse transcript
    @ht.example(("1", 1300, 1301), False)  # Within coding exon
    @ht.example(("1", 1290, 1291), False)  # Within splice region [-10]
    @ht.example(("1", 1090, 1091), False)  # Within splice region of UTR exon [-10]
    @ht.example(("1", 1164, 1165), False)  # Within splice region of UTR exon [+5]
    @ht.example(("1", 1449, 1450), False)  # Within utr region [20]
    @ht.example(("1", 1218, 1219), False)  # Within utr region [-12]
    @ht.example(("5", 5441, 5442), False)  # Within utr region [-12] on reverse transcript
    @ht.example(("5", 5210, 5211), False)  # Within utr region [20] on reverse transcript
    @ht.example(("5", 5469, 5470), False)  # Within exonic region [-10] on reverse transcript
    @ht.example(("5", 5095, 5096), False)  # Within exonic region [+5] on reverse transcript
    @ht.example(("1", 1261, 1262), False)  # Splice region variant (+2)
    @ht.example(("1", 1260, 1261), False)  # Intronic variant (+1)
    @ht.example(("1", 1259, 1260), False)  # Last variant in exon
    @ht.example(("1", 1199, 1200), False)  # Splice region variant (-1)
    @ht.example(("1", 1198, 1199), False)  # Splice region variant (-2)
    @ht.example(("1", 1200, 1201), True)  # First variant in non-coding exon
    @ht.example(("1", 1260, 1261), False)  # First variant in coding exon
    @ht.example(("5", 5398, 5399), False)  # Splice region variant (+2) on reverse transcript
    @ht.example(("5", 5399, 5400), False)  # Splice region variant (+1) on reverse transcript
    @ht.example(("5", 5400, 5401), False)  # Last variant in exon on reverse transcript
    @ht.example(("5", 5461, 5462), False)  # Splice region variant (+2) on reverse transcript
    @ht.example(("5", 5460, 5461), False)  # Splice region variant (+1) on reverse transcript
    @ht.example(("5", 5459, 5460), True)  # First variant in non-coding exon on reverse transcript
    @ht.example(("5", 5359, 5460), False)  # First variant in coding exon on reverse transcript
    @ht.example(("6", 6259, 6260), False)  # First base in coding region)
    @ht.example(("6", 6400, 6401), False)  # Last base in coding region
    @ht.given(
        st.one_of(
            allele_positions("1", 800, 1700),  # t1, positive strand
            allele_positions("5", 4800, 5700),  # t5, negative strand
            allele_positions("6", 5800, 6700),  # t6, negative strand
        ),
        st.just(None),
    )
    @ht.settings(deadline=1000)
    def test_genomic_region_filtering(self, session, positions, manually_curated_result):
        """
        Tests both using manually curated test and parallell implementation in Python.
        """
        session.rollback()

        chromosome, start_position, open_end_position = positions
        al = mock_allele(
            session,
            {
                "chromosome": chromosome,
                "start_position": start_position,
                "open_end_position": open_end_position,
            },
        )

        allele_ids = [al.id]
        gp_key = ("testpanel", "v01")
        rf = RegionFilter(session, None)
        result = rf.filter_alleles({gp_key: allele_ids}, FILTER_CONFIG)

        # Manually curated test cases
        if manually_curated_result is not None:
            if manually_curated_result:
                assert result[gp_key] == set(allele_ids)
            else:
                assert result[gp_key] == set([])

        genepanel = (
            session.query(gene.Genepanel)
            .filter(gene.Genepanel.name == "testpanel", gene.Genepanel.version == "v01")
            .one()
        )

        splice_region = FILTER_CONFIG["splice_region"]
        utr_region = FILTER_CONFIG["utr_region"]

        splice_include_regions = []
        coding_include_regions = []
        utr_include_regions = []

        for transcript in genepanel.transcripts:
            for es, ee in zip(transcript.exon_starts, transcript.exon_ends):
                splice_upstream = (
                    splice_region[0] if transcript.strand == "+" else -splice_region[1]
                )
                splice_downstream = (
                    splice_region[1] if transcript.strand == "+" else -splice_region[0]
                )
                splice_include_regions.append(
                    (es + splice_upstream, es - 1)
                )  # Region before exon start
                splice_include_regions.append((ee, ee - 1 + splice_downstream))

                if es <= transcript.cds_end - 1 and ee - 1 >= transcript.cds_start:
                    coding_start = es if es > transcript.cds_start else transcript.cds_start
                    coding_end = ee - 1 if ee < transcript.cds_end else transcript.cds_end - 1
                    coding_include_regions.append((coding_start, coding_end))

            utr_upstream = utr_region[0] if transcript.strand == "+" else -utr_region[1]
            utr_downstream = utr_region[1] if transcript.strand == "+" else -utr_region[0]

            utr_include_regions.extend(
                [
                    (transcript.cds_start + utr_upstream, transcript.cds_start - 1),
                    (transcript.cds_end, transcript.cds_end - 1 + utr_downstream),
                ]
            )
        final_include_regions = (
            splice_include_regions + utr_include_regions + coding_include_regions
        )

        if any(
            (start_position >= p[0] and start_position <= p[1])
            or (open_end_position > p[0] and open_end_position < p[1])
            or (start_position <= p[0] and open_end_position >= p[1])
            for p in final_include_regions
        ):
            assert not result[gp_key]
        else:
            assert result[gp_key] == set(allele_ids)

    @pytest.mark.aa(order=2)
    def test_hgvsc_region_filtering(self, session):
        """
        All variants are outside any transcripts (in genomic position), but are annotated with a genepanel transcript
        with exon_distance or coding_region_distance within splice_region/utr_region
        """
        # Should be saved as annotated with exon_distance -10
        a1, _ = mock_allele_with_annotation(
            session,
            annotations={
                "transcripts": [
                    {
                        "symbol": "GENE1",
                        "hgnc_id": 1,
                        "transcript": "NM_1.1",
                        "exon_distance": -10,
                        "coding_region_distance": None,
                    }
                ]
            },
        )

        # Should be saved as annotated with exon_distance +5
        a2, _ = mock_allele_with_annotation(
            session,
            annotations={
                "transcripts": [
                    {
                        "symbol": "GENE1",
                        "hgnc_id": 1,
                        "transcript": "NM_1.1",
                        "exon_distance": 5,
                        "coding_region_distance": None,
                    }
                ]
            },
        )

        # Should be saved as annotated with coding_region_distance -12
        a3, _ = mock_allele_with_annotation(
            session,
            annotations={
                "transcripts": [
                    {
                        "symbol": "GENE1",
                        "hgnc_id": 1,
                        "transcript": "NM_1.1",
                        "exon_distance": 0,
                        "coding_region_distance": -12,
                    }
                ]
            },
        )

        # Should be saved as annotated with coding_region_distance +20
        a4, _ = mock_allele_with_annotation(
            session,
            annotations={
                "transcripts": [
                    {
                        "symbol": "GENE1",
                        "hgnc_id": 1,
                        "transcript": "NM_1.1",
                        "exon_distance": 0,
                        "coding_region_distance": 20,
                    }
                ]
            },
        )

        na1, _ = mock_allele_with_annotation(
            session,
            annotations={
                "transcripts": [
                    {
                        "symbol": "GENE1",
                        "hgnc_id": 1,
                        "transcript": "TRANSCRIPT_NOT_FOR_FILTERING",
                        "exon_distance": 0,
                        "coding_region_distance": 0,
                    }
                ]
            },
        )

        session.flush()

        gp_key = ("testpanel", "v01")
        allele_ids = [a1.id, a2.id, a3.id, a4.id, na1.id]

        rf = RegionFilter(session, None)
        # Run first with no padding, to make sure that all are filtered out

        config_no_padding = copy.deepcopy(FILTER_CONFIG)
        config_no_padding["splice_region"] = [0, 0]
        config_no_padding["utr_region"] = [0, 0]

        result = rf.filter_alleles({gp_key: allele_ids}, config_no_padding)
        assert result[gp_key] == set(allele_ids)

        # Apply the normal config, to ensure that these are captured by the computed distance
        result = rf.filter_alleles({gp_key: allele_ids}, FILTER_CONFIG)

        assert result[gp_key] == set([na1.id])


@st.composite
def create_transcript(draw):
    """Create a semi-plausible transcript"""
    tx_start = draw(st.integers(min_value=1000, max_value=2000))
    tx_end = draw(st.integers(min_value=3000, max_value=4000))

    # Create exons
    num_exons = draw(st.integers(min_value=1, max_value=7))
    exons = draw(
        st.lists(
            st.integers(min_value=tx_start, max_value=tx_end),
            min_size=2 * num_exons,
            max_size=2 * num_exons,
            unique=True,
        )
    )
    # Sort exons like:
    # [exon_start1, exon_end1, exon_start2, exon_end2, ...]
    exons = list(sorted(exons))

    # Fetch exon starts and exon ends
    exon_starts = exons[::2]
    exon_ends = exons[1::2]

    # Choose exons containing cds_start and cds_end
    cds_exons = draw(
        st.lists(st.integers(min_value=0, max_value=num_exons - 1), min_size=2, max_size=2)
    )
    cds_start_exon, cds_end_exon = tuple(sorted(cds_exons))

    # Generate cds_start and cds_end within given exons
    cds_start = draw(
        st.integers(min_value=exon_starts[cds_start_exon], max_value=exon_ends[cds_start_exon] - 1)
    )
    cds_end = draw(
        st.integers(min_value=exon_starts[cds_end_exon] + 1, max_value=exon_ends[cds_end_exon])
    )

    # Since cds_start_exon could be equal to cds_end_exon, we add a check that the coding region actually has a span
    ht.assume(cds_end > cds_start)

    reversed = draw(st.booleans())

    return gene.Transcript(
        gene=gene.Gene(hgnc_id=int(1e7), hgnc_symbol="REGION_TEST_GENE"),
        transcript_name="NM_REGION_TEST.1",
        type="RefSeq",
        genome_reference="",
        tags=[],
        chromosome="1",
        tx_start=tx_start,
        tx_end=tx_end,
        strand="-" if reversed else "+",
        cds_start=cds_start,
        cds_end=cds_end,
        exon_starts=exon_starts,
        exon_ends=exon_ends,
    )


def default_transcript(**kwargs):
    tx = gene.Transcript(
        gene=gene.Gene(hgnc_id=int(1e7), hgnc_symbol="REGION_TEST_GENE"),
        transcript_name="NM_REGION_TEST.1",
        type="RefSeq",
        genome_reference="",
        tags=[],
        chromosome="1",
        tx_start=1000,
        tx_end=4000,
        strand="+",
        cds_start=1100,
        cds_end=2900,
        exon_starts=[500, 1050, 1700, 2300, 2800, 3500],
        exon_ends=[800, 1150, 2000, 2500, 2990, 3700],
    )

    for k, v in kwargs.items():
        setattr(tx, k, v)
    return tx


@ht.example(
    default_transcript(),
    0,
    (0, 0),
    (0, 0),
    {
        "coding_regions": set([(1100, 1149), (1700, 1999), (2300, 2499), (2800, 2899)]),
        "splice_regions": set(),
        "utr_regions": set(),
    },
)
@ht.example(
    default_transcript(),
    0,
    (-1, 0),
    (-1, 0),
    {
        "coding_regions": set([(1100, 1149), (1700, 1999), (2300, 2499), (2800, 2899)]),
        "splice_regions": set(
            [(499, 499), (1049, 1049), (1699, 1699), (2299, 2299), (2799, 2799), (3499, 3499)]
        ),
        "utr_regions": set([(1099, 1099)]),
    },
)
@ht.example(
    default_transcript(),
    0,
    (0, 2),
    (0, 1),
    {
        "coding_regions": set([(1100, 1149), (1700, 1999), (2300, 2499), (2800, 2899)]),
        "splice_regions": set(
            [(800, 801), (1150, 1151), (2000, 2001), (2500, 2501), (2990, 2991), (3700, 3701)]
        ),
        "utr_regions": set([(2900, 2900)]),
    },
)
# Reverse strand transcripts
@ht.example(
    default_transcript(strand="-"),
    0,
    (0, 0),
    (0, 0),
    {
        "coding_regions": set([(1100, 1149), (1700, 1999), (2300, 2499), (2800, 2899)]),
        "splice_regions": set(),
        "utr_regions": set(),
    },
)
@ht.example(
    default_transcript(strand="-"),
    0,
    (-1, 0),
    (-1, 0),
    {
        "coding_regions": set([(1100, 1149), (1700, 1999), (2300, 2499), (2800, 2899)]),
        "splice_regions": set(
            [(800, 800), (1150, 1150), (2000, 2000), (2500, 2500), (2990, 2990), (3700, 3700)]
        ),
        "utr_regions": set([(2900, 2900)]),
    },
)
@ht.example(
    default_transcript(strand="-"),
    0,
    (0, 2),
    (0, 1),
    {
        "coding_regions": set([(1100, 1149), (1700, 1999), (2300, 2499), (2800, 2899)]),
        "splice_regions": set(
            [(498, 499), (1048, 1049), (1698, 1699), (2298, 2299), (2798, 2799), (3498, 3499)]
        ),
        "utr_regions": set([(1099, 1099)]),
    },
)
@ht.given(
    st.one_of(create_transcript()),
    st.integers(min_value=0),
    st.tuples(st.integers(min_value=-20, max_value=0), st.integers(min_value=0, max_value=20)),
    st.tuples(st.integers(min_value=-20, max_value=0), st.integers(min_value=0, max_value=20)),
    st.just(None),
)
def test_regions(
    session, transcript, allele_offset, splice_region, utr_region, manually_curated_result
):
    session.rollback()

    max_padding = max(abs(x) for x in (*splice_region, *utr_region))
    genepanel = gene.Genepanel(name="testpanel", version="v02", genome_reference="GRCh37")
    session.add(genepanel)
    session.add(transcript)
    session.flush()
    session.execute(
        gene.genepanel_transcript.insert(),
        {
            "transcript_id": transcript.id,
            "genepanel_name": genepanel.name,
            "genepanel_version": genepanel.version,
            "inheritance": "AD/AR",
        },
    )
    session.flush()

    # Add one allele within transcript (+ padding)
    allele_offset = allele_offset % (transcript.tx_end - 1 - transcript.tx_start + 2 * max_padding)
    al = mock_allele(
        session,
        {
            "start_position": transcript.tx_start - max_padding + allele_offset,
            "open_end_position": transcript.tx_start + allele_offset + 1,
        },
    )

    rf = RegionFilter(session, None)
    tmp_gene_padding = rf.create_gene_padding_table(
        [transcript.gene_id], {"splice_region": splice_region, "utr_region": utr_region}
    )

    assert session.query(*tmp_gene_padding.c).all() == [
        (transcript.gene_id, splice_region[0], splice_region[1], utr_region[0], utr_region[1])
    ]

    genepanel_tx_regions = rf.create_genepanel_transcripts_table(
        ("testpanel", "v02"), [al.id], max_padding
    )
    # Check that transcript is included (on basis of allele)
    assert session.query(genepanel_tx_regions).count() == len(transcript.exon_starts)

    # Get the different regions from RegionFilter
    def get_region_tuples(regions):
        return session.query(regions.c.region_start, regions.c.region_end).all()

    coding_regions = get_region_tuples(rf.get_coding_regions(genepanel_tx_regions).subquery())
    splice_regions = get_region_tuples(
        rf.get_splice_regions(genepanel_tx_regions, tmp_gene_padding).subquery()
    )
    utr_regions = get_region_tuples(
        rf.get_utr_regions(genepanel_tx_regions, tmp_gene_padding).subquery()
    )

    if manually_curated_result is not None:
        assert manually_curated_result["coding_regions"] == set(coding_regions)
        assert manually_curated_result["splice_regions"] == set(splice_regions)
        assert manually_curated_result["utr_regions"] == set(utr_regions)

    # Work with positive numbers in the test code
    utr_region = [abs(x) for x in utr_region]
    splice_region = [abs(x) for x in splice_region]

    # Reverse utr_region/splice_region if transcript is reversed
    if transcript.strand == "-":
        utr_region = utr_region[::-1]
        splice_region = splice_region[::-1]

    # Check coding regions
    expected_coding_regions = []
    for exon_start, exon_end in zip(transcript.exon_starts, transcript.exon_ends):
        # Work with closed intervals
        exon_end -= 1
        cds_end = transcript.cds_end - 1

        if exon_end < transcript.cds_start:
            # Exon lies before coding region
            continue
        elif exon_start > cds_end:
            # Exon lies after coding region
            continue

        if transcript.cds_start > exon_start:
            region_start = transcript.cds_start
        else:
            region_start = exon_start

        if cds_end < exon_end:
            region_end = cds_end
        else:
            region_end = exon_end

        expected_coding_regions.append((region_start, region_end))

    assert set(expected_coding_regions) == set(coding_regions)

    # Check utr regions
    expected_utr_regions = []
    if utr_region[0] != 0:
        expected_utr_regions.append(
            (
                transcript.cds_start
                - utr_region[0],  # cds_start is closed, no need to subtract one
                transcript.cds_start - 1,  # Exclude cds_start
            )
        )
    if utr_region[1] != 0:
        # Exclude cds_end (cds_end is open_ended, but interval should be closed)
        expected_utr_regions.append(
            (
                transcript.cds_end,  # Subtract one to close interval, add one to exclude cds_end (cds_end == cds_end - 1 + 1)
                transcript.cds_end - 1 + utr_region[1],  # Subtract one to close interval
            )
        )

    # Check length of regions compared with config (add one since cds_start/cds_end is excluded)
    for region in utr_regions:
        assert (region[1] - region[0] + 1) in utr_region

    # Check that regions are the same
    assert set(expected_utr_regions) == set(utr_regions)

    # Check splice regions
    expected_splice_regions = []
    if splice_region[0] != 0:
        for exon_start in transcript.exon_starts:
            expected_splice_regions.append(
                (
                    exon_start - splice_region[0],  # exon_start is closed, no need to subtract one
                    exon_start - 1,  # Exclude exon_start
                )
            )
    if splice_region[1] != 0:
        for exon_end in transcript.exon_ends:
            # Exclude exon_end (exon_end is open_ended, but interval should be closed)
            expected_splice_regions.append(
                (
                    exon_end,  # Subtract one to close interval, add one to exclude exon_end (exon_end == exon_end - 1 + 1)
                    exon_end - 1 + splice_region[1],  # Subtract one to close interval
                )
            )

    # Check length of regions compared with config (add one since exon_start/exon_end is excluded)
    for region in splice_regions:
        assert (region[1] - region[0] + 1) in splice_region

    # Check that regions are the same
    assert set(expected_splice_regions) == set(splice_regions)
