#!/usr/bin/env python
"""
Module for VCF helper functions.

Methods in VCFAlleleCreator class can create correct alleles and vcf position
which is useful when making VCF files from scratch.
"""

import re
import sys


class VCFAlleleCreator(object):
    """
    Creates first VCF fields (chromosome, position, ref, alt, id)
    given zero-based genomic positions.
    Verifies that given reference matches what is found in genome at given coordinates.
    """

    def __init__(self, seqdb, useGenomeRef=True):
        self.seqdb = seqdb
        self.useGenomeRef = useGenomeRef
        self.refMismatch = []

    def _refMatch(self, refAtPosition, ref):
        return refAtPosition == ref

    def snp(self, chromosome, gPos, ref, alt, id="."):
        """Given zero-based genomic position and other SNP data, return VCF SNP data."""
        assert len(ref) == len(alt) == 1
        assert gPos >= 0
        refAtPosition = str(self.seqdb[chromosome][gPos : gPos + 1]).upper()
        if not self._refMatch(refAtPosition, ref):
            self.refMismatch.append(("SNP", refAtPosition, chromosome, gPos, ref, alt, id))
        vcfPosition = gPos + 1
        if self.useGenomeRef:
            return chromosome, str(vcfPosition), id, refAtPosition, alt
        else:
            return chromosome, str(vcfPosition), id, ref, alt

    def insertion(self, chromosome, gPos, inserted, id="."):
        """Returns VCF insertion data.

        Note that gPos is 0-position before insertion, i.e. the first base in the VCF alleles."""
        assert gPos >= 0
        firstBase = str(self.seqdb[chromosome][gPos : gPos + 1]).upper()
        ref = firstBase
        alt = firstBase + inserted
        vcfPosition = gPos + 1
        return chromosome, str(vcfPosition), id, ref, alt

    def deletion(self, chromosome, gPosStart, gPosEnd, deleted="", id="."):
        """Returns VCF deletion data.

        Note that gPosStart is 0-position at first deleted base,
        gPosEnd is pos after last deleted base (i.e. half-open interval).
        """
        assert gPosStart >= 0 and gPosEnd > 0
        refAtPosition = str(self.seqdb[chromosome][gPosStart:gPosEnd]).upper()
        if deleted != "":
            if len(deleted) != gPosEnd - gPosStart or not self._refMatch(refAtPosition, deleted):
                self.refMismatch.append(
                    ("DEL", refAtPosition, chromosome, gPosStart, gPosEnd, deleted, id)
                )
        firstBase = str(self.seqdb[chromosome][gPosStart - 1 : gPosStart]).upper()
        vcfPosition = gPosStart + 1 - 1
        ref = (
            firstBase + deleted
            if deleted != "" and not self.useGenomeRef
            else firstBase + refAtPosition
        )
        alt = firstBase
        return chromosome, str(vcfPosition), id, ref, alt

    def indel(self, chromosome, gPosStart, gPosEnd, inserted, deleted="", id="."):
        """Returns VCF indel data. Positions as for deletion."""
        assert gPosStart >= 0 and gPosEnd > 0
        refAtPosition = str(self.seqdb[chromosome][gPosStart:gPosEnd]).upper()
        if deleted != "":
            if len(deleted) != gPosEnd - gPosStart or not self._refMatch(refAtPosition, deleted):
                self.refMismatch.append(
                    ("INDEL", refAtPosition, chromosome, gPosStart, gPosEnd, inserted, deleted, id)
                )
        firstBase = str(self.seqdb[chromosome][gPosStart - 1 : gPosStart]).upper()
        vcfPosition = gPosStart + 1 - 1
        ref = (
            firstBase + deleted
            if deleted != "" and not self.useGenomeRef
            else firstBase + refAtPosition
        )
        alt = firstBase + inserted
        return chromosome, str(vcfPosition), id, ref, alt

    def duplication(self, chromosome, gPosStart, gPosEnd, duplicated="", id="."):
        """Returns VCF duplication data. Positions as for deletion."""
        assert gPosStart >= 0 and gPosEnd > 0
        refAtPosition = str(self.seqdb[chromosome][gPosStart:gPosEnd]).upper()
        if duplicated != "":
            if len(duplicated) != gPosEnd - gPosStart or not self._refMatch(
                refAtPosition, duplicated
            ):
                self.refMismatch.append(
                    ("DUP", refAtPosition, chromosome, gPosStart, gPosEnd, duplicated, id)
                )
        vcfPosition = gPosStart + 1
        ref = duplicated if duplicated != "" and not self.useGenomeRef else refAtPosition
        alt = ref + ref
        return chromosome, str(vcfPosition), id, ref, alt

    def write_records_failing_reference_match(self, fileHandle=sys.stderr):
        """Write data of those calls that had given reference data not matching the reference genome.

        If there are any, these should be checked as there is most likely an error in the input data.
        """
        for r in self.refMismatch:
            fileHandle.write("\t".join((str(e) for e in r)) + "\n")


