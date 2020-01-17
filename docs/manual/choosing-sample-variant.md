---
title: Choosing a sample or variant
---

# Choosing a sample or variant 

[[toc]]

The first page you see after logging in is the OVERVIEW page. You can always navigate to this page using the link in the top right corner:

<div style="text-indent: 4%;"><img src="./img/overview_btn.png"></div>
<br>

This page also links to the current documentation (you can also reach these by going to [allel.es/docs](http://allel.es/docs)): 

<div style="text-indent: 4%;"><img src="./img/documentation_btn.png"></div>


## Select analysis or variant from the worklist

Depending on how ELLA is configured, the vertical buttons in the left margin of the OVERVIEW page may include buttons for either `ANALYSES` or `VARIANTS`, or both: 

<div style="text-indent: 4%;"><img src="./img/overview_sidebar_analyses.png"></div>

For an in-depth explanation of the difference between an ANALYSES workflow and a VARIANTS workflow, see [Workflows](/manual/workflows.md). Most importantly: 

- ANALYSES are tied to a specific laboratory sample and gene panel.
- VARIANTS are stand-alone variant interpretations, and therefore contains no sample-specific information (e.g. genotype and variant calling quality).

### ANALYSES worklist

In the ANALYSES view, you may choose from one or more of the following: 

Option  | Explanation
:--- | :---
`NOT READY` | Imported analyses where a variant needs validation or regions are insufficiently covered. The variants in these samples should not be interpreted until validation/sequencing of missing regions has been performed.
`YOUR ANALYSES` | Any unfinished analyses that you have started and saved, but not completed.
`INTERPRETATION`  | Analyses that have not yet been opened by any user.
`REVIEW`  | Analyses that have been interpreted by another user and marked for review.
`MEDICAL REVIEW`  | Analyses marked for review by a lab physician.
`OTHERS’ ANALYSES`  | Analyses currently being worked on by other users.
`FINALIZED` | Analyses that have been analysed and marked as Finalized.

#### Optional/alternative ANALYSES worklist sections

Depending on configuration, some of the worklist sections may have been swapped by other alternatives. 

Optional replacement for `INTERPRETATION`:

Option  | Explanation
:--- | :---
`INTERPRETATION - ALL VARIANTS CLASSIFIED`  | Analyses ready for interpretation, but where all variants already have a valid classification.
`INTERPRETATION - MISSING CLASSIFICATIONS` | Analyses ready for interpretation and where at least one variant is missing a valid classification (all analyses not in above section)

Optional replacement for `REVIEW`:

Option  | Explanation
:--- | :---
`REVIEW - ALL VARIANTS CLASSIFIED` | Analyses ready for review, but where all variants already have a valid classification.
`REVIEW - MISSING CLASSIFICATIONS`  | Analyses ready for review and where at least one variant is missing a valid classification (all analyses not in above section).

### VARIANTS worklist

In the VARIANTS view, you may choose from one or more of the following:

Option  | Explanation
:--- | :---
`YOUR VARIANTS` | Any unfinished variant interpretations that you have started and saved from a previous session.
`PENDING CLASSIFICATION` | Variants that have not yet been opened/interpreted.
`PENDING REVIEW` | Variants that have been interpreted at least once and that have been marked for review. Users and dates for previous interpretations are given to the far right.
`OTHERS’ VARIANTS` | Variants currently being worked on by other users.
`FINALIZED` | Variants that have been interpreted and marked as Finalized.

## History, comments and tags

For both ANALYSES and VARIANTS view, each analysis/variant is marked with the date when the sample/variant was loaded into ELLA (sorted with oldest on top) and, if present, user and date of previous interpretation rounds along with any [overview comments](/manual/top-bar.html#work-log) provided by the previous analyst. 

In the ANALYSES view, samples are marked with the source of the data (HTS or SANGER, or both), as well as a [WARNING](/manual/info-page.html#pipeline-warnings) from the variant calling pipeline if relevant:

<div style="text-indent: 4%;"><img src="./img/overview_tags.png"></div>

## Search (and edit) variants and samples

To search for a particular variant or analysis (past or present), use the search section at the top of the OVERVIEW page:

<div style="text-indent: 4%;"><img src="./img/search.png"></div>

Possible searches include HGVS cDNA or protein variant name with or without reference ID, genomic position/range and analysis ID. Examples:

  - `c.198A>G`
  - `NP_075561.3:p.Gly1248Asp`
  - `13:32890607`
  - `13:32890500-32890800`
  - `NA12878`

Search results may be narrowed further by selecting gene or user, or by ignoring excluded variants (see figure above).

Clicking on a variant search result will open the variant in a VARIANTS workflow. Note that to (re-)interpret the variant, ELLA has to tie the interpretation to a gene panel. Check that the correct gene panel is chosen in the dropdown next to the `START` button, *before* you start:

<div style="text-indent: 4%;"><img src="./img/choose_genepanel.png"></div>

