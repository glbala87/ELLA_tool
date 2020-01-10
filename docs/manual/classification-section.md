---
title: Classification section
---

# Classification section: Summarize and set ACMG criteria and classification

[[toc]]

This section is where you review the information from other sections, summarize your findings, add ACMG criteria and set a classification. In other words, for variants with no pre-existing interpretation, you should review the other sections first. 

## Summarizing comments: Evaluation and Report

Unlike other sections, this section contains two main comment fields:

  - EVALUATION: For summarizing the evaluation of the consequence of the variant. This should be detailed enough for making an informed decision, but leaving the specifics to comments in respective sections.
  - REPORT: Comments relevant for clinical evaluation (automatically included in the final patient report). 
  ::: warning NOTE
  Comments made here will be visible for all patients where this variant shows up, and should be generalized, not patient-specific, as far as possible. For patient specific comments, use [fields on the REPORT page](/manual/report-page.html#comment-fields-indication-and-report).  
  ::: 

## Variants with a previous interpretation

ELLA matches the variants in each new sample with existing variant interpretations in the database. If a match is found, the last classification along with user, date and any changes to the report is displayed in a separate card:

<div style="text-indent: 4%;"><img src="./img/existing_classification.png"></div>

Clicking the `HISTORY` button shows a more detailed history including ACMG criteria and comments, for every previously finalized round of interpretation, ordered by date.

### Interpretations that are still valid

Previously finalized variant interpretations have a limited time period where they are still considered valid, and can be re-used without further evaluation. These variants are grouped with CLASSIFIED VARIANTS in the [side bar](/manual/side-bar.html#side-bar-sections). 

Variant interpretations that are still valid are shown with a green background and automatically accepted as if you had performed a regular interpretation, but without resetting the validity period. 

It is still possible to do a re-evaluation of these variants by clicking the `RE-EVALUATE` button in the section banner (only available if the analysis/interpretation has been started). To undo any new interpretation (and avoid resetting the validity period), click the `UNDO RE-EVALUATION` button:

<div style="text-indent: 4%;"><img src="./img/reevaluate_btn.png"></div>

::: warning NOTE
Pushing the `RE-EVALUATION` button also resets the classification. To be able to finalize the variant, you must first reselect a class in the dropdown. 

Changing the REPORT field only does not reset the validity period for a variant.
:::

### Interpretations that are outdated

If a previous variant interpretation has exceeded the validity time period, it will be considered outdated and due for re-evaluation. 

Outdated variants are grouped with UNCLASSIFIED VARIANTS in the [side bar](/manual/side-bar.html#side-bar-sections). Unlike new variants (no previous interpretation in the database), however, you _must_ press the `RE-EVALUATE` button for outdated variants before you are able to update the interpretation. This is to avoid resetting the validity period if no actual re-evaluation has been performed.

## Review and add ACMG criteria 

The ACMG criteria in ELLA are based on the official [ACMG 2015 guidelines](https://www.ncbi.nlm.nih.gov/pubmed/25741868).

Before setting a variant classification, you should add relevant ACMG criteria to the variant interpretation. There are two main ways of doing this, from [suggested criteria](/manual/classification-section.html#suggested-acmg-criteria-and-requirements-req) or [manually](/manual/classification-section.html#add-acmg-criteria-manually), explained below. A third option is available for a few selected criteria in the [Quick classification mode](/manual/quick-classification.md).

Added criteria are shown in a list above the SUGGESTED card.

::: warning NOTE
Each ACMG criterion can be added only once for a particular variant, irrespective of chosen strength.
:::

### Suggested ACMG criteria and requirements (REQ)

ELLA automatically [suggests relevant ACMG criteria](/concepts/acmg-rule-engine.html) based on a mapping of the variant annotation, as well as any information you have added manually, to these criteria. Suggested criteria are shown in the SUGGESTED card:

<div style="text-indent: 4%;"><img src="./img/ACMG_suggested.png"></div>

The specific requirements for each criterion are available by clicking on the label. The resulting pop-up also contains (where applicable):

  - Notes: From official [ACMG 2015 guidelines](https://www.ncbi.nlm.nih.gov/pubmed/25741868)
  - Local adjustments: Notes specific to your own setup
  - Match: What triggered the suggestion (this is still in development and may be somewhat cryptic or not available)

To add a suggested criterion to the interpretation, click `ADD` to the right. 

::: warning NOTE
The suggestions may be somewhat imprecise and **you should always check that all requirements are satisfied** before clicking `ADD`.
:::

#### REQ: requirements for ACMG criteria

Where possible, some of the ACMG criteria have been split into separate ["requirements" (REQs)](/concepts/acmg-rule-engine.html#req-requirements) in ELLA. Each of these REQs is a necessary component for the ACMG criteria they belongs to. ELLA displays these REQs for information, which can be used as hints for additional criteria that may be relevant for the current variant. 

REQs that have a match in the current variant are shown when you click the `SHOW REQ` button:

<div style="text-indent: 4%;"><img src="./img/ACMG_REQ.png"></div>

### Add ACMG criteria manually

To add an ACMG criterion that is not already suggested by ELLA, press the `ADD ACMG` button in the top banner:

<div style="text-indent: 4%;"><img src="./img/add_ACMG_btn.png"></div>

This brings up a side bar where you may modify strength, comment and add any ACMG criterion:

<div style="text-indent: 4%;"><img src="./img/add_ACMG.png"></div>

#### Other (non-ACMG) criteria

In addition to the official ACMG criteria, you can also add the generic `OTHER` criterion. This can be used for criteria that are not described in the ACMG guidelines, but that are nonetheless important for the clinical classification. This includes, e.g., certain gene-specific criteria from the ENIGMA and InSiGHT guidelines. Note that these will not be used in calculation of the [suggested classification](#set-variant-class).

## Modifying the strength of added criteria

To change the strength of a particular, added criterion, click either the `+` or `-` sign, for stronger or weaker evidence, respectively:

<div style="text-indent: 4%;"><img src="./img/ACMG_change_strength.png"></div>

### Unweighted ACMG criterion 

If you click the `-` sign all the way, the criterion will be marked as `NOT WEIGHTED`. This can be used when the evaluation of a criterion needs to be documented, but where the evidence does not support using it in the final classification. Any criteria added this way will not be used in the [suggested classification](#set-variant-class). 

## Set variant class

Based on the particular ACMG criteria you have added, ELLA [suggests a classification](/concepts/acmg-rule-engine.html#generating-suggestions), shown over the list of included ACMG criteria:

<div style="text-indent: 4%;"><img src="./img/suggested_class.png"></div>

As with suggested criteria, you are free to ignore the suggestion, and you must always actively set a classification yourself before it takes effect. Once you have made a decision, select the corresponding class in the pull-down menu in the section bar:

<div style="text-indent: 4%;"><img src="./img/select_class.png"></div>

If in ANALYSES mode, this moves the variant to CLASSIFIED VARIANTS in the variant side bar.

Note that suggestions are only made for CLASS 1-5. 

## Finalize variant

Once you have set a classification, you have the option to finalize the variant: 

<div style="text-indent: 4%;"><img src="./img/finalize_variant.png"></div>

Once a variant is finalized, the interpretation is made available to other users and will not generate [collision warnings](/manual/warnings.html#collision-warnings) if there are overlapping analyses. 

::: warning NOTES
Finalization of all new/updated classified variants is a requirement to finalize the analysis. This includes any classifications that were set using [QUICK mode](/manual/quick-classification.md).

Finalizing a variant should only be used when you consider the evaluation to be complete, i.e. no further review is needed. Depending on configuration, this option may therefore not be available except in review workflow steps. 
:::