def make_record(alleleFields, qual=".", filter=".", info=".", format="GT", genotype="0/1"):
    return "\t".join(alleleFields + (qual, filter, info, format, genotype)) + "\n"


# --------------------------------


def compare_alleles(ref, alt):
    """Returns start offset, length, changeType, changeFrom, and changeTo
    after comparing alt allele with reference.

    Start offset is the offset of first differing base:
    0 for SNPs, and +1 for insertions/deletions (which must be corrected for).
    length is 1 if SNP, or length of deletion/insertion if del/ins/indel.
    changeType is SNP, ins, del, or indel.
    changeFrom/changeTo is empty string if ins/del respectively,
    for indels changeFrom is what is deleted and changeTo is what is inserted.
    """
    # If it's a simple SNV, don't remap anything
    if len(ref) == 1 and len(alt) == 1:
        return 0, 1, "SNP", ref, alt
    assert len(ref) >= 1 and len(alt) >= 1
    offset = 0
    # strip off identical suffixes
    while (min(len(alt), len(ref)) > 0) and (alt[-1] == ref[-1]):
        alt = alt[:-1]
        ref = ref[:-1]
    # strip off identical prefixes and increment position
    while (min(len(alt), len(ref)) > 0) and (alt[0] == ref[0]):
        alt = alt[1:]
        ref = ref[1:]
        offset += 1
    if len(ref) == len(alt) == 1:
        changeType = "SNP"
    elif len(ref) == 0:
        changeType = "ins"
    elif len(alt) == 0:
        changeType = "del"
    else:
        changeType = "indel"
    return offset, max(len(ref), len(alt)), changeType, ref, alt


def get_start_position(vcfPos, startOffset, changeType):  # changeType not used.
    """Return start position for allele.

    Convert 1-based vcfPos to 0-based and add startOffset."""
    return (vcfPos - 1) + startOffset


def get_end_position(vcfPos, startOffset, alleleLength):
    return (vcfPos - 1) + startOffset + alleleLength


_SUBSTITUTED = (
    re.compile(r"="),
    re.compile(r","),
    re.compile(r";"),
    re.compile(r" "),
    re.compile(r"\t"),
)
_SUBSTITUTION = ("@#EQ", "@#CM", "@#SC", "@#SP", "@#TA")

_SUBSTITUTED_ORIG = (
    re.compile(r"@#EQ"),
    re.compile(r"@#CM"),
    re.compile(r"@#SC"),
    re.compile(r"@#SP"),
    re.compile(r"@#TA"),
)
_SUBSTITUTION_ORIG = ("=", ",", ";", " ", "\t")


def translate_illegal(infoString):
    # OPT: Could perhaps use function for replacement instead of looping
    for regexp, substitution in zip(_SUBSTITUTED, _SUBSTITUTION):
        infoString = regexp.sub(substitution, infoString)
    return infoString


def translate_to_original(translatedString):
    for regexp, substitution in zip(_SUBSTITUTED_ORIG, _SUBSTITUTION_ORIG):
        translatedString = regexp.sub(substitution, translatedString)
    return translatedString


# --------------------------------


def split_vcf_into_multiple_by_ids(vcfFile, lastID="KA1", writeHeader=True):
    """Splits a VCF file based on ID into multiple files named as ID.vcf

    Puts the ID as sample name in the VCF header.
    Note that vcftools vcf-merge can merge files by position, creating multi-sample VCFs.
    """
    if isinstance(vcfFile, str):
        vcfFile = open(vcfFile)
    g = open("{}.vcf".format(lastID), "w")
    for line in vcfFile:
        if line.strip().isspace() or line.startswith("#"):
            continue
        parts = line.strip().split("\t")
        sampleID = parts[2]
        if sampleID != lastID:
            g.close()
            g = open("{}.vcf".format(parts[2]), "w")
            if writeHeader:
                g.write("##fileformat=VCFv4.1\n")
                g.write(
                    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{}\n".format(sampleID)
                )
        g.write(line)
        lastID = sampleID
    vcfFile.close()
    g.close()
