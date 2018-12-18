#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script for sorting a VCF file.

Does *not* drop duplicate records, unlike some perl scripts :-/
Sort order currently not read from dictionary.
Does not sort stably.
"""

__author__ = "Tony Håndstad"
__credits__ = ["Tony Håndstad"]
__license__ = "GPL"
__version__ = "0.1.0"
__email__ = "tony.handstad@gmail.com"

import sys
from collections import defaultdict

# Chromosome 'contig' order:
chromosomeOrder = [str(i) for i in range(1, 23)] + ["X", "Y", "M"]

f = sys.stdin
g = sys.stdout


# {chromosome:{start:{alleles:[lines]}}}
records = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
starts = set()

# Load all lines
for line in f:
    if line.startswith("#") or line.strip() == "":
        g.write(line)
        continue
    parts = line.split("\t")
    chromosome, start, alleles = parts[0], parts[1], parts[3] + parts[4]
    assert chromosome in chromosomeOrder
    starts.add(int(start))
    records[chromosome][start][alleles].append(line)
f.close()

starts = sorted(starts)
starts = map(str, starts)
# Write all lines in order of sorted chromosome and start positions
for chromosome in chromosomeOrder:
    for start in starts:
        for alleles in records[chromosome][start]:
            for line in records[chromosome][start][alleles]:
                g.write(line)
g.close()
