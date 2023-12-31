---
title: Latest releases
---

# Release notes: Latest releases

|Major versions|Minor versions|
|:--|:--|
[v1.17](#version-1-17)|[v1.17.1](#version-1-17-1), [v1.17.2](#version-1-17-2)
[v1.16](#version-1-16)|[v1.16.1](#version-1-16-1), [v1.16.2](#version-1-16-2), [v1.16.3](#version-1-16-3), [v1.16.4](#version-1-16-4), [v1.16.5](#version-1-16-5)
[v1.15](#version-1-15)|[v1.15.1](#version-1-15-1)
[v1.14](#version-1-14)|[v1.14.1](#version-1-14-1), [v1.14.2](#version-1-14-2)

See [older releases](/releasenotes/olderreleases.md) for earlier versions.

## Version 1.17.2

Release date: 09.05.2023

### Highlights

This release fixes a bug and adds support for non-coding transcripts and showing PL value in the Quality card.

### All changes

<!-- MR !740 -->
- Add support for non-coding transcripts.
<!-- MR !746 -->
- Add [Phred-scaled genotype likelihood (PL)](https://gatk.broadinstitute.org/hc/en-us/articles/360035890451-Calculation-of-PL-and-GQ-by-HaplotypeCaller-and-GenotypeGVCFs) value to the Quality card.
<!-- MR !748 -->
- Fixed a bug causing errors when inspecting the work log for a variant interpretation with no allele report.

## Version 1.17.1

Release date: 26.04.2023

### Highlights

This is a bugfix release.

### All changes

<!-- MR !742 -->
- Fixed a bug causing inability to finalize previously evaluated allele assessments.
<!-- MR !743 -->
- Fixed a bug in parser and fetcher for PubMed records.
<!-- 
No further release notes necessary, but adding here for reference: 
MR !744 Hetzner CI runner setup
MR !743 (extra) Update issue and MR templates
MR !745 Use smart_union instead of _validate_unions
-->
- Fixes and improvements to development environment and code base.

## Version 1.17

Release date: 28.03.2023

### Highlights

This version does not add significant new features, but switches to a new, improved format of gene panels. 

Note there are several [breaking changes](#small_red_triangle-breaking-changes-for-117) with this version, and admins should take care to update the necessary files.

#### Improved format of gene panels

The biggest change in this release is a new setup for gene panels. Although this doesn't add any new features in ELLA by itself, the new process for building, updating and configuring gene panels represent a significant improvement, both in terms of more easily keeping transcript and gene names updated and in terms of keeping manual configuration consistent across gene panels. 

For details, see the [Gene panel builder](https://dpipe.gitlab.io/docs/docs-pages/genepanel-builder/) documentation and the separate [GitLab](https://gitlab.com/alleles/genepanel-builder) repository. 

Note that these changes also make providing gene panel version in the usergroup config optional; see [User groups and gene panels](/technical/users.md#user-groups-and-gene-panels) and [Default import gene panel](/technical/import.md#default-import-gene-panel).

### :small_red_triangle: Breaking changes for 1.17

#### Gene panels must be updated for new imports

Changes in this version deprecates all gene panels in the old format. Historic analyses imported with old panels will still load, but no new imports will be possible until gene panels have been updated to the new version. See [above](#improved-format-of-gene-panels) for details.

#### Changes to user configuration

The configuration options `allow_notrelevant` and `allow_technical` have been removed. To update: 

1. Remove `allow_notrelevant` and `allow_technical` (if any) from your user group config (usually `fixtures/usegroups.json`).
2. Remove `allow_notrelevant` and `allow_technical` from your application config (under `user.user_config.workflows.analysis.finalize_requirements` in `ella_config.yml` or similar; see [UI options](/technical/uioptions.md#finalize-requirements)).
3. Update user groups with: 

    ``` bash
    ella-cli users add_groups <path to usergroups.json>
    ```

#### Removal of export scripts

The CLI command `ella-cli export classifications` has been removed and export scripts will no longer be maintained as part of this source code. The last version of the script is [available here](https://gitlab.com/alleles/ella/-/blob/09f29eb05732899baf83a59e7c420b9dc0cebabb/src/vardb/export/dump_classification.py).

### All changes
<!-- MR !693, !723, !726, !728, !729, !735, !736, !737 -->
- [Improved format of gene panels](#improved-format-of-gene-panels).
<!-- MR !739 -->
- Added link to [UCSC Genome Browser](https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19) in chromosome position in the [top bar](/manual/top-bar.md).
<!-- MR !733 -->
- Upgraded IGV.js in VISUAL to [v2.12.6](https://github.com/igvteam/igv.js/releases/tag/v2.12.6). This includes fixes for coloring items by pair orientation and insert size and bugs that affected rendering of bed files and amino acid translation.
<!-- MR !711 -->
- Added support for bigBed file format in VISUAL.
<!-- MR !722 -->
- Added support for VEP [v108.2](https://github.com/Ensembl/ensembl-vep/releases/tag/release%2F108.2).
<!-- MR !716 -->
- [Removed config option for disallowing Technical and Not relevant for Finalize](#changes-to-user-configuration) (set to always allowed).
<!-- MR !717 -->
- [Removed export scripts](#removal-of-export-scripts).
<!-- MR !727 -->
- Upgraded Python to [v3.11](https://www.python.org/downloads/release/python-3110/) and pydantic to [v1.10.5](https://pypi.org/project/pydantic/1.10.5/).
<!-- MR !731, !734 -->
- Updated parser and fetcher for PubMed records.
<!-- MR !732 -->
- Fixed a bug causing gene assessments not being loaded for variants where default transcript is missing from annotation.
<!-- 
No further release notes necessary, but adding here for reference: 
MR !632 Added typing to all of our API endpoints
MR !694 Create scaffolding for testdata, fix review app/local demo functionality, devcontainer optimizations
MR !697 Updated callerTypes in filterconfig schema
MR !705 Create default data directories in Dockerfile
MR !706 Add db dump/reset for tesdata
MR !707 API returns invalid IGV config
MR !709 Fixes to fetching of testdata
MR !710 Updated VEP CSQ order in typing
MR !712 Tesdata submodule
MR !713 Use submodules in review apps
MR !714 Tech doc improvements; includes Makefile and testdata changes
MR !715 Do not navigate on frontend from the backend
MR !725 Fixed types used with validation turned off
MR !738 Fallback to subquery when trying to create temp table as user without privileges
-->
- Fixes and improvements to development environment and code base.

## Version 1.16.5

Release date: 30.01.2023

### Highlights

This is a bugfix release.

### All changes

<!-- MR !721 -->
- Refined some queries that used sequential scans on large tables due to how they were formed

## Version 1.16.4

Release date: 08.03.2022

### Highlights

This is a bugfix release.

### All changes

<!-- MR !700 -->
- Upgraded IGV.js in VISUAL to [v2.11.0](https://github.com/igvteam/igv.js/releases/tag/v2.11.0), using a [temporary fork](https://github.com/ousamg/igv.js) with additional bugfixes that remove excessive error messages in VISUAL.

## Version 1.16.3

Release date: 02.03.2022

### Highlights

This is a minor release with a few bugfixes, but also includes an upgraded IGV and track descriptions available as a mouseover on the track selection buttons in VISUAL.

### All changes

<!-- MR !695 -->
- Added track description in mouseover for track selection buttons in VISUAL.
<!-- MR !698 -->
- Upgraded IGV.js in VISUAL to [v2.10.5](https://github.com/igvteam/igv.js/releases/tag/v2.10.5). This includes some bugfixes and adds the option "colour alignments by insert size and pair orientation".
<!-- MR !696 -->
- Added support for bgzipped VCF files.
<!-- MR !688 -->
- Fixed a bug causing a reset of analysis names when clicking import options for batch imports.
<!-- MR !691 -->
- Fixed a bug causing analysis to fail loading when PL values for de novo calculation is very high.
<!-- 
No further release notes necessary, but adding here for reference: 
MR !683 Fix review app / demo functionality
-->
- Fixes and improvements to development environment and code base. 

## Version 1.16.2

Release date: 21.12.2021

### Highlights

This is a bugfix release.

### All changes

<!-- MR !679-->
- Fixed a bug where genotype display is not shown in allele bar

## Version 1.16.1

Release date: 16.12.2021

### Highlights

This is a bugfix release.

### All changes

<!-- MR !676-->
- Fixed a bug causing inability to paste plain text into comment fields.
- Fixed word wrapping in comment fields.

## Version 1.16

Release date: 16.12.2021

### Highlights

#### Experimental support for CNV interpretation
<!-- MRs !575, !606, !626, !636, !638, !643, !650, !659, !673 -->

This version introduces experimental support for copy number variants (CNVs). 

When enabled, a separate CNV mode is added (switched to using a button in the top bar), where CNVs are shown in a separate variant list and allow documenting, reporting and reusing CNV interpretations, as for SNVs. The current version supports CNV deletions, duplications and tandem duplications (VCF format: `DEL`, `DUP` and `DUP:TANDEM`, respectively; for variants of type = `SVTYPE`).

<div class="figure_text">
    <img src="./img/1-16-CNV-mode.png"><br>
    <p><strong>Figure: </strong>Experimental CNV mode. Major changes from SNV mode are highlighted with red squares.</p>
</div> 

Note the limitations in this version: 
- No CNV filtering is done in ELLA, for the time being this needs to be done upstream, prior to import. 
- No particular adaptations have been made to presentation of annotation. However, any annotation from the VCF can be added in the configuration, and we recommend adding CNV-specific tracks to VISUAL to aid in interpretation.
- No CNV-specific ACMG criteria have been added.
- No manual import of CNVs is supported.

::: warning DISCLAIMER
As the CNV features are not fully validated, this functionality is currently disabled by default, and we recommend not enabling it in production. For testing, the new features can be enabled by setting the feature flag `ENABLE_CNV` to `true` in the [application configuration](/technical/application.md).
:::

#### Changes in VISUAL

Configuration of tracks in VISUAL has been further improved, allowing all types of tracks to be placed under presets. To allow better zoom/scroll control with many tracks visible, this version also adds a requirement to hold the `Shift` or `Alt` key when zooming with the mousewheel. 

### :small_red_triangle: Breaking changes for 1.16

#### Configuration of tracks in IGV
<!-- MRs !605, !651, !652, !657, !660 -->

With this version, configuration of tracks shown in IGV needs to be updated. 

Specifically, all tracks are now configured in a single config file and specified as either `DYNAMIC`, `STATIC` or `ANALYSIS` tracks. This means all tracks (including dynamic and analysis tracks) are now configurable, but also means that the individual track JSON config files used in earlier versions will no longer work. 

To configure a particular track, the file path must be matched with a regular expression (regex). Note that the JSON format requires special regex characters to be double-escaped (e.g. `.bed.gz` should be written as `\\.bed\\.gz`). See [`track_config_default.json`](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/igv-data/track_config_default.json) for examples and [IGV in VISUAL](/technical/uioptions.md) for further details.

### All changes

<!-- MR !575, !606, !626, !636, !638, !643, !650, !659, !667, !673 -->
- [Added experimental support for CNV interpretation](#experimental-support-for-cnv-interpretation).
<!-- MR !605, !651, !652, !657, !660, !668 -->
- [Improved configuration of tracks in VISUAL, including dynamic and analysis tracks](#configuration-of-tracks-in-igv). 
<!-- MR !633-->
- Mousewheel zoom in VISUAL now requires holding the `Shift` or `Alt` key.
<!-- MR !647 -->
- Added default transcript to Gene info.
<!-- MR !611 -->
- Updated order of VEP consequences to match the [Ensembl default](https://www.ensembl.org/info/genome/variation/prediction/predicted_data.html).
<!-- MR !645, !670 -->
- Fixed another bug in listing "5 most similar gene panels" for analyses with custom or older gene panels.
<!-- 
No further release notes necessary, but adding here for reference: 
MR !584 Refactor ReferenceEvalModal
MR !596 Refactor wysiwygjs
MR !600 CI is not detecting front end javascript test failures
MR !603 Provide a CORS policy for ELLA
MR !607 Improvements to region filter
MR !622 increase-api-call-timeout
MR !623 SQL performance: large list of values as subquery expression
MR !639 Upgrade to Postgres 14
MR !640 Avoid postgres error with too many locks per transaction
MR !646 Put pydantic models behind feature flag
-->
- Fixes and improvements to performance, development environment and code base. 

## Version 1.15.1

Release date: 10.11.2021

### Highlights

This is a bugfix release.

### All changes

<!-- MR !595-->
- Fixed a bug causing missing transcripts in exported classifications.
<!-- MR !619 -->
- Fixed a bug causing an error when listing "5 most similar gene panels" for analyses with custom gene panels.
<!-- MR !621-->
- Fixed a bug causing IGV search to occasionally return wrong gene when there are partial matches.
<!-- MR !624 -->
- Fixed a bug causing invisible INH values for filtered variants.
<!-- MR !625 -->
- Upgraded IGV.js in VISUAL to [v2.10.4](https://github.com/igvteam/igv.js/releases/tag/v2.10.4).
<!-- MR !629 -->
- Fixed a bug causing error on start if a Worklog comment was just added.

## Version 1.15

Release date: 13.10.2021

### Highlights

This update brings a number of enhancements to the user interface, with further improvements to VISUAL, new quick add actions, as well as several smaller improvements and bugfixes.

#### Improvements to VISUAL
<!-- MR !553, !555 -->
Selecting tracks in VISUAL has been further improved by splitting off presets in one section and the individual tracks in another, with the latter section collapsed by default. Tracks are now also organized under headers determined by preset names instead of the previous "Global", "Group" and "Analysis" headers: 

<div class="figure_text">
    <img src="./img/1-15-improved-track-selection.png"><br>
    <p><strong>Figure: </strong>Improved track selection presets, with tracks organized by preset name.</p>
</div> 

Note that tracks that have no configuration (e.g. at present, analysis raw data) are placed in the preset `OTHER` .

<!-- MR 580 -->
In addition, IGV.js was upgraded to the [most recent version](https://github.com/igvteam/igv.js/releases/tag/v2.10.0), which adds exon numbering (in feature popup) to transcript reference tracks, and improved performance. It is now also possible to open analyses with no unfiltered variants, e.g. for reviewing raw data before reporting negative test results.

See [Visual](/manual/visual.md) for further details.

#### New quick add actions
<!-- MR !565 -->
It is now possible to quickly add a signature and date (`[username, yyyy-mm-dd]`) to any comment field, using either the keyboard shortcut `Alt + S` or a button on the formatting toolbar: 

<div class="figure_text">
    <img src="./img/1-15-quick-add-signature.png"><br>
    <p><strong>Figure: </strong>Quick add signature to any comment field.</p>
</div> 

In addition, the option to quickly add a reference was added to the Report and Indications comment fields on the REPORT page, as well as in the Indications comment in the sidebar: 

<div class="figure_text">
    <img src="./img/1-15-insert-reference.png"><br>
    <p><strong>Figure: </strong>Quick add references to Indications or Report comments.</p>
</div> 

Note that for these particular comment fields, only references from variants that have been included in the REPORT are listed. 

#### Miscellaneous improvements to the user interface

Other user interface changes in this version include a better collapsed mode for sections on the CLASSIFICATION page, more concise gene and gene panel related information, improvements to layout, and various bugfixes. 

### All changes

<!-- MR !553, !555 -->
- [Improved track selection in VISUAL with grouping of tracks under preset names](#improvements-to-visual).
<!-- MR !580 -->
- Upgraded IGV.js in VISUAL from v2.7.9 to [v2.10.0](https://github.com/igvteam/igv.js/releases/tag/v2.10.0) (using [temporary fork](https://github.com/ousamg/igv.js) with bug fix). 
<!-- MR !593 -->
- In VISUAL, tracks with no configured preset are placed in an `OTHER` preset.
<!-- MR !590 -->
- Opening VISUAL is now possible also for analyses with no unfiltered variants. 
<!-- MR !565 -->
- [Added button and keyboard shortcut for quick insertion of signature and date in comment fields](#new-quick-add-actions).
<!-- MR !558 -->
- [References from included variants can now be inserted in Indication and Report comments](#new-quick-add-actions).
<!-- MR !554 -->
- Added `SHOW ANALYSES` button to VARIANTS workflow.
<!-- MR !562 -->
- Collapsing sections on the CLASSIFICATION page now also truncates comments, improving overview when comments are lengthy.
<!-- MR !564 -->
- Layout in Studies & references section is improved, removing some headers and adding an `UNPUBLISHED` tag when relevant.
<!-- MR !566 -->
- Gene `INFO` tag in top bar is now removed if gene comment is emptied.
<!-- MR !583 -->
- `GENE PANEL INFO` (button in top bar) now only lists latest version of each gene panel in "5 most similar gene panels".
<!-- MR !557-->
- User dashboard now only shows official (not custom) gene panels.
<!-- MR !585 -->
- Fixed a bug causing external links for currently selected variant instead of filtered variant in Filtered variants modal.
<!-- MR !572 -->
- Fixed a bug causing incorrect sorting of unpublished studies.
<!-- MR !581 -->
- Fixed a bug where variants in pseudo-autosomal regions threw errors on loading gnomAD hemizygous counts.
<!-- 
No further release notes necessary, but adding here for reference: 
MR !574 Makefile/local-e2e: use docker inspect to get CHROME_HOST
MR !587 Avoid log spamming from /api/v1/ui/exceptionlog/
MR !589 Make app.js updates "cache-safe"
MR !594 Fix duplicate destructured parameters
MR !599 Avoid loading all gene assessments when opening an analysis
-->
- Fixes and improvements to development environment and code base. 


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

### :small_red_triangle: Breaking changes for 1.14

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
