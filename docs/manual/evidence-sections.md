---
title: Evidence sections
---

# Evidence sections: Evaluate annotation and studies

[[toc]]

## Analysis specific (ANALYSES only)

This section is specific to the current sample (analysis) and displays indicators of the quality of the variant calling (HTS data, ANALYSES mode only).

::: warning Note
This is the only section on this page that is specific to the sample (analysis), all other sections are tied to the variant interpretation, which is independent of samples. This also means that any comments you add here will be visible in this analysis only.
:::

### Quality information 

Quality information is tied to a particular sample, and is therefore only available in ANALYSES mode. In addition, only information from HTS data is provided. The following quality parameters are shown (from the VCF file; see <https://software.broadinstitute.org/gatk/documentation/article.php?id=1268> for details):

  - Filter: PASS if all filters have passed, otherwise list filters that failed

  - Quality: Variant calling quality
    
      - Phred-scaled probability that a REF/ALT polymorphism exists at this site given sequencing data
      - 10 = 1 in 10 chance of error, 100 = 1 in 10^10 chance of error

  - GQ: Genotype quality
    
      - Derived from PL below
      - 99 is the maximum

  - PL: Phred-scaled likelihood for genotype
    
      - Most likely genotype is always 0, if other values are \>=99, GQ above is 99
      - The three numbers represent REF/REF, REF/ALT and ALT/ALT, respectively

  - Depth: Number of reads covering the site

  - Ratio: Number of reads covering each allele, with ratio for variant allele/total

Variants with quality issues are marked with NEEDS VERIFICATION in red in the QUALITY card. Note that indels are always marked, irrespective of other parameters.

### Mark as verified/technical/not relevant

In the header of the ANALYSIS SPECIFIC section, you can mark variants as verified, technical or 'not relevant':

<div style="text-indent: 4%;"><img src="./img/verified_btn.png"></div>

  - VERIFIED means the variant has been verified by an independent method (e.g. Sanger) in this sample. This adds a green “V” tag in the “Q” column of the [side bar](/manual/side-bar.html).

  - TECHNICAL means the variant is a false variant call in this sample (analysis). This adds a red “T” tag in the “Q” column of the [side bar](/manual/side-bar.html) and moves the variant to a separate section TECHNICAL VARIANTS in the side bar.
  
  - NOT RELEVANT means the variant should be disregarded in this analysis. 
  
::: tip Note 
Variants marked as TECHNICAL or NOT RELEVANT can, depending on the your configuration, be left without a selected class upon finalisation of the analysis.
:::

## Frequency

This section displays population frequencies reported in external or internal datasets (if any). Note that variants with a population frequency exceeding the threshold for ACMG criterion BA1 have already been [filtered out](/manual/top-bar.html#excluded-variants).

### Included Datasets

  - gnomAD exomes and genomes: <http://gnomad.broadinstitute.org/>
  - ExAC: <http://exac.broadinstitute.org/> (NB: partly deprecated, most samples are included in gnomAD)
  - InDB: OUSWES, in-house frequency database for sequenced exomes.
  - dbSNP: <https://www.ncbi.nlm.nih.gov/projects/SNP/>  
	::: warning Note
	Any SNP that has positional overlap with the current variant is reported, and therefore may not contain the exact same variant/allele. If you use this data, you should check the dbSNP entry to verify that it has the same variant as in your sample.
	:::

Variants with quality issues reported in gnomAD display a warning in the gnomAD cards.

### Mark as Class 2 variant

You may quickly set a class 2 for the current variant by pressing the MARK CLASS 2 button in the header of this section:

<div style="text-indent: 4%;"><img src="./img/class2_btn.png"></div>

This will move the variant to CLASSIFIED VARIANTS in the side bar.

## External

This section shows annotation from external databases, currently including HGMD Pro and ClinVar.

### Included databases

  - HGMD Pro: <https://portal.biobase-international.com/hgmd/pro/>
  - ClinVar: <http://www.ncbi.nlm.nih.gov/clinvar/>

### Add data from other external databases

If you want to add results from other databases (various LSDBs, depending on the gene), press the ADD EXTERNAL DB button:

<div style="text-indent: 4%;"><img src="./img/add_external_btn.png"></div>

In the popup, select from the dropdown for each database you want to add from. For pre-specified databases, there will be a <span class="underline">Visit database</span> link to the right, which will take you to the corresponding database and gene. Choices for all databases except OTHER (which is free text) are:

  - Unambigous classification: 
	  - **Pathogenic**: Class 5 or similar
	  - **Likely pathogenic**: Class 4 or similar
	  - **Uncertain significance**: Class 3 or similar
	  - **Likely benign**: Class 2 or similar
	  - **Benign**: Class 1 or similar

  - Other: 
	  - **Conflicting**: Conflicting classes reported
	  - **Indirectly relevant**: Variant is not the same, but has indirect relevance
	  - **Nothing found**: No entries found in database
	  - **Other**: None of the choices above are applicable

Remember to SAVE (top right) once you are done.

## Prediction

This section displays various predicted effects of the variant.

### Included predictions

#### VEP consequence

[Variant Effect Predictor (VEP)](http://www.ensembl.org/info/genome/variation/predicted_data.html#consequences) provides basic information about the location and expected effect of a variant within a transcript and protein. VEP uses [Sequence Ontology terms](http://www.sequenceontology.org/).

By default, only effects in the default transcript(s) specified in the gene panel are shown. However, if there are worse consequences in other, alternative RefSeq (NM\_) transcripts, this will also be displayed together with a warning. To view consequences in all alternative RefSeq transcripts, click the given consequence(s).

### Add predictions

Add other types of predictions by clicking the ADD PREDICTION button:

<div style="text-indent: 4%;"><img src="./img/add_prediction_btn.png"></div>

The choices you make here are meant as “keywords”, and any details important for evaluating the choices made should always be added to the PREDICTION-COMMENTS field. Choices made here result in suggestions for relevant ACMG codes in the CLASSIFICATION section, but you still need to approve/add individual codes before final classification.

::: warning NOTE
The DOMAIN and REPEAT options are also available in the reference evaluation module (see below), and should be added there if you have a specific reference to attach this information to.
:::

The manual options are:

  - ORTHOLOG CONSERVATION
    
      - Conserved: the amino acid is highly conserved in orthologues
      - Non-conserved: the amino acid is not conserved in orthologues

  - PARALOG CONSERVATION
    
      - Conserved: the amino acid is highly conserved in paralogs
      - Non-conserved: the amino acid is not conserved in paralogs

  - DNA CONSERVATION
    
      - Conserved: the DNA nucleotide is highly conserved
      - Non-conserved: the DNA nucleotide is not conserved

  - DOMAIN
    
      - Critical functional domain: the variant is located in a critical functional domain
      - Critical functional amino acid: the function of the reference amino acid is known to be critical

  - REPEAT
    
      - Repeat region: the variant is located in a repeat region.
      - Non-repeat region: the variant is located in a non-repeat region

  - SPLICE SITE EFFECT
    
      - Splice site lost: the variant is predicted to cause the loss of an authentic splice site
      - De novo splice site: the variant is predicted to cause the creation of a novel splice site
      - No splice site effect: the variant is predicted to have no effect on splicing

Remember to SAVE (bottom right) once you are done.

## References

This section contains literature references describing the variants in the sample. The references have been automatically retrieved from HGMD Pro.

### Reference evaluation

The reference section has separate cards for new (PENDING), already EVALUATED and EXCLUDED references (note that empty cards are not shown).

Each of the references in the PENDING card can either be evaluated or ignored by pressing one of the corresponding buttons:

<div style="text-indent: 4%;"><img src="./img/evaluate_ignore_btn.png"></div>

The EVALUATE button will bring up the evaluation form. Help text for the different options provided here is available by holding the mouse cursor over the header/question. The options are meant as a guide, and you should always make a separate comment summarising any points from the reference that will be important for the classification of the variant. Note also that there is a separate REFERENCE-COMMENTS field on the front page, for summarising findings from multiple references.

Already evaluated references with RELEVANCE: YES/INDIRECTLY are placed in the EVALUATED card. Here, any unpublished (e.g. in-house) studies are always shown at the top. To review/change the previous evaluation, click RE-EVALUATE or IGNORE. Note that the latter option excludes the reference and should only be used in special circumstances.

The IGNORE button marks the reference as ignored and moves it to an EXCLUDED card that by default is hidden from the list. The same thing happens to references that are marked as ignored or not relevant (RELEVANCE: NO/IGNORE) in the evaluation form. To show hidden references, press the SHOW EXCLUDED button:

<div style="text-indent: 4%;"><img src="./img/show_excluded_btn.png"></div>

Excluded references may be added back by clicking the RE-EVALUATE button and changing to RELEVANCE: YES or INDIRECTLY.

### Add studies

If you have found other studies/references that aren’t already in the list, you can add them by clicking the ADD STUDIES button:

<div style="text-indent: 4%;"><img src="./img/add_studies_btn.png"></div>

The resulting dialogue lets you add studies in one of three ways:

  - SEARCH: Search the internal database for studies that have already been added but not connected to the current variant, then click ADD next to a positive search result.
  
  - PUBMED: Add reference data as provided in PubMed XML format - see instructions in the pop-up.
  
  - MANUAL: Add studies manually, either PUBLISHED or UNPUBLISHED (e.g., in-house) studies. Fields marked with a \* are mandatory.
