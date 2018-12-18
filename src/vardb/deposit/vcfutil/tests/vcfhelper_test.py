# -*- coding: utf-8 -*-
"""
Tests for vcfcreator module.

      x x x            (Nucleotides 2, 3, and 4 on forward [2,5)
  0 1 2 3 4 5 6 7 8 9 Forward strand coordinates (first base is 0)
"""


import unittest

import mox
from pyfaidx import Fasta

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


class TestVCFAlleleCreator(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        # self.seqdb = self.mox.CreateMockAnything()
        self.seqdb = self.mox.CreateMock(Fasta)
        self.v = vc.VCFAlleleCreator(self.seqdb, useGenomeRef=False)

    def tearDown(self):
        self.mox.UnsetStubs()

    def mockseq(self, chromosome, start, stop, returnValue):
        """Helps registering expectations for calls to the self.seqdb mock"""
        # Skip registering str() on seqdb, not necessary.
        self.seqdb[chromosome].AndReturn(self.mox.CreateMockAnything())[start:stop].AndReturn(
            returnValue
        )

    def test_snp(self):
        ##self.seqdb['1'].AndReturn(self.mox.CreateMockAnything())[10:11].AndReturn('A')
        self.mockseq("1", 10, 11, "A")
        self.mockseq("1", 5, 6, "A")
        self.mox.ReplayAll()
        self.assertEqual(self.v.snp("1", 10, "A", "T", "id1"), ("1", "11", "id1", "A", "T"))
        self.assertEqual(self.v.snp("1", 5, "A", "G", "id2"), ("1", "6", "id2", "A", "G"))
        self.mox.VerifyAll()

    def test_snp_when_useGenomeRef(self):
        """VCFAlleleCreator outputs ref from reference genome if its attribute 'useGenomeRef' is True"""
        self.v.useGenomeRef = True
        self.mockseq("1", 10, 11, "A")
        self.mockseq("1", 5, 6, "A")
        self.mox.ReplayAll()
        self.assertEqual(self.v.snp("1", 10, "C", "T", "id1"), ("1", "11", "id1", "A", "T"))
        self.assertEqual(self.v.snp("1", 5, "C", "G", "id2"), ("1", "6", "id2", "A", "G"))
        self.mox.VerifyAll()

    def test_snp_verifies_reference(self):
        """VCFCreator maintains a list of those that failed reference match"""
        self.mockseq("1", 10, 11, "G")  # G, not A
        self.mox.ReplayAll()
        self.assertEqual(self.v.snp("1", 10, "A", "T", "id1"), ("1", "11", "id1", "A", "T"))
        self.assertEqual(
            self.v.refMismatch, [("SNP", "G", "1", 10, "A", "T", "id1")]
        )  # type, genomeref, restofinput
        self.mox.VerifyAll()

    def test_insertion(self):
        self.mockseq("1", 10, 11, "T")
        self.mockseq("1", 5, 6, "C")
        self.mox.ReplayAll()
        self.assertEqual(self.v.insertion("1", 10, "AAA", "id1"), ("1", "11", "id1", "T", "TAAA"))
        self.assertEqual(self.v.insertion("1", 5, "C"), ("1", "6", ".", "C", "CC"))
        self.mox.VerifyAll()

    def test_deletion(self):
        self.mockseq("1", 10, 13, "AAA")
        self.mockseq("1", 9, 10, "T")
        self.mox.ReplayAll()
        self.assertEqual(self.v.deletion("1", 10, 13, "AAA"), ("1", "10", ".", "TAAA", "T"))
        self.mox.VerifyAll()

    def test_deletion_when_useGenomeRef(self):
        self.v.useGenomeRef = True
        self.mockseq("1", 10, 13, "AAA")
        self.mockseq("1", 9, 10, "T")
        self.mox.ReplayAll()
        self.assertEqual(self.v.deletion("1", 10, 13, "AAT"), ("1", "10", ".", "TAAA", "T"))
        self.mox.VerifyAll()

    def test_deletion_verifies_reference(self):
        self.mockseq("1", 10, 13, "CCC")
        self.mockseq("1", 9, 10, "T")
        self.mox.ReplayAll()
        self.assertEqual(self.v.deletion("1", 10, 13, "AAA"), ("1", "10", ".", "TAAA", "T"))
        self.assertEqual(self.v.refMismatch, [("DEL", "CCC", "1", 10, 13, "AAA", ".")])
        self.mox.VerifyAll()

    def test_giving_deleted_sequence_is_optional(self):
        """If deleted sequence not given, use refAtPosition."""
        self.mockseq("1", 10, 13, "AAA")
        self.mockseq("1", 9, 10, "T")
        self.mox.ReplayAll()
        self.assertEqual(self.v.deletion("1", 10, 13, ""), ("1", "10", ".", "TAAA", "T"))
        self.mox.VerifyAll()

    def test_indel(self):
        """Delins, deletion followed by insertion."""
        self.mockseq("1", 10, 13, "AAA")
        self.mockseq("1", 9, 10, "T")
        self.mox.ReplayAll()
        self.assertEqual(self.v.indel("1", 10, 13, "G", "AAA"), ("1", "10", ".", "TAAA", "TG"))
        self.mox.VerifyAll()

    def test_indel_when_useGenomeRef(self):
        self.v.useGenomeRef = True
        self.mockseq("1", 10, 13, "AAA")
        self.mockseq("1", 9, 10, "T")
        self.mox.ReplayAll()
        self.assertEqual(self.v.indel("1", 10, 13, "G", "CCC"), ("1", "10", ".", "TAAA", "TG"))
        self.mox.VerifyAll()

    def test_duplication(self):
        self.mockseq("1", 10, 13, "AAA")
        self.mox.ReplayAll()
        self.assertEqual(self.v.duplication("1", 10, 13, "AAA"), ("1", "11", ".", "AAA", "AAAAAA"))
        self.mox.VerifyAll()

    def test_duplication_when_useGenomeRef(self):
        self.v.useGenomeRef = True
        self.mockseq("1", 10, 13, "AAA")
        self.mox.ReplayAll()
        self.assertEqual(self.v.duplication("1", 10, 13, "CCC"), ("1", "11", ".", "AAA", "AAAAAA"))
        self.mox.VerifyAll()


if __name__ == "__main__":
    unittest.main(exit=False)
