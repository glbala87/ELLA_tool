import pytest
from vardb.deposit.vcfutil.vcfhelper import (
    get_end_position,
    get_start_position,
    compare_alleles,
    translate_illegal,
    translate_to_original,
)


def test_compare_alleles():
    # Set up data to be tested in the dictionary form: [input, output]
    # [(ref, alt), (start offset, length, changeType, changeFrom, changeTo)]
    data = [
        # SNP
        [("C", "T"), (0, 1, "SNP", "C", "T")],
        [("CTCC", "CCCC"), (1, 1, "SNP", "T", "C")],
        [("AAT", "ATT"), (1, 1, "SNP", "A", "T")],
        # ins
        [("A", "ATT"), (0, 2, "ins", "", "TT")],
        [("AT", "ATT"), (0, 1, "ins", "", "T")],
        [("CTCC", "CTACC"), (1, 1, "ins", "", "A")],
        [("CTT", "CTTT"), (0, 1, "ins", "", "T")],
        # del
        [("AT", "A"), (1, 1, "del", "T", "")],
        [("AT", "T"), (0, 1, "del", "A", "")],
        [("CTCC", "CCC"), (1, 1, "del", "T", "")],
        [("CTCC", "CTC"), (2, 1, "del", "C", "")],
        [("CTAG", "CTG"), (2, 1, "del", "A", "")],
        [("CTT", "C"), (1, 2, "del", "TT", "")],
        [("CTT", "CT"), (1, 1, "del", "T", "")],
        [("TCAGCAGCAG", "TCAGCAG"), (1, 3, "del", "CAG", "")],
        [("AAAATATATATAT", "A"), (1, 12, "del", "AAATATATATAT", "")],
        [("AAAATATATATAT", "AATAT"), (1, 8, "del", "AAATATAT", "")],
        [("ACACACACAC", "AACAC"), (1, 5, "del", "CACAC", "")],
        [("ACCCC", "AC"), (1, 3, "del", "CCC", "")],
        # indel
        [("AA", "T"), (0, 2, "indel", "AA", "T")],
        [("CT", "AG"), (0, 2, "indel", "CT", "AG")],
        [("C", "AG"), (0, 2, "indel", "C", "AG")],
        [("A", "TTT"), (0, 3, "indel", "A", "TTT")],
        [("CAG", "CTTTG"), (1, 3, "indel", "A", "TTT")],
    ]
    for input, output in data:
        assert compare_alleles(*input) == output
    with pytest.raises(AssertionError):
        compare_alleles("A", "")
    with pytest.raises(AssertionError):
        compare_alleles("", "AA")


def test_get_start_position_for_SNPs():
    """Convert VCF pos to zero-based and add startOffset."""
    assert get_start_position(10, 0) == 9
    assert get_start_position(1, 0) == 0
    assert get_start_position(10, 1) == 10
    assert get_start_position(2, 1) == 2
    assert get_start_position(10, 10) == 19
    assert get_start_position(2, 1) == 2
    assert get_start_position(3, 1) == 3
    assert get_start_position(3, 3) == 5


def test_get_end_position():
    """VCF position - 1 + startoffset + alleleLength"""
    assert get_end_position(10, 0, 1) == 10
    assert get_end_position(1, 0, 1) == 1
    assert get_end_position(10, 10, 50) == 69


def test_translates_illegal_characters():
    """Can translate VCF-illegal characters ,;= and space"""
    assert translate_illegal("EFF=nasty") == "EFF@#EQnasty"
    assert translate_illegal("EFF,nasty") == "EFF@#CMnasty"
    assert translate_illegal("EFF nasty") == "EFF@#SPnasty"
    assert translate_illegal("EFF\tnasty") == "EFF@#TAnasty"
    assert translate_illegal("EFF\t nasty") == "EFF@#TA@#SPnasty"
    assert translate_illegal("EFF=nasty, and,;") == "EFF@#EQnasty@#CM@#SPand@#CM@#SC"
    assert translate_illegal("EFF   spaces") == "EFF@#SP@#SP@#SPspaces"


def test_translates_back_to_original_characters():
    """Can translate substitutions back to original characters"""
    assert translate_to_original("EFF@#EQnasty") == "EFF=nasty"
    assert translate_to_original("EFF@#CMnasty") == "EFF,nasty"
    assert translate_to_original("EFF@#TAnasty") == "EFF\tnasty"
    assert translate_to_original("EFF@#EQnasty@#CM@#SPand@#CM@#SC") == "EFF=nasty, and,;"
    assert translate_to_original("EFF@#SP@#SP@#SPspaces") == "EFF   spaces"


def test_translations_tackle_unicode_strings():
    """Note: Returns strings, not unicode, even when given unicode input"""
    assert translate_illegal("EFF=nasty") == "EFF@#EQnasty"
    assert translate_to_original("EFF@#EQnasty") == "EFF=nasty"
