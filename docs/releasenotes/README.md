---
title: Latest releases
---

# Release notes: Latest releases

|Major versions|Minor versions|
|:--|:--|
[v1.13](#version-1-13)|
[v1.12](#version-1-12)|[v1.12.1](#version-1-12-1), [v1.12.2](#version-1-12-2)

See [older releases](/releasenotes/olderreleases.md) for earlier versions.

## Version 1.13

Release date: [TBD]

### Highlights

[...]

### All changes

<!-- 
Probably no further release notes necessary, but adding here for reference: 
MR !494 Updated JSON schema for filterconfigs
MR !496 Split references from annotation in database
MR !497 Replaced vcfiterator with cyvcf2
MR !498 Fixes for running local demo instances 
-->
- Several fixes and improvements to development environment and code base. 

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


