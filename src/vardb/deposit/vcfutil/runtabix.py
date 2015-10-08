#!/usr/bin/env python
"""
Script for running bgzip and tabix on all supplied VCF file paths.
Sorts the input files prior to bgzip and tabix.
"""
import os
import sys

##from pybedtools import BedTool
scriptDirectory = os.path.dirname(os.path.realpath(__file__))

for filePath in sys.argv[1:]:
    # if filePath.lower().endswith(".bed"):
    #     b = BedTool(filePath)
    #     sortedBed = b.sort()
    #     sortedBed.tabix(in_place=False, is_sorted=True) # temporary files only...
    # elif filePath.lower().endswith(".vcf"):
    os.system("cat %s | python %s/sort_vcf.py | bgzip -c > %s.gz" % (filePath, scriptDirectory, filePath))
    os.system("tabix -p vcf %s.gz" % filePath)
sys.exit(0)
