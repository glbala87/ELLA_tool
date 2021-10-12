---
title: Choosing a sample or variant
---

# Choosing a sample or variant 

[[toc]]

The first page you see after logging in is the OVERVIEW page. You can always navigate to this page using the link in the top right corner:

<div class="figure"><img src="./img/overview_btn.png"></div>
<br>

This page also links to the current documentation (you can also reach these by going to [allel.es/docs](http://allel.es/docs)): 

<div class="figure"><img src="./img/documentation_btn.png"></div>


## Select analysis or variant from the worklist

The vertical buttons in the left margin of the OVERVIEW page lets you choose between `ANALYSES` or `VARIANTS` workflows, with ANALYSES being the default: 

<div class="figure"><img src="./img/analyses_variants_btn.png"></div>

For an in-depth explanation of the difference between an ANALYSES workflow and a VARIANTS workflow, see [Workflows](/manual/workflows.md). Most importantly: 

- ANALYSES are tied to a specific laboratory sample and gene panel.
- VARIANTS are stand-alone variant interpretations, and therefore contains no sample-specific information (e.g. genotype and variant calling quality).

### ANALYSES worklist

In the ANALYSES view, you may choose from one or more of the following: 

Option  | Explanation
:--- | :---
NOT READY | Analyses where a variant needs validation or are insufficiently covered. The variants in these samples should not be interpreted until validation/sequencing of missing regions has been performed.
YOUR ANALYSES | Any unfinished analyses that you have started and saved, but not completed.
INTERPRETATION  | Analyses that have not yet been opened by any user.
REVIEW  | Analyses that have been interpreted by another user and marked for review.
MEDICAL REVIEW  | Analyses marked for review by a lab physician.
OTHERS’ ANALYSES  | Analyses currently being worked on by other users.
FINALIZED` | Analyses that have been analysed and marked as Finalized.

#### Optional auto-comments

Depending on [configuration](/technical/import.html#deposit), ELLA can add certain OVERVIEW comments automatically upon deposit of the analysis:

Option  | Explanation
:--- | :---
ALL CLASSIFIED  | All variants in the analysis already have a valid classification.
NO VARIANTS | The analysis contains no non-filtered variants. 

Use the [OVERVIEW filter](#filter-the-overview) to quickly locate analyses with these comments.

### VARIANTS worklist

In the VARIANTS view, only variants that have been imported manually as stand-alone variants (not tied to an analysis/sample) or that have been opened from variant search are shown. Here, you may choose from the following:

Option  | Explanation
:--- | :---
YOUR VARIANTS | Any unfinished variant interpretations that you have started and saved from a previous session.
INTERPRETATION | Variants that have not yet been opened/interpreted.
REVIEW | Variants that have been interpreted at least once and that have been marked for review. Users and dates for previous interpretations are given to the far right.
OTHERS’ VARIANTS | Variants currently being worked on by other users.
FINALIZED | Variants that have been interpreted and marked as Finalized.

## History, comments and tags

For both ANALYSES and VARIANTS view, each analysis/variant is marked with the date when the sample/variant was loaded into ELLA (sorted with oldest on top) and, if present, user and date of previous interpretation rounds along with any [overview comments](/manual/top-bar.html#work-log) provided by the previous analyst. 

In the ANALYSES view, samples are marked with the source of the data (HTS or SANGER, or both), as well as a [WARNING](/manual/info-page.html#pipeline-warnings) from the variant calling pipeline if relevant:

<div class="figure"><img src="./img/overview_tags.png"></div>

## Filter and search

### Filter the OVERVIEW

Use the search fields and buttons in the top bar to quickly filter what is shown: 

<div class="figure"><img src="./img/overview_filter.png"></div>

Filtering options include: 
- Analysis name
- Comment text (search OVERVIEW comments)
- Date requested (when the sample was requested or imported into ELLA, depending on configuration)
- Genotyping technology (HTS/Sanger)
- Priority (Normal/High/Urgent)

Hit the `RESET FILTER` button to remove all filtering. 

::: warning NOTE
Only analyses that are not finalized are included in the filter. To find older analyses, use the search function instead.
:::

### Search for variants or samples

To search for any variant or analysis (past or present), use the search section at the top of the OVERVIEW page:

<div class="figure"><img src="./img/search.png"></div>

Possible searches include HGVS cDNA or protein variant name, with or without reference ID, genomic position/range and analysis ID. Examples:

- Variant search: 
  - `c.198A>G` (note that a gene must also be selected for searches without a reference)
  - `NP_075561.3:p.Gly1248Asp`
  - `13:32890607`
  - `13:32890500-32890800`

- Analysis search:
  - `NA12878` (any part of an analysis name may be used)

Search results may be narrowed further by selecting gene and/or user (see figure above).

#### Open a search result

Clicking on a search result will open the analysis/variant. Individual variants are opened in a VARIANTS workflow; note that to (re-)interpret the variant, ELLA has to tie the interpretation to a gene panel. Check that the correct gene panel is chosen in the dropdown next to the `START` button, *before* you start:

<div class="figure"><img src="./img/choose_genepanel.png"></div>

#### Show analyses containing a variant

When searching for variants, a `SHOW ANALYSES` button next to each search result allows you to view any existing analyses containing the variant. This button is also available in the [top bar](/manual/top-bar.html#variant) in a VARIANTS workflow.

::: warning NOTE
For patient privacy reasons, investigating other analyses containing a variant should only be done when absolutely necessary (you will need to confirm this with an `I ACCEPT` button), and all actions will be logged.
::: 

Click on an analysis name in the resulting list to open it for further details. To quickly export the list of analyses shown (e.g. if performing an audit), click the `COPY TO CLIPBOARD` button.
