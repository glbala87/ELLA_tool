"""
Integration/unit test for the AlleleFilter module.
Since it consists mostly of database queries, it's tested on a live database.
"""
import copy
import pytest

from api.allelefilter.polypyrimidinetractfilter import PolypyrimidineTractFilter
from vardb.datamodel import allele, annotation, gene, annotationshadow, assessment

import hypothesis as ht
import hypothesis.strategies as st


GLOBAL_CONFIG = {}


def check_valid_allele(vcf_ref, vcf_alt):
    ht.assume(vcf_ref != vcf_alt)


@st.composite
def allele_positions(draw, chromosome, start, end):
    start_position = draw(st.integers(min_value=start, max_value=end))
    # end_position = draw(st.integers(min_value=start_position+1, max_value=start_position+50))
    vcf_ref = draw(st.text(alphabet=["A", "C", "G","T"], min_size=1, max_size=2))
    vcf_alt = draw(st.text(alphabet=["A", "C", "G","T"], min_size=1, max_size=2))
    ht.assume(vcf_alt != vcf_ref)
    ht.assume(vcf_ref[0] != vcf_alt[0] or len(vcf_alt) != len(vcf_ref))
    ht.assume(not (vcf_ref[0] == vcf_alt[0] and len(vcf_alt) > 1 and len(vcf_ref) > 1))

    return (chromosome, start_position, vcf_ref, vcf_alt)


allele_start = 1300


def create_allele(data=None):
    global allele_start
    allele_start += 1
    default_allele_data = {
            "chromosome": "1",
            "start_position": allele_start,
            # "open_end_position": allele_start+1,
            # "change_from": "A",
            # "change_to": "T",
            # "change_type": "SNP",
            "vcf_pos": allele_start+1,
            "vcf_ref": "A",
            "vcf_alt": "T"
        }
    if data:
        for k in data:
            assert k not in ["change_from", "change_to"], "Use vcf_ref and vcf_alt to set allele"
            default_allele_data[k] = data[k]
    data = default_allele_data

    if len(data['vcf_ref']) == len(data['vcf_alt']) == 1:
        data["change_from"] = data['vcf_ref']
        data["change_to"] = data["vcf_alt"]
        data["change_type"] = "SNP"
        data["open_end_position"] = data["start_position"] + 1
    elif len(data["vcf_ref"]) > len(data["vcf_alt"]) and len(data["vcf_alt"]) == 1:
        data["change_from"] = data["vcf_ref"][1:]
        data["change_to"] = ""
        data["change_type"] = "del"
        data["open_end_position"] = data["start_position"] + len(data["change_from"])
    elif len(data["vcf_ref"]) < len(data["vcf_alt"]) and len(data["vcf_ref"]) == 1:
        if data["vcf_ref"][0] == data["vcf_alt"][0]:
            data["change_from"] = ""
            data["change_to"] = data["vcf_alt"][1:]
            data["change_type"] = "ins"
            data["open_end_position"] = data["start_position"] + len(data["change_to"])
        else:
            data["change_from"] = data["vcf_ref"]
            data["change_to"] = data["vcf_alt"]
            data["change_type"] = "indel"
            data["open_end_position"] = data["start_position"] + max([len(data["change_from"]), len(data["change_to"])])
    elif len(data["vcf_ref"]) > 1 and len(data["vcf_alt"]) > 1:
        assert data["vcf_ref"][0] != data["vcf_alt"][0]
        data["change_from"] = data["vcf_ref"]
        data["change_to"] = data["vcf_alt"]
        data["change_type"] = "indel"
    else:
        raise ValueError("Unable to determine change type from vcf_ref ({}) and vcf_alt ({})".format(data["vcf_ref"], data["vcf_alt"]))

    if data["change_type"] == "SNP":
        data["open_end_position"] = data["start_position"] + 1
    elif data["change_type"] == "del":
        data["open_end_position"] = data["start_position"] + len(data["change_from"])
    elif data["change_type"] == "ins":
        data["open_end_position"] = data["start_position"] + len(data["change_to"])
    elif data["change_type"] == "indel":
        data["open_end_position"] = data["start_position"] + max([len(data["change_from"]), len(data["change_to"])])

    return allele.Allele(
        genome_reference="GRCh37",
        **data
    )


