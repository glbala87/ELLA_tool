---
title: Top bar
---

# Top bar: Info and actions

[[toc]]

The top bar contains information about the current user, selected variant, as well as action buttons. The figure below shows the top bar in the ANALYSIS workflow, where there are three sections, for global and variant-specific information/actions, respectively:

<div style="text-indent: 4%;"><img src="./img/top_bar.png"></div>

The view in VARIANTS workflow is almost the same but contains no sample-specific information.

## Action buttons

### Global

Button  | Explanation | More information
:---  | :---  | :---
`GENE PANEL INFO` | Show information about the gene panel used in the current analysis. | [Gene panel info](/manual/info-page.html#gene-panel-info)
`COPY ALL TO ALAMUT`  | Copy all variants in analysis to clipboard in Alamut format. | [Links](/manual/classification-page.html#links-to-the-web-and-alamut)
`WORK LOG`  | System and user messages related to current analysis/interpretation. |  [Work log](/manual/worklog.md)
`START` / <br>`FINISH`+`SAVE` | Start, save changes and finish an analysis or interpretation. | [Start](/manual/classification-page.html#start-an-analysis-or-interpretation); [Save/Finish](/manual/classification-page.html#save-and-finish)


### Variant

Button  | Explanation | More information
:---  | :---  | :---
`COPY VARIANT TO ALAMUT`  | Copy currently selected variant to clipboard in Alamut format.  | [Links](/manual/classification-page.html#links-to-the-web-and-alamut)
`ADD ACMG`  | Add an ACMG criterion manually. | [Classification section](/manual/classification-section.html#add-acmg-criterion-manually)
`ADD ATTACHMENT`  | Add an attachment (picture or file) to a comment field. | [Comments and attachments](/manual/classification-page.html#comments-and-attachments)
`COLLAPSE ALL`  | Collapse all evidence sections. | [Use collapsing for overview ...](/manual/classification-page.html#use-collapsing-for-overview-and-marking-sections-as-done)


## Analysis history for previously finished samples

When a previously analysed sample is opened in ANALYSES mode, a drop-down menu in the top bar (right) provides an option for viewing the exact state at an earlier, finished step (review or finalize):

<div style="text-indent: 4%;"><img src="./img/analyses_history_select.png"></div>

This shows all variant interpretations as well as the annotation available at the selected time. Note that if you click `REOPEN` (button the right of the drop-down) for a finalized sample, the annotation and variant interpretations shown are always equal to the most current state.

::: warning NOTE
This history view is specific to analyses performed in [ANALYSES mode](/concepts/workflows.html#sample-centered-workflow-analyses) and does not include history of independent variant interpretations performed in [VARIANTS mode](/concepts/workflows.html#variant-centered-workflow-variants) (if any). See also [variant-specific classification histories](/manual/classification-section.html#variants-with-a-previous-interpretation).
:::

## Warnings

### Collision warnings

If you open a variant or analysis that overlaps with (unfiltered) variants currently being evaluated by another user, ELLA displays a red warning banner at the top (this can be collapsed by clicking on the banner). For the warning below, the analysis contains one variant currently being worked on in an ANALYSIS workflow by the user Henrik Ibsen:

<div style="text-indent: 4%;"><img src="./img/collision_warning.png"></div>

This means that variant interpretation changes made by the other user may overwrite your own changes, or vice versa. You should therefore wait until the other user is finished, or clarify with the other user if you should do the interpretation for these variants. 

Note that, if you open a variant that is under the OTHERS’ VARIANTS header in a VARIANTS workflow, you can choose to reassign the variant or analysis to yourself by using the `REASSIGN TO ME` button top right:

<div style="text-indent: 4%;"><img src="./img/reassign_btn.png"></div>

Similarly, if another user imports new results to an analysis you have already opened, a warning will be displayed upon next save or if you try to finish the analysis: `ADDITIONAL DATA HAVE BEEN ADDED TO THIS ANALYSIS. PLEASE REFRESH`. In this case, simply refresh your browser (Ctrl + R), which will add the new variants to the analysis.

### Variant warnings

Another type of warning is triggered when certain conditions are met for a variant. This is displayed both as a [tag in the side bar](/manual/side-bar.html#variant-tags) and as a warning in the top banner when you select the variant. The list of warnings currently includes:

  - Worse consequences in other transcripts
  - Other variants are within 3 bp of the variant in the analysis

Example warning:

<div style="text-indent: 4%;"><img src="./img/variant_warning.png"></div>

### Errors

If ELLA is not able to perform an action, an error message will be flashed at the bottom of the page. Note down the error message and contact a system administrator if this happens. 

## User profile and history

By clicking your user name (top right corner), you will get an overview of your profile and interpretation history. Clicking on a variant/sample under YOUR ACTIVITY will open that variant/sample.

This page also includes a `LOGOUT` button (top right).

::: warning NOTE
Checking the user history will exit any currently active interpretation, so remember to save your work first!
:::