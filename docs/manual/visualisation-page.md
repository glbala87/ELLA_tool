---
title: Visualisation
---

# VISUALISATION (ANALYSES only)

Navigate to the VISUALISATION page by using the button in the left corner of the top bar:

<div style="text-indent: 4%;"><img src="./img/nav_visualisation_btn.png"></div>

This page features an integrated version of [IGV](https://igv.org/doc/doc.html):

<div style="text-indent: 4%;"><img src="./img/visualisation.png"></div>

With IGV, you can visualise all variants in an analysis, along with customisable tracks at three different levels: 

- Global (all users):  
	- RefGene: Transcripts.
	- Genepanel: Regions covered by the current gene panel.
	- Classifications: All classifications present in the database.
	- Variants: All variants in the same sample (analysis) _after_ filtering.
	
- User group: 
	- Tracks specific to your user group in *ella*. Typically includes data from external sources and references.
	
- Analysis (none, some or all will be available):
	- BAM files: Raw alignments (HTS data only), split by family members if relevant
	- VCF: All variants called in the VCF file (HTS data only, within gene panel, no filtering)
	- CNV: Called CNVs (HTS data only)

