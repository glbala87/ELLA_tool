---
title: User information and warnings
---

# User information and warnings

[[toc]]

## Collision warnings: Same variant - Multiple users

If you open a variant or analysis that overlaps with (unfiltered) variants currently opened by other users, ELLA displays a red warning banner at the bottom. For the warning below, the analysis contains one variant currently being worked on in VARIANTS workflows by the user Bjørnstjerne Bjørnson:

<div style="text-indent: 4%;"><img src="./img/collision_warning.png"></div>

This means that variant interpretation changes made by the other user may overwrite your own changes, or vice versa. You should therefore wait until the other user is finished, or clarify with the other user if you should do the interpretation for these variants. Note that, if you open a variant that is under the OTHERS’ VARIANTS header in a VARIANTS workflow, you can choose to reassign the variant or analysis to yourself by using the `REASSIGN TO ME` button top right:

<div style="text-indent: 4%;"><img src="./img/reassign_btn.png"></div>

Similarly, if another user imports new results to an analysis you have already opened, a warning will be displayed upon next save or if you try to finish the analysis: ADDITIONAL DATA HAVE BEEN ADDED TO THIS ANALYSIS. PLEASE REFRESH. In this case, simply refresh your browser (Ctrl + R), which will add the new variants to the analysis.

## Date, user and tags

For both ANALYSES and VARIANTS view, each analysis/variant is marked with the date when the sample/variant was loaded into ELLA (sorted with oldest on top) and, if present, user and date of previous interpretation rounds along with any [overview comments](/manual/top-bar.html#work-log) provided by the previous analyst. In addition, in the ANALYSES view, samples are marked with the source of the data (HTS or SANGER, or both), as well as a [WARNING](/manual/info-page.html#pipeline-warnings) if relevant:

<div style="text-indent: 4%;"><img src="./img/overview_tags.png"></div>

## User profile and history

By clicking your user name, you will get an overview of your profile and interpretation history. Clicking on a variant/sample under YOUR ACTIVITY will open that variant/sample.

This page also includes a `LOGOUT` button (top right), but the use of this should usually not be necessary in TSD.

::: warning NOTE
Checking the user history will exit any currently active interpretation, so remember to save your work first!
:::