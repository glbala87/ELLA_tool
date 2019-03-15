---
title: Data import
---

# Data import

[[toc]]

HTS data produced in-house is imported automatically into *ella*. However, data for samples or individual variants can also be added manually. 

## Import data

Start by clicking on the `IMPORT` button in the top banner of the OVERVIEW page:

<div style="text-indent: 4%;"><img src="./img/import_btn.png"></div>

The numbers after the green and red dot in the button displays the number of import jobs that are currently being processed and that have failed processing, respectively.

Clicking the button brings up a pop-up window. Paste text containing the variants to be imported into the RAW DATA field, in one of the supported formats (see below), then click `+ PARSE DATA`:

<div style="text-indent: 4%;"><img src="./img/parse_data_btn.png"></div>

[Supported import formats](#supported-import-formats) and [options](#options) are explained below. When the import is ready, click the 
`+ IMPORT` button:

<div style="text-indent: 4%;"><img src="./img/plus_import_btn.png"></div>

Submitted jobs are displayed at the top of the import pop-up:

<div style="text-indent: 4%;"><img src="./img/status_submitted.png"></div>

The status will change from SUBMITTED to DONE once the import has successfully completed. If something went wrong, you can try the retry button to the right, or check for errors in the imported text (click the STATUS text) and repeat the import process.

## Batch import

Results from multiple analyses may be imported at the same time by inserting a line before the results of each analysis in the pasted text, starting with "-" and followed by the analysis name. 

The contents of each original file is given its own import number and treated separately.

::: warning NOTE
Variants for the same sample must all be given in the same format. If you wish to import variants with multiple formats (e.g. HGVS cDNA and genomic) to the same sample, copy the sample header (starting with “-“) to a new line and move any variants with a deviating format under it.
:::

## Supported import formats

Supported formats are explained in the list to the left of the RAW DATA field (click on each list item in *ella* to get more examples):

  - Full HGVS cDNA name (e.g. `NM_000059.3:c.9732_9733insA`)
  - Genomic position (e.g `13-32893435-G-T`)
  - VCF file
  - SeqPilot text export flie

::: danger
The import module is **not able to convert HGVS cDNA names for variants outside the transcribed region** of a given transcript (e.g. promoter variants), as this is considered invalid in terms of the HGVS format by the conversion service. 

To successfully import these variants, they must first be converted to **genome-based names**. 

Example: `NM_000321.2:c.-193T>G (het)` → `13-48877856-T-G (het)`  

Be careful when you do the conversion: If the transcript is reverse to the genome, you must use alleles that are complementary to the alleles given in the transcript!
:::

## Options

You may change parameters by clicking the `EDIT IMPORT` button (if a warning: “Selection is incomplete” is displayed, the dialogue is automatically opened):

<div style="text-indent: 4%;"><img src="./img/edit_import_btn.png"></div>

Depending on your data, the following options are available:

  - TYPE: `ANALYSIS`. Imports variants tied to an analysis ID and a gene panel.
    
      - MODE: `CREATE`. Add a new sample (no match to existing analysis IDs).
      - MODE: `APPEND`. Append to an existing analysis ID with genotypes. \*
      - ANALYSIS NAME. Filled in automatically if provided in the pasted data, otherwise you must fill in (for CREATE) or choose an existing analysis.

  - TYPE: `VARIANTS`. Imports variants independently of analyses (samples). This is automatically chosen when one or more variants lack genotypes, and a warning message is displayed.

  - GENEPANEL. Must be specified for all imports, to enable proper filtering. *ella* automatically chooses either the default panel (which you can change), or for MODE: `APPEND`, the panel matching the existing analysis ID (which you shouldn’t change unless you want to change to MODE: `CREATE`).

  - TECHNOLOGY: `SANGER`/`HTS`. Default is SANGER, but you can change to HTS if importing from an external HTS service.

::: warning NOTE
If you import variants (`APPEND`) to an analysis that is already opened by another user, *ella* displays a warning: "Analysis is ongoing. (\[user/date])!". 

The other user will then get a notification to refresh his/her browser upon next save, which will add any new variants to the ongoing analysis.
:::

You may also exclude individual variants from the import by deselecting them in the VARIANTS TO INCLUDE list to the right.
