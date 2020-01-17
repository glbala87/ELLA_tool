---
title: Gene panels
---

# Gene panels

[[toc]]

Analyses in ELLA are restricted to genes included in predefined gene panels. In addition to which genes to investigate, the gene panels defines default transcripts, phenotype relationships and inheritance mode for each gene. 

## Genes
Genes to include, using [HGNC ID](https://www.genenames.org/about/).

## Transcripts 

Transcript(s) to use as default for each gene (multiple choices possible). Default transcripts affect how variants and annotation are displayed in the user interface, especially regarding HGVS cDNA/protein naming and [VEP consequence](http://www.ensembl.org/info/genome/variation/predicted_data.html#consequences) calculation. 

Note that ELLA also uses consequences calculated for alternative transcripts in the same gene, but these will be less visible unless they are "worse" (i.e. more likely to cause damage) than in the default transcript(s). 

## Phenotypes

Phenotypes linked to each gene, based on [OMIM](http://omim.org/). Tied to: 

## Inheritance

The inheritance mode to use for each gene, based on [OMIM](http://omim.org/). These are important for certain rules in [variant filtering](/concepts/filtering.html#filters) and suggesting [ACMG criteria](/concepts/acmg-rule-engine.html). 

The modes are grouped like this for the purpose of both filtering and ACMG suggestions:

- Autosomal dominant (AD)
- Other (autosomal recessive (AR), x-linked dominant/recessive (XD/XR), combinations)

Note that although mixed modes are possible (e.g. AD/AR), using pure AD whenever reasonable generally means more accurate results in filtering and ACMG suggestions. 