def create_annotation(annotations, allele=None):
    return annotation.Annotation(
        annotations=annotations,
        allele=allele
    )


def create_allele_with_annotation(session, annotations=None, allele_data=None):
    al = create_allele(data=allele_data)
    session.add(al)
    if annotations is not None:
        an = create_annotation(annotations, allele=al)
        session.add(an)
    else:
        an = None

    return al, an


def create_genepanel(genepanel_config):
    # Create fake genepanel for testing purposes

    g1_ad = gene.Gene(hgnc_id=int(1e6), hgnc_symbol="GENE1AD")
    g1_ar = gene.Gene(hgnc_id=int(2e6), hgnc_symbol="GENE1AR")
    g2 = gene.Gene(hgnc_id=int(3e6), hgnc_symbol="GENE2")
    g3 = gene.Gene(hgnc_id=int(4e6), hgnc_symbol="GENE3")
    g4 = gene.Gene(hgnc_id=int(5e6), hgnc_symbol="GENE4")
    g5 = gene.Gene(hgnc_id=int(6e6), hgnc_symbol="GENE5")

    t1_ad = gene.Transcript(
        gene=g1_ad,
        transcript_name='NM_1AD.1',
        type='RefSeq',
        genome_reference='',
        chromosome='1',
        tx_start=1000,
        tx_end=1500,
        strand='+',
        cds_start=1230,
        cds_end=1430,
        exon_starts=[1100, 1200, 1300, 1400],
        exon_ends=[1160, 1260, 1360, 1460]
    )

    t1_ar = gene.Transcript(
        gene=g1_ar,
        transcript_name='NM_1AR.1',
        type='RefSeq',
        genome_reference='',
        chromosome='1',
        tx_start=1000,
        tx_end=1500,
        strand='+',
        cds_start=1230,
        cds_end=1430,
        exon_starts=[1100, 1200, 1300, 1400],
        exon_ends=[1160, 1260, 1360, 1460]
    )

    t2 = gene.Transcript(
        gene=g2,
        transcript_name='NM_2.1',
        type='RefSeq',
        genome_reference='',
        chromosome='2',
        tx_start=2000,
        tx_end=2500,
        strand='+',
        cds_start=2230,
        cds_end=2430,
        exon_starts=[2100, 2200, 2300, 2400],
        exon_ends=[2160, 2260, 2360, 2460]
    )

    t3 = gene.Transcript(
        gene=g3,
        transcript_name='NM_3.1',
        type='RefSeq',
        genome_reference='',
        chromosome='3',
        tx_start=3000,
        tx_end=3500,
        strand='+',
        cds_start=3230,
        cds_end=3430,
        exon_starts=[3100, 3200, 3300, 3400],
        exon_ends=[3160, 3260, 3360, 3460]
    )

    t4 = gene.Transcript(
        gene=g4,
        transcript_name='NM_4.1',
        type='RefSeq',
        genome_reference='',
        chromosome='4',
        tx_start=4000,
        tx_end=4500,
        strand='+',
        cds_start=4230,
        cds_end=4430,
        exon_starts=[4100, 4200, 4300, 4400],
        exon_ends=[4160, 4260, 4360, 4460]
    )

    t5_reverse = gene.Transcript(
        gene=g5,
        transcript_name='NM_5.1',
        type='RefSeq',
        genome_reference='',
        chromosome='5',
        tx_start=5000,
        tx_end=5500,
        strand='-',
        cds_start=5230,
        cds_end=5430,
        exon_starts=[5100, 5200, 5300, 5400],
        exon_ends=[5160, 5260, 5360, 5460]
    )

    p1 = gene.Phenotype(
        gene=g1_ad,
        inheritance='AD',
        description='P1'
    )

    p2 = gene.Phenotype(
        gene=g1_ar,
        inheritance='AD,AR',
        description='P2'
    )

    genepanel = gene.Genepanel(
        name='testpanel',
        version='v01',
        genome_reference='GRCh37'
    )

    genepanel.transcripts = [t1_ad, t1_ar, t2, t3, t4, t5_reverse]
    genepanel.phenotypes = [p1, p2]
    return genepanel


