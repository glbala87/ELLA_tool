---
title: Latest release
---

# Release notes: Latest releases

See [older releases](/releasenotes/olderreleases.md) for earlier versions.

## Version 1.9

Release date: 29.01.2020

### Highlights

This version adds changes to better support larger number of users and user groups using the same variant interpretation database. 

#### Finalize variants in analyses

The most important change in this version is the addition of a "finalize variant" function in analyses. This allows variant interpretations to be released for overlapping analyses (where the same variant is present in more than one non-finalized analysis workflow) as quickly as possible. This also means that workflow collision warnings are given per variant instead of per analysis, reducing the number of displayed warnings.

With this change, each variant with a new/updated classification in an analysis needs to be finalized by pressing the new `FINALIZE` button in the CLASSIFICATION section before the analysis (sample) itself can be finalized:

<div style="text-indent: 4%;">
    <img src="./img/1-9-finalize-variant.png">
    <br>
    <div style="font-size: 80%;">
        <strong>Figure: </strong>New button to finalize variant in analysis.
    </div>
    <br>
</div>

Note that this also needs to be performed for any classification done in [QUICK mode](/manual/quick-classification.md), and that interpretations done in VARIANTS mode (stand-alone variants e.g. from search) still need to be finalized as before via the `FINISH` button in the top bar before the variant is considered truly finalized. 

#### User group warnings

Finalizing variants means each variant interpretation will be tagged with the main responsible user and user group. This also allows showing a warning if the previous (finalized) variant interpretation was performed by a user from another user group than your own: 

<div style="text-indent: 4%;">
    <img src="./img/1-9-user-group-warning.png">
    <br>
    <div style="font-size: 80%;">
        <strong>Figure: </strong>New user group warning.
    </div>
    <br>
</div>

#### Copy text by mouse-click

You can now more easily copy text from many pop-overs by clicking on the text. Look for the clipboard symbol, e.g. in the HGVS cDNA variant name in the top bar: 

<div style="text-indent: 4%;">
    <img src="./img/1-9-popup.png">
    <br>
    <div style="font-size: 80%;">
        <strong>Figure: </strong>New option to copy text directly by mouse-click in popups.
    </div>
    <br>
</div>

### All changes

<!-- MR !341 -->
- [Finalize variant in analysis](#finalize-variants-in-analyses)
<!-- MR !346 -->
- [Display warning when variant was finalized by different group](#user-group-warnings)
<!-- MR !350 -->
- Mouse popovers and tooltips now use [tippy.js](https://atomiks.github.io/tippyjs/), with possibility for [copying text by mouse-click](#copy-text-by-mouse-click) (any text marked with a clipboard symbol).
<!-- MR !358 -->
- Optional sections on the ANALYSES OVERVIEW page have been simplified, see [ANALYSIS worklist](/manual/choosing-sample-variant.html#optional-analyses-view). 
<!-- MR !356 -->
- Added support for importing references with .RIS format from the [new PubMed webpage](https://pubmed.ncbi.nlm.nih.gov/).
<!-- MR !347 -->
- Entries listed in the STUDIES & REFERENCES section are now shown with annotation source and better separation. 
<!-- MR !341-->
- `MARK CLASS 2` button has been removed from the FREQUENCY section (CLASSIFICATION page).
<!-- MR !355 -->
- ACMG criteria now have short descriptions available everywhere.
<!-- MR !348 -->
- All action buttons are now disabled until all data has been loaded when opening an analysis.
<!-- MR !349 -->
- Most configuration settings that were previously hard coded in `/src/api/config/config.py` have now been replaced by a dynamic configuration, set by the environment variable `ELLA_CONFIG`. See `/example_config.yml` for examples.
<!-- MR !354 -->
- Fixed issue during import when re-importing previously deleted analyses.
<!-- MR !351 -->
- Changes to the documentation, including moving the "Concepts" section to the [User manual](/manual/concepts.md). 

