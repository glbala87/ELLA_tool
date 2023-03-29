import pytest
from .. import pubmed_parser
import xml.etree.ElementTree as ET
import os.path as path

"""
This module tests pubmed_parser.py on test_data/TESTFILE

Tested formatting:
- One section abstract
- Two authors
- Abstract several sections
- One author
- No issue
- No abstract
- No volume, no issue, no pages
- More than 2 authors
- CollectiveName are caught when no LastName field
- MedlineDate are caught when no Year field
- Journal title when no ISOAbbreviation (resort to Title)
"""


# The Pubmed IDs that are used for testing
TEST_PMIDS = [
    11485765,
    8896564,
    24122059,
    23374456,
    21550946,
    16160809,
    24891336,
    24432435,
    20301425,
]
# Contains xml of Entrez query for TEST_PMIDS
TESTDATA = path.join(path.dirname(__file__), "test_data")


def provide_generator_of_articles():
    pmparser = pubmed_parser.PubMedParser()
    for pmid in TEST_PMIDS:
        with open(f"{TESTDATA}/{pmid}.xml", "r") as f:
            xml_raw = f.read()
        yield pmparser.parse_pubmed_article(ET.fromstring(xml_raw))
        with open(f"{TESTDATA}/{pmid}.pubmed", "r") as f:
            pubmed_raw = f.read()
        yield pmparser.from_medline(pubmed_raw)


@pytest.fixture(params=provide_generator_of_articles())
def test_references(request):
    return request.param


def test_parse_pubmed_article(test_references):
    reference = test_references
    match reference.pubmed_id:
        case 11485765:
            # Test that MedlineDate are caught when no Year field
            assert reference.year == "2001 Jul-Aug"
        case 8896564:
            # Test that CollectiveName are caught when no LastName field
            assert reference.authors == "Fanconi anaemia/Breast cancer consortium"
        case 24122059:
            # Test that more than 2 authors are treated well
            assert reference.authors == "Maggi L et al."
            # Test for no volume, no issue, no pages
            assert reference.journal in ["J. Neurol.: ", "J Neurol"]
            # Test for no abstract
            assert reference.abstract is None
        case 23374456:
            # Test for no issue
            assert reference.journal == "J Med Case Rep: 7, 35"
        case 21550946:
            # Test one author
            assert reference.authors == "Lietman SA"
            # Test abstract several sections
            assert (
                reference.abstract
                == "OBJECTIVE: To describe the process of preimplantation genetic diagnosis (PGD), "
                "which allows the selection of embryos without mutations for implantation, "
                "with specific application for mutations in GNAS.\n"
                "METHODS: We identified a GNAS mutation in a patient with a severe form of Albright "
                "hereditary osteodystrophy and pseudohypoparathyroidism type 1a with phocomelia and "
                "performed PGD on embryos derived by in vitro fertilization in order to deliver an "
                "unaffected infant.\n"
                "RESULTS: After in vitro fertilization, embryos that were homozygous normal for GNAS were "
                "identified and implanted into the mother. Ultrasonography 34 days after embryo "
                "transfer showed a viable singleton intrauterine pregnancy. A normal-appearing male "
                "infant was born at 36.5 weeks of gestation. Newborn screening revealed normal "
                "results of thyroid function tests, and a buccal swab obtained when the child "
                "was 1 year old verified normal GNAS gene sequences.\n"
                "CONCLUSION: PGD is an alternative that "
                "can be offered for many genetic diseases and represents a method to decrease and "
                "potentially eliminate the transmission of severe genetic diseases. Patients with "
                "multiple endocrine neoplasia (MEN) type 2 with known RET gene mutations as well as "
                "those with other heritable disorders are candidates for PGD. Successful PGD in "
                "patients with MEN has not yet been reported and has met with some early difficulties, "
                "but it is believed that this technique will eventually be successful for MEN and "
                "other hereditary endocrine disorders."
            )
        case 16160809:
            # Test two authors
            assert reference.authors == "Ptok M & Morlot S"
            # Test one section abstract
            assert (
                reference.abstract
                == "Waardenburg syndrome (WS) type 1 occurs due to a mutation in the PAX3-gene on "
                "the long arm of chromosome 2. It is an autosomal dominant mutation with highly "
                "variable expression and high penetrance. Symptoms include the absence of melanocytes "
                "in the skin, hair, eyes and cochlea due to an early developmental disturbance in "
                "melancoytes from the neural crest. An inner ear disturbance is characteristic. Here "
                "we present a 4 year old girl with unilateral hearing loss, dystopia canthorum and "
                "partial albinism. Screening the entire PAX 3 gene revealed C64A und T164A mutations "
                "in exon I und II, both being missense mutations. Neither mutation has not been "
                "reported previously."
            )
        case 24891336:
            # Test journal title when no ISOAbbreviation
            assert reference.journal == "Arthritis & rheumatology (Hoboken, N.J.): 66(9), 2621-7"
        case 24432435:
            # Test title of entire book
            assert (
                reference.title
                == "Risk Assessment, Genetic Counseling, and Genetic Testing for BRCA-Related Cancer: "
                "Systematic Review to Update the U.S. Preventive Services Task Force Recommendation"
            )
            # Test 'journal' name which is an entire book
            assert (
                reference.journal
                == "Agency for Healthcare Research and Quality (US), Rockville (MD)."
            )
        case 20301425:
            # Test title which is an article in a book of articles
            assert reference.title == "BRCA1 and BRCA2 Hereditary Breast and Ovarian Cancer"
            # Test 'journal' name which is a book of articles
            assert (
                reference.journal
                == "In: Pagon RA et al. (eds)., GeneReviews(\xae), University of Washington, Seattle, Seattle (WA)."
            )
        case _:
            raise ValueError("Test not implemented for PMID: {}".format(reference.pubmed_id))
