#!/usr/bin/env python
"""
Module for creating VCF file(s) from a CSV file with
at least 3 columns giving the sample name, the HGVS-described variant, and a homozygosity flag.
Additional columns found will be added to the VCF INFO field;
except for (sampleAndVariant-specific) columns whose names are specified explicitly.
These will be added to the genotype field.

The script outputs one VCF line per line in input, with sampleName in VCF ID field.
If desired, you can split the output into separate files by sampleName using
vcfhelper.split_vcf_into_multiple_by_IDs() and merge these files into
one multi-sample VCF file with vcftools vcf-merge.

Note that ref alleles in VCF output is by default taken from the genomic reference sequence.
If there is an error such that the given ref (from the HGVS expression)
is not identical to the genomic ref, a warning is given.
One can alternatively also choose to use the given ref from the HGVS expression.


Example input (first line header starting with #):
#sample  hgvs  homozygous
s1  NC_000001.10:g.156104598delG  FALSE
s1  NC_000011.9:g.47365199G>T     TRUE
s2  NM_123:c.123+4A>T             FALSE


Notes regarding conversion of positions:
1Genomic:    123  456789
Insertions:     XX   HGVS: 3_4   VCF (firstbase): 3   0Genomic: 3-1

1Genomic:    12345678
Deletions :    XX    HGVS: 3_4   VCF (firstbase): 2   0Genomic: 2-1
"""

import re
import csv
import sys
import argparse
import warnings

from pyfaidx import Fasta

from vcfutil import vcfhelper
from coordinates import hgvs
from coordinates.posconverter import posconverter


NC_CHROM = {"1" : "NC_000001", "2" : "NC_000002", "3" : "NC_000003",
            "4" : "NC_000004", "5" : "NC_000005", "6" : "NC_000006",
            "7" : "NC_000007", "8" : "NC_000008", "9" : "NC_000009",
            "10" : "NC_000010", "11" : "NC_000011", "12" : "NC_000012",
            "13" : "NC_000013", "14" : "NC_000014", "15" : "NC_000015",
            "16" : "NC_000016", "17" : "NC_000017", "18" : "NC_000018",
            "19" : "NC_000019", "20" : "NC_000020", "21" : "NC_000021",
            "22" : "NC_000022", "X" : "NC_000023", "Y" : "NC_000024"}
NC_CHROM = dict((v, k) for k, v in NC_CHROM.iteritems())

GT_COLS = [] # Colums that are genotype/sample specific. Updated from args in main().


def from_SNP(vcfAlleleCreator, variant, chromosome, hgvsStart, vcfID):
    ref, foo, alt = variant.partition('>')
    gPos = hgvsStart - 1
    return vcfAlleleCreator.snp(chromosome, gPos, ref, alt, vcfID)


def from_indel(vcfAlleleCreator, variant, chromosome, hgvsStart, hgvsEnd, vcfID):
    # Works with both 'delinsAA' and 'delGGGinsAA'
    inserted = variant.split("ins")[1] # Inserted sequence (not the deleted)
    if variant.index("ins") > variant.index("del") + 3: #delGGGinsAA
        deleted = variant.split("del")[1].split("ins")[0]
    else:
        deleted = ''
    gPosStart = hgvsStart - 1
    if hgvsEnd is not None:
        gPosEnd = hgvsEnd - 1 + 1 # +1 for half-open interval, whereas HGVS is last deleted
    else:
        # Indel not given with end coordinates means deletion of 1 nucleotide.
        gPosEnd = gPosStart + 1
    return vcfAlleleCreator.indel(chromosome, gPosStart, gPosEnd, inserted, deleted, vcfID)


def from_insertion(vcfAlleleCreator, variant, chromosome, hgvsStart, vcfID):
    inserted = variant.split("ins")[1]
    gPos = hgvsStart - 1
    return vcfAlleleCreator.insertion(chromosome, gPos, inserted, vcfID)


