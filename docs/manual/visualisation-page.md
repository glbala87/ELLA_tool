---
title: Visualisation page
---

# Visualisation page

[[toc]]

Navigate to the VISUALISATION page (available in ANALYSIS mode only) by using the button in the left corner of the top bar:

<div style="text-indent: 4%;"><img src="./img/nav_visualisation_btn.png"></div>
<br>

This page features an [integrated version](https://igv.org/doc/doc.html) of [Integrative Genomics Viewer (IGV)](http://software.broadinstitute.org/software/igv/):

<div style="text-indent: 4%;"><img src="./img/visualisation.png"></div>

With IGV, you can visualise all variants in an analysis, along with customisable tracks at three different levels: global, user group or analysis.

## Global tracks

Tracks available to all users. Currently includes: 

- `REFGENE`: Transcripts from RefGene.
- `GENEPANEL`: Regions covered by the current gene panel.
- `VARIANTS`: All variants in the same sample (analysis) _after_ filtering.
- `CLASSIFICATIONS`: All existing classifications present in the database.
	
## Your tracks (user group)

Tracks specific to your user group in *ella*. Typically includes data from external sources and references.
	
## Analysis tracks

Tracks specific to the analysis (depending on configuration). This may include:

- `BAM` files: Raw alignments (HTS data only), split by family members if relevant
- `VCF`: All variants called in the VCF file (HTS data only, within gene panel, no filtering)
- `CNV`: Called CNVs (HTS data only)

