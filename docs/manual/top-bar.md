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

## Variant warnings

Variants are tagged with warnings whenever there is something special that needs to be considered for the variant in question. This is displayed both as a [tag in the side bar](/manual/side-bar.html#variant-tags) and as a warning in the top banner when you select the variant. The list of warnings currently includes:

  - Worse consequences in other transcripts
  - Other variants are within 3 bp of the variant in the analysis

Variant warnings are implemented for both the variant and analysis workflows, but some warnings are only available for analyses.

Example warning:

<div style="text-indent: 4%;"><img src="./img/variant_warning.png"></div>