def from_deletion(vcfAlleleCreator, variant, chromosome, hgvsStart, hgvsEnd, vcfID):
    deleted = variant.split("del")[1] # Can optionally be empty!
    gPosStart = hgvsStart - 1
    gPosEnd = hgvsEnd -1 + 1 if hgvsEnd is not None else gPosStart + 1 # half-open interval
    return vcfAlleleCreator.deletion(chromosome, gPosStart, gPosEnd, deleted, vcfID)


def from_duplication(vcfAlleleCreator, variant, chromosome, hgvsStart, hgvsEnd, vcfID):
    duplicated = variant.split("dup")[1] # Can optionally be empty!
    gPosStart = hgvsStart - 1
    gPosEnd = hgvsEnd - 1 + 1 if hgvsEnd is not None else gPosStart + 1
    return vcfAlleleCreator.duplication(chromosome, gPosStart, gPosEnd, duplicated, vcfID)


def extract_genomic_data_from_hgvs(hgvsField, pcs):
    """Parse HGVS expression and return genomic coordinates, also for c. pos HGVS"""
    # This is a point of change and will likely be handled by the pypi hgvs module in the future.
    h = hgvs.read(hgvsField)
    # Strip any version numbers in 'ids' (e.g. NM_123.X and NC_00001.X):
    h = h._replace(id = h.id.split('.')[0]) # namedtuple requires ._replace
    assert h.id.startswith("NM_") or h.id.startswith("NC_")
    if h.reftype == 'c':
        h = hgvs.read(pcs.hgvs_c2g(hgvsField, returnHGVS=True))
    chromosome = NC_CHROM[h.id]
    hgvsStart = int(h.start) # 1-based HGVS position
    hgvsEnd = int(h.end) if h.end is not None else None
    return chromosome, hgvsStart, hgvsEnd, h.var


def make_info_field(columnNames, columns):
    """Returns an INFO field string with keys from columnNames and values from columns.

    Skips empty columns and those where the column name is in GT_COLS.
    """
    infoField = ['='.join((cn, vcfhelper.translate_illegal(c))) for cn, c in zip(columnNames, columns) if not cn in GT_COLS and not c.strip()=='']
    return ';'.join(infoField) or '.'

def make_genotype_field(columnNames, columns):
    """Returns a genotype field"""
    # Genotype field must be equal for all records, so most use missing value if column empty.
    return ':'.join((vcfhelper.translate_illegal(c) or '.' for cn, c in zip(columnNames, columns) if cn in GT_COLS))



