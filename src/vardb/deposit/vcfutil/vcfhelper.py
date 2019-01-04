#!/usr/bin/env python
"""
Module for VCF helper functions.
"""
import re


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