class TestPolypyrimidineTractFilter(object):

    @pytest.mark.aa(order=0)
    def test_prepare_data(self, test_database, session):
        test_database.refresh()  # Reset db

        gp = create_genepanel({})
        session.add(gp)
        session.commit()

    @pytest.mark.aa(order=1)
    @ht.example(('1', 1290, "C", "T"), True)
    @ht.example(('1', 1290, "G", "T"), False)
    @ht.example(('1', 1280, "AC", "A"), False)
    @ht.example(('1', 1280, "CT", "C"), True)
    @ht.example(('1', 1397, 'C', 'T'), True)
    @ht.given(
        st.one_of(
            allele_positions('1', 900, 1600),  # t1, positive strand
            allele_positions('5', 4900, 5600)),  # t5, negative strand
        st.just(None)
    )
    @ht.settings(deadline=1500)
    def test_genomic_region_filtering(self, session, positions, manually_curated_result):
        """
        Tests both using manually curated test and parallell implementation in Python.
        """

        chromosome, start_position, vcf_ref, vcf_alt = positions
        al, _ = create_allele_with_annotation(session,
            None,
            {
                "chromosome": chromosome,
                "start_position": start_position,
                "vcf_ref": vcf_ref,
                "vcf_alt": vcf_alt
            }
        )

        session.flush()

        ppy_tract_region = [-20, -3]
        filter_config = {
            'ppy_tract_region': ppy_tract_region
        }

        allele_ids = [al.id]
        gp_key = ('testpanel', 'v01')
        ppyf = PolypyrimidineTractFilter(session, GLOBAL_CONFIG)
        result = ppyf.filter_alleles({gp_key: allele_ids}, filter_config)

        # Manually curated test cases
        if manually_curated_result is not None:
            if manually_curated_result:
                assert result[gp_key] == set(allele_ids)
            else:
                assert result[gp_key] == set([])

        if al.change_type not in ["del", "SNP"]:
            assert result[gp_key] == set()
        elif len(al.change_from) > 2 or len(al.change_to) > 1:
            assert result[gp_key] == set()

        genepanel = session.query(gene.Genepanel).filter(
            gene.Genepanel.name == 'testpanel',
            gene.Genepanel.version == 'v01'
        ).one()

        ppy_regions = []
        for transcript in genepanel.transcripts:
            for es, ee in zip(transcript.exon_starts, transcript.exon_ends):
                if transcript.strand == '+':
                    ppy_regions.append(
                        (
                            es + ppy_tract_region[0],
                            es + ppy_tract_region[1],
                            transcript.strand
                        )
                    )
                else:
                    ppy_regions.append(
                        (
                            ee - ppy_tract_region[1],
                            ee - ppy_tract_region[0],
                            transcript.strand
                        )
                    )

        region = next((p for p in ppy_regions if (
            (al.start_position >= p[0] and al.start_position <= p[1]) or
            (al.open_end_position > p[0] and al.open_end_position < p[1]) or
            (al.start_position <= p[0] and al.open_end_position > p[1]))
            ), None)

        if not region:
            assert result[gp_key] == set()
        else:
            strand = region[2]
            if strand == '+' and al.change_type == 'SNP' and set(al.change_from + al.change_to) == set('CT'):
                assert result[gp_key] == set([al.id])
            elif strand == '-' and al.change_type == 'SNP' and set(al.change_from + al.change_to) == set('GA'):
                assert result[gp_key] == set([al.id])
            elif strand == '+' and al.change_type == 'del' and set(al.change_from) - set('CT') == set() and al.vcf_alt != 'A' and len(al.change_from) <= 2:
                assert result[gp_key] == set([al.id])
            elif strand == '-' and al.change_type == 'del' and set(al.change_from) - set('GA') == set() and al.vcf_alt != 'G' and len(al.change_from) <= 2:
                assert result[gp_key] == set([al.id])
            else:
                assert result[gp_key] == set()