def make_vcf(csvReader, vcfAlleleCreator, pcs):
    """Make a VCF file from a tab-separated file of sampleName, HGVS expression,
    homozygous, and other fields."""
    columnNames = csvReader.next()
    columnNames[0] = columnNames[0].strip('#')
    assert columnNames[0].lower() == "sample" and columnNames[1].lower() == "hgvs" and columnNames[2].lower() == "homozygous"

    # Write VCF meta-information lines
    sys.stdout.write("##fileformat=VCFv4.1\n")
    for cn in columnNames[3:]:
        if not cn in GT_COLS:
            sys.stdout.write('##INFO=<ID={0},Number=.,Type=String,Description="{0}">\n'.format(cn))
    sys.stdout.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
    for cn in columnNames[3:]:
        if cn in GT_COLS:
            sys.stdout.write('##FORMAT=<ID={0},Number=.,Type=String,Description="{0}">\n'.format(cn))
    sys.stdout.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tMetasample\n")

    for columns in csvReader:
        sampleID, hgvsField, homozygous = columns[0:3]
        try:
            chromosome, hgvsStart, hgvsEnd, hgvsVar = extract_genomic_data_from_hgvs(hgvsField, pcs)
        except posconverter.PosconverterOutsideTranscriptError as err:
            sys.stderr.write("Error: Skipping {} as it is outside transcript!\n".format(hgvsField))
            continue
        except hgvs.HGVSNomenclatureError as err:
            sys.stderr.write("Error: Skipping {} as it does not conform to HGVS standard!\n".format(hgvsField))
            continue
        assert homozygous.upper() in ("TRUE", "SANN", '1', 'T', "FALSE", "USANN", '0', 'F')
        genotype = "1/1" if homozygous.upper() in ("TRUE", "SANN", '1', 'T') else "0/1"

        if re.search(r">", hgvsVar):
            chromosome, vcfPosition, vcfID, ref, alt = from_SNP(vcfAlleleCreator, hgvsVar, chromosome, hgvsStart, sampleID)
        elif re.search(r"delins|del\S+ins", hgvsVar):
            chromosome, vcfPosition, vcfID, ref, alt = from_indel(vcfAlleleCreator, hgvsVar, chromosome, hgvsStart, hgvsEnd, sampleID)
        elif re.search(r"ins", hgvsVar):
            chromosome, vcfPosition, vcfID, ref, alt = from_insertion(vcfAlleleCreator, hgvsVar, chromosome, hgvsStart, sampleID)
        elif re.search(r"del", hgvsVar):
            chromosome, vcfPosition, vcfID, ref, alt = from_deletion(vcfAlleleCreator, hgvsVar, chromosome, hgvsStart, hgvsEnd, sampleID)
        elif re.search(r"dup", hgvsVar):
            chromosome, vcfPosition, vcfID, ref, alt = from_duplication(vcfAlleleCreator, hgvsVar, chromosome, hgvsStart, hgvsEnd, sampleID)
        else:
            raise ValueError("Cannot recognize variant {}".format(hgvsVar))

        # Make INFO, FORMAT and Genotype fields
        infoField = make_info_field(columnNames[3:], columns[3:])
        extraGT = make_genotype_field(columnNames[3:], columns[3:])
        genotypeField = genotype + ':' + extraGT if len(extraGT) > 0 else genotype
        formatField = ':'.join((cn for cn in columnNames[3:] if cn in GT_COLS))
        formatField = "GT:" + formatField if formatField != '' else "GT"

        # CHROM	POS	ID REF ALT QUAL FILTER	INFO FORMAT	GENOTYPE
        sys.stdout.write('\t'.join((chromosome, str(vcfPosition), vcfID, ref, alt,
                                ".", ".", infoField, formatField, genotypeField)) + '\n')




def main(argv=None):
    global GT_COLS
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="""Convert CSV file with HGVS-described sample/variant data to a VCF file.
    Outputs to stdout and stderr.""")
    parser.add_argument("--input", action="store", dest="inputFileName", required=True,
                        help="Path to file with positions to convert.")
    parser.add_argument("--fasta", action="store", dest="fasta",
                        default="/Users/tonyha/Dropbox/data/hg19/chromosomes/hg19.fa",
                        help="Path to (pygr) FASTA file")
    parser.add_argument("--refgene", action="store", dest="refgeneFilePath", required=True,
                        help="Path to UCSC refGene file")
    parser.add_argument("--genotypecols", action="store", dest="genotypeColumns",
                        required=False, nargs='*', default = [], metavar="COLNAME",
                        help="The names of the columns that are sample/genotype specific.")
    parser.add_argument("--hgvsref", action="store_true", dest="hgvsRef", required=False, default=False,
                        help="Use ref allele from HGVS expression, not from FASTA file.")
    args = parser.parse_args(argv)
    GT_COLS.extend(args.genotypeColumns)

    vcfAlleleCreator = vcfhelper.VCFAlleleCreator(Fasta(filepath=args.fasta),
                                                  useGenomeRef=not args.hgvsRef)
    pcs = posconverter.PosConverterService.make_pos_converters(args.refgeneFilePath) # Will give warnings
    with open(args.inputFileName, 'rb') as inputFile:
        csvDialect = csv.Sniffer().sniff(inputFile.read(1024), delimiters="\t,")
        inputFile.seek(0)
        csvReader = csv.reader(inputFile, csvDialect)
        make_vcf(csvReader, vcfAlleleCreator, pcs)
    vcfAlleleCreator.write_records_failing_reference_match(fileHandle=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
