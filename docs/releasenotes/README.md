---
title: Latest releases
---

# Release notes: Latest releases

|Major versions|Minor versions|
|:--|:--|
[v1.15](#version-1-15)|
[v1.14](#version-1-14)|[v1.14.1](#version-1-14-1), [v1.14.2](#version-1-14-2)
[v1.14](#version-1-14)|[v1.14.1](#version-1-14-1)
[v1.13](#version-1-13)|[v1.13.1](#version-1-13-1), [v1.13.2](#version-1-13-2)
[v1.12](#version-1-12)|[v1.12.1](#version-1-12-1), [v1.12.2](#version-1-12-2), [v1.12.3](#version-1-12-3)

See [older releases](/releasenotes/olderreleases.md) for earlier versions.

## Version 1.14.2

Release date: 31.08.2021

### Highlights

This release adds a few bugfixes.

### All changes

<!-- MR !567 -->
- Fixed a bug causing inability to import VCFs with no variants.
<!-- MR !569 -->
- Fixed missing tooltip for reference title.
<!-- MR !570 -->
- Fixed a bug causing incorrect sorting of variants in the Region section.
<!-- MR !573 -->
- Fixed a bug causing display of info from currently selected variant instead of filtered variant in Filtered variants modal.
<!-- MR !576 -->
- Fixed a bug causing inability to manually add External or Prediction info in certain instances.
<!-- MR !578 -->
- Fixed a bug causing missing hemizygous counts for legacy/default frequency annotation.
## Version 1.15

Release date: TBD

### Highlights

[TODO]

It is now possible to quickly add a signature and date (`[username, yyyy-mm-dd]`) to any comment field, using either the keyboard shortcut `Alt + S` or a button on the formatting toolbar: 

<div class="figure_text">
    <img src="./img/1-15-quick-add-signature.png"><br>
    <p><strong>Figure: </strong>Quick add signature to any comment field.</p>
</div> 

### All changes

<!-- MR !554 -->
- Added `SHOW ANALYSES` button to VARIANTS workflow.
<!-- MR !565 -->
- Added button and keyboard shortcut for quick insertion of signature and date in comment fields.
<!-- MR !568 -->
- Filtered variants are now sorted by genomic position.
<!-- MR !569 -->
- Re-added tooltip for reference title.
<!-- MR !572 -->
- Fixed a bug causing incorrect sorting of unpublished studies.

## Version 1.14.1

Release date: 08.07.2021

### Highlights

This release adds a single bugfix.

### All changes

<!-- MR !559 -->
- Fixed a bug causing front end to break in some edge cases.

## Version 1.14

Release date: 30.06.2021

### Highlights

The most significant change in this release is the addition of support for configurable annotation. In addition, several improvements have been made in the UI in preparation for CNV support. 

#### Support for configurable annotation
<!-- Relevant MRs: !405 -->
Adding new kinds of variant annotation in ELLA has up until now required changes to the source code, and has been a major limitation in the software. Starting with this release, however, new annotation can be added with a few changes to configuration. This allows much more flexibility and ease when adding new variant annotation resources. See the [technical docs](/technical/annotation.html) for more information on how to use the new configuration.

Unless new annotation is added, no changes will be visible to the end user, except a very minor change in the sorting of ClinVar entries (now sorted on date only).

#### New REGION section
<!-- Relevant MRs: !531, !544, !546, !551 -->
A new section termed REGION has been added to the CLASSIFICATION page. This shows previously classified SNVs from the internal database VarDB that are within a [preconfigured](/technical/annotation.html#region) genomic distance from the currently selected variant: 

<div class="figure_text">
    <img src="./img/1-14-nearby-variants.png"><br>
    <p><strong>Figure: </strong>New section with nearby classified variants.</p>
</div> 

#### Improvements to VISUAL
<!-- Relevant MRs: !520, !535, !541, !542, !550 -->
This version adds several improvements to how the VISUAL mode (with IGV.js) works. Most significantly, the track selection section on top of the VISUAL page is now collapsible and has the possibility for adding presets that allow quick selection/deselection of groups of tracks: 

<div class="figure_text">
    <img src="./img/1-14-track-selection.png"><br>
    <p><strong>Figure: </strong>Improved track selection with possibility for presets.</p>
</div> 

In addition, the Classification track now includes links to existing allele assessments. Click a variant in the track, then the link in the resulting popover to go to the variant: 

<div class="figure_text">
    <img src="./img/1-14-classification-link.png"><br>
    <p><strong>Figure: </strong>Classification track now has links to existing allele assessments.</p>
</div> 

Lastly, it is now possible to zoom the view quickly using the mouse wheel, and clicking a selected variant in the side bar recenters the view on the variant. 

### :small_red_triangle: Breaking changes

The following changes must be made to `ella-config.yml` to use this version: 
- Remove `frequencies.view` and instead add to the new `annotation-config.yml` (see [Annotation](/technical/annotation.md)).
- Add `similar_alleles` with subkeys `max_variants` and `max_genomic_distance` (see [Region](/technical/annotation.html#region)).

### All changes
<!-- MR !405 -->
- [Added support for configurable annotation](#support-for-configurable-annotation).
<!-- MR !531, !544, !546, !551 -->
- [Added new section REGION on CLASSIFICATION page, showing nearby SNV assessments](#new-region-section). 
<!-- MR !535 -->
- [Added support for track selection presets in VISUAL](#improvements-to-visual).
<!-- MR !520 -->
- [Made track selection section in VISUAL collapsible](#improvements-to-visual).
<!-- MR !541, !550 -->
- [Enabled links to existing classifications in VISUAL](#improvements-to-visual).
<!-- MR !542 -->
- [Added mouse wheel zoom and possibility to recenter on selected variant in VISUAL](#improvements-to-visual).
<!-- MR !525 -->
- Added support for `bigWig` and `cram` track file formats in VISUAL.
<!-- MR !545 -->
- Fixed a bug causing inability to update REPORT.
<!-- 
No further release notes necessary, but adding here for reference: 
MR !534 Add typing stubs
MR !548 Minor fixes
MR !549 Load tracks in cerebral to avoid JS promises in watch. Remove duplicate tracks with AngularJS watch.
-->
- Fixes and improvements to development environment and code base. 

## Version 1.13.2

Release date: 19.05.2021

### Highlights

This release changes thresholds for verification warnings and adds a few other tweaks and bugfixes.

### All changes

<!-- MR !526-->
- Thresholds for the ["Needs verification" warning](/manual/evidence-sections.html#warning-needs-verification) was adjusted to depth <20 (was ≤20) and allele ratio (heterozygous) ≤0.3 or ≥0.7 (was ≥0.6).
<!-- MR !527 -->
- Disallow spaces and underscores in custom gene panel names when [ordering reanalyses](/manual/data-import-reanalyses.html#use-custom-gene-panel) in the IMPORT module.
<!-- MR !523 -->
- Fixed a bug causing de novo likelihood calculation to fail in certain instances.
<!-- MR !528 -->
- Fixed a bug causing missing source information for studies and references.

## Version 1.13.1

Release date: 16.04.2021

### Highlights

This release adds a single bugfix.

### All changes

<!-- MR !517 -->
- Fixed a bug causing excessive load on backend.

## Version 1.13

Release date: 09.04.2021

### Highlights

This release brings several improvements to variant filtering rules, as well as a number of smaller fixes.

#### Improvements to variant filters in ELLA

It is now possible to configure the [Classification filter](/technical/filtering.html#classification-filter) to only consider classifications that are still valid. With this option enabled it is possible to define that e.g.  class 1 and class 2 variants should be filtered only if they have a classification that is still valid (not outdated).

#### Improvements to pre-filters

The [pre-filters](/technical/filtering.html#pre-filter-before-import) (applied before import of variants into ELLA) are now configurable and has the added option of pre-filtering variants with low mapping quality (MQ<20). This latter option is relevant e.g. for variants called with Dragen-GATK, which unlike GATK does not automatically exclude variants with a low MQ. 

#### Upgraded IGV in VISUAL

`IGV.js` on the VISUAL page has been upgraded to [v2.7.9](https://github.com/igvteam/igv.js/releases/tag/v2.7.9). For ELLA users, this fixes a few bugs, but also brings new view mode options: Click the cog wheel to the right of a track to switch between "expand" (default), "squish" or "collapse" display modes (available options depend on track type).  

### :small_red_triangle: Breaking changes

With the [improvements to pre-filters](#improvements-to-pre-filters), the configuration in `usergroups.json` must be updated. The equivalent to the previous
`"prefilter" = True` is now `"prefilter": [["hi_frequency", "no_nearby_variant", "no_classification", "not_multiallelic"]]`. See [pre-filters](/technical/filtering.html#pre-filter-before-import) for further details.

### All changes

<!-- MR !508 -->
- [Added possibility for excluding outdated classifications in the Classification filter](#improvements-to-variant-filters-in-ella).
<!-- MR !509 -->
- [Added configurability and options for pre-filters](#improvements-to-pre-filters). 
<!-- MR !506 -->
- [`IGV.js` has been upgraded to v2.7.9](#upgraded-igv-in-visual).
<!-- MR !510 -->
- Tweaked front-end error reporting to reduce number of "An error occurred ..." messages displayed to users.
<!-- MR !497 -->
- Replaced custom vcf parser with [cyvcf2](https://github.com/brentp/cyvcf2).
<!-- MR !511 -->
- Added blacklist option in the [analysis watcher](/technical/import.html#analysis-watcher-for-automated-import), allowing exclusion of specific analyses during automated import.
<!-- 
No further release notes necessary, but adding here for reference: 
MR !505 Create upload release artifacts
MR !496 Split references from annotation in database
MR !498 Fixes for running local demo instances
MR !512 Update testdata
MR !513 Update black, and run black on code base
MR !514 Fix memory issue in migration script. Reorder migrations.
-->
- Several fixes and improvements to development environment and code base. 

## Version 1.12.3

Release date: 19.02.2021

### Highlights

This release adds a few bugfixes. 

### All changes

<!-- MR !501 -->
- Fixed a bug causing loading of certain historical analyses to fail.
<!-- MR !494, MR !502  -->
- Fixes to deposit and backend.

## Version 1.12.2

Release date: 29.01.2021

### Highlights

This release adds a few bugfixes. 

### All changes

<!-- MR !491 -->
- Fixed a bug causing ELLA not to start.
<!-- MR !489 -->
- Fixed a bug causing excessive memory use in exports of variant interpretation database.
<!-- MR !490 -->
- Fixed an error in test configuration. 

## Version 1.12.1

Release date: 19.01.2021

### Highlights

This release adds a few bugfixes. 

### All changes

<!-- MR !486 -->
- Fixed a bug that caused pre- and postprocessing to fail.
- Fixed a bug that caused missing "Requested" date on imported analyses.
- Fixed a bug that caused performance problems.

## Version 1.12

Release date: 13.01.2021

### Highlights

This release includes many fixes and improvements, both to the frontend and backend/development environment. The most significant changes for users include changes to [classification](#redefined-classification-choices), [history](#improvements-to-history) and [variant warnings](#improved-warnings): 

#### Redefined classification choices

<!-- MR !477 -->
Variant classification choices have been redefined in line with [ClinVar definitions](https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/): 
- `CLASS U` was renamed to `NOT PROVIDED`, meant for recording various information (literature/research/clinical/phenotyping) without interpreting clinical significance. It is recommended to configure this class to be immediately outdated.
- The choice `RISK FACTOR` was added, meant for variants that are interpreted not to cause a disorder but to increase the risk.

The classification choices are now: 

<div class="figure_text">
    <img src="./img/1-12-select-class.png"><br>
    <p><strong>Figure: </strong>Redefined variant classification choices.</p>
</div>

#### Improvements to history

<!-- MR !465 --> 
History for changes to the variant CLASSIFICATION REPORT field was added, and the HISTORY pop-up now shows a drop-down for viewing previous versions instead of listing them: 

<div class="figure_text">
    <img src="./img/1-12-variant-history.png"><br>
    <p><strong>Figure: </strong>Modified variant history view with addition of Report history and drop-down for previous versions.</p>
</div>

<!-- MR !454 -->
In addition, when opening a previously finalized analysis, ELLA will now default to displaying the state corresponding to the latest interpretation round, i.e. showing variant interpretations, classifications and annotation exactly as they were presented at the time of the last finalization. The previous default, `CURRENT DATA` (along with any other interpretation round), is still available using the drop-down in the top bar. To prevent confusion, a warning was added when viewing historical data. 

<div class="figure_text">
    <img src="./img/1-12-analyses-history-select.png"><br>
    <p><strong>Figure: </strong>Latest interpretation round now selected by default (with warning) for historic analyses.</p>
</div>

#### Improved warnings

<!-- MR !458 --> 
To improve visibility of the different variant warnings displayed on the CLASSIFICATION page, collision warnings are now shown in a yellow banner separate from annotation and user group warnings (red), and collision warnings are no longer included in the `!` tag in the sidebar: 

<div class="figure_text">
    <img src="./img/1-12-separate-warnings.png">
    <p><strong>Figure: </strong>Collision and annotation warnings are now separate.</p>
</div>

<!-- MR !456 --> 
In addition, ELLA now displays a message at the bottom of the page if a finalized variant in an ongoing analysis has been updated and finalized by another user: 

<div class="figure_text">
    <img src="./img/1-12-toast-updated-evaluation.png">
    <p><strong>Figure: </strong>Message when evaluation has been updated by another user.</p>
</div>

Note that the message is only displayed when a user finalizes another variant or manually refreshes the view.

#### Select user group on custom imports

<!-- MR !463, MR !485-->
To better support custom gene panel imports that should be available to more than one user group, the custom gene panel import dialogue now includes an option to select user groups: 

<div class="figure_text">
    <img src="./img/1-12-select-user-group-custom-import.png">
    <p><strong>Figure: </strong>Message when evaluation has been updated by another user.</p>
</div>


### All changes

<!-- MR !477 -->
- [Redefined classification choices in line with ClinVar definitions](#redefined-classification-choices).
<!-- MR !465 -->
- [Improved design of the history modal, with addition of CLASSIFICATION REPORT history and sorted ACMG criteria](#improvements-to-history).
<!-- MR !454 -->
- [Show latest interpretation round by default for historical analyses, including warning](#improvements-to-history).
<!-- MR !458 -->
- [Variant collision warnings are now separated from annotation warnings on the CLASSIFICATION page](#improved-warnings).
<!-- MR !456 -->
- [Display message when variant in ongoing analysis has been updated by another user](#improved-warnings).
<!-- MR !463 -->
- [Added possibility to select which user groups an imported custom gene panel analysis should be available to](#select-user-group-on-custom-imports). 
<!-- MR !433 -->
- Search result limit has been increased from 10 to 100, with pagination of the search results.
<!-- MR !435 -->
- Added more external links in the gene information popup (ClinGen, PanelApp and ACMG incidental findings).
<!-- MR !475 -->
- Updated HGMD Pro links to point to new base url. 
<!-- MR !450 -->
- Added support for templates in the Gene information comment field.
<!-- MR !473 -->
- Added possibility for linking attachments on the INFO page.
<!-- MR !444 -->
- Made allele list in top bar scrollable when number of transcripts exceed 3. 
<!-- MR !453 -->
- Fixed wrong tooltip on `SUBMIT REPORT` button.
<!-- MR !455 -->
- Fixed a bug that caused variants that were removed from the REPORT to be added back again without user intent. 
<!-- MR !482 -->
- Fixed a bug that caused errors in loading of historical data.
<!-- MR !429, !443, !446, !462, !464, !468, !469, !470, !474, !478, !483, !484 -->
- Many fixes and improvements to development environment and code base.


