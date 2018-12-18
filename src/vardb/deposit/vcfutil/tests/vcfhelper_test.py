# -*- coding: utf-8 -*-
"""
Tests for vcfcreator module.

      x x x            (Nucleotides 2, 3, and 4 on forward [2,5)
  0 1 2 3 4 5 6 7 8 9 Forward strand coordinates (first base is 0)
"""

import unittest
from .. import vcfhelper as vc


class TestVCFHelperFunctions(unittest.TestCase):
    def setUp(self):
        """
        Set up data to be tested in the dictionary form: [input, output]
        [(ref, alt),
         (start offset, length, changeType, changeFrom, changeTo)]
        """
        self.data = [
            [("C", "T"), (0, 1, "SNP", "C", "T")],
            [("CT", "AG"), (0, 2, "indel", "CT", "AG")],
            [("C", "AG"), (0, 2, "indel", "C", "AG")],
            [("A", "TTT"), (0, 3, "indel", "A", "TTT")],
            [("A", "ATT"), (1, 2, "ins", "", "TT")],
            [("AT", "ATT"), (1, 1, "ins", "", "T")],
            [("AAT", "ATT"), (1, 1, "SNP", "A", "T")],
            [("AA", "T"), (0, 2, "indel", "AA", "T")],
            [("AT", "A"), (1, 1, "del", "T", "")],
            [("AT", "T"), (0, 1, "del", "A", "")],
            [("CTCC", "CCCC"), (1, 1, "SNP", "T", "C")],
            [("CTCC", "CCC"), (1, 1, "del", "T", "")],
            [("CTCC", "CTC"), (2, 1, "del", "C", "")],
            [("CTAG", "CTG"), (2, 1, "del", "A", "")],
            [("CTCC", "CTACC"), (2, 1, "ins", "", "A")],
            [("TCAGCAGCAG", "TCAGCAG"), (1, 3, "del", "CAG", "")],
            [("CTT", "CTTT"), (1, 1, "ins", "", "T")],
            [("CTT", "C"), (1, 2, "del", "TT", "")],
            [("CTT", "CT"), (1, 1, "del", "T", "")],
            [("AAAATATATATAT", "A"), (1, 12, "del", "AAATATATATAT", "")],
            [("AAAATATATATAT", "AATAT"), (1, 8, "del", "AAATATAT", "")],
            [("ACACACACAC", "AACAC"), (1, 5, "del", "CACAC", "")],
            [("ACCCC", "AC"), (1, 3, "del", "CCC", "")],
        ]

    def test_compare_alleles(self):
        for data in self.data:
            self.assertEqual(vc.compare_alleles(*data[0]), data[1])
        self.assertRaises(AssertionError, vc.compare_alleles, "A", "")
        self.assertRaises(AssertionError, vc.compare_alleles, "", "AA")

    def test_get_start_position_for_SNPs(self):
        """Convert VCF pos to zero-based and add startOffset (usually zero)."""
        self.assertEqual(vc.get_start_position(10, 0, "SNP"), 9)
        self.assertEqual(vc.get_start_position(1, 0, "SNP"), 0)
        # A SNP with startoffset>0 should only occur if in/del in same record
        self.assertEqual(vc.get_start_position(10, 1, "SNP"), 10)

    def test_get_start_position_for_deletions(self):
        """Deletions and indels start with the first deleted base (zero-based)."""
        self.assertEqual(vc.get_start_position(2, 1, "del"), 2)
        self.assertEqual(vc.get_start_position(10, 10, "del"), 19)
        self.assertEqual(vc.get_start_position(2, 1, "indel"), 2)

    def test_get_start_position_for_insertions(self):
        """VCF position is the 1-based before insertion, (startoffset is usually 1).

        We store the pos of first inserted base 'after' last ref base, zero-based.
        VCF 3 A  ATTT --> insert TTT at 1-based 4 which is 4-1 = 0-based 3.
        VCF 3 AGG  AGGTTTT --> insert at 1-based 6 = 0-based 5.
        """
        self.assertEqual(vc.get_start_position(3, 1, "ins"), 3)
        self.assertEqual(vc.get_start_position(3, 3, "ins"), 5)

    def test_get_end_position(self):
        """VCF position - 1 + startoffset + alleleLength"""
        self.assertEqual(vc.get_end_position(10, 0, 1), 10)
        self.assertEqual(vc.get_end_position(1, 0, 1), 1)
        self.assertEqual(vc.get_end_position(10, 10, 50), 69)

    def test_translates_illegal_characters(self):
        """Can translate VCF-illegal characters ,;= and space"""
        self.assertEqual(vc.translate_illegal("EFF=nasty"), "EFF@#EQnasty")
        self.assertEqual(vc.translate_illegal("EFF,nasty"), "EFF@#CMnasty")
        self.assertEqual(vc.translate_illegal("EFF nasty"), "EFF@#SPnasty")
        self.assertEqual(vc.translate_illegal("EFF\tnasty"), "EFF@#TAnasty")
        self.assertEqual(vc.translate_illegal("EFF\t nasty"), "EFF@#TA@#SPnasty")
        self.assertEqual(
            vc.translate_illegal("EFF=nasty, and,;"), "EFF@#EQnasty@#CM@#SPand@#CM@#SC"
        )
        self.assertEqual(vc.translate_illegal("EFF   spaces"), "EFF@#SP@#SP@#SPspaces")

    def test_translates_back_to_original_characters(self):
        """Can translate substitutions back to original characters"""
        self.assertEqual(vc.translate_to_original("EFF@#EQnasty"), "EFF=nasty")
        self.assertEqual(vc.translate_to_original("EFF@#CMnasty"), "EFF,nasty")
        self.assertEqual(vc.translate_to_original("EFF@#TAnasty"), "EFF\tnasty")
        self.assertEqual(
            vc.translate_to_original("EFF@#EQnasty@#CM@#SPand@#CM@#SC"), "EFF=nasty, and,;"
        )
        self.assertEqual(vc.translate_to_original("EFF@#SP@#SP@#SPspaces"), "EFF   spaces")

    def test_translations_tackle_unicode_strings(self):
        """Note: Returns strings, not unicode, even when given unicode input"""
        self.assertEqual(vc.translate_illegal("EFF=nasty"), "EFF@#EQnasty")
        self.assertEqual(vc.translate_to_original("EFF@#EQnasty"), "EFF=nasty")

