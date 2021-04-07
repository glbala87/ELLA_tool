---
title: Latest releases
---

# Release notes: Latest releases

|Major versions|Minor versions|
|:--|:--|
[v1.13](#version-1-13)|
[v1.12](#version-1-12)|[v1.12.1](#version-1-12-1), [v1.12.2](#version-1-12-2), [v1.12.3](#version-1-12-3)

See [older releases](/releasenotes/olderreleases.md) for earlier versions.

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

### Breaking changes

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
- Tweaked front-end error reporting to reduce number of "An error occured ..." messages displayed to users.
<!-- MR !497 -->
- Replaced custom vcf parser with [cyvcf2](https://github.com/brentp/cyvcf2).
<!-- MR !511 -->
- Added blacklist option in the [analysis watcher](/technical/import.html#analysis-watcher-for-automated-import), allowing exclusion of specific analyses during automated import.
<!-- 
Probably no further release notes necessary, but adding here for reference: 
MR !505 Create upload release artifacts
MR !496 Split references from annotation in database
MR !498 Fixes for running local demo instances 
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


