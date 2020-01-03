---
title: Latest release
---

# Release notes: Latest releases

See [older releases](/releasenotes/olderreleases.md) for earlier versions.

## Version 1.9

Release date: 22.01.2020

### Highlights

This version adds changes to better support larger number of users and user groups using the same variant interpretation database. 

#### Finalize variants in analyses

The most important change is the addition of a "finalize variant" function in analyses. This allows variant interpretations to be released for overlapping analyses (where the same variant is present in more than one non-finalized analysis workflow) as quickly as possible. This also means that workflow collision warnings are given per variant instead of per analysis, reducing the number of displayed warnings.

With this change, each variant with a new/updated classification in an analysis should now be finalized by pressing a `FINALIZE` button in the CLASSIFICATION section before the analysis can be finalized.

[TODO: screenshot + manual]

#### User group warnings

Finalizing variants means each variant interpretation will be tagged with the main responsible user and user group. This also allows showing a warning if the previous (finalized) variant interpretation was performed by a user from another user group than your own. 

[TODO: screenshot + manual]

### All changes

<!-- MR !341 -->
- [Finalize variant in analysis](#finalize-variants-in-analyses)
- `MARK CLASS 2` button has been removed from the FREQUENCY section (CLASSIFICATION page).
<!-- MR !346 -->
- [Display warning when variant was finalized by different group](#user-group-warnings)
<!-- MR !347 -->
- Entries listed in the STUDIES & REFERENCES section are now shown with annotation source and better separation. 
<!-- MR !348 -->
- All action buttons are now disabled until all data has been loaded when opening an analysis.
<!-- MR !349 -->
- Some configuration files that was hard coded have now been replaced by a dynamic configuration.
<!-- MR !350 -->
- Mouse popovers and tooltips now use tippy.js, with possibility for copying text to clipboard by mouse-click (any text marked with a clipboard symbol).


