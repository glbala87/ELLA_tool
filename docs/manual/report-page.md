---
title: Report page
---

# Report page: Generate a clinical report

Navigate to the report page using the corrseponding button in the top bar:

<div style="text-indent: 4%;"><img src="./img/nav_report_btn.png"></div>
<br>

## Comment fields: Indication and report

You may add two types of comments on this page, meant for internal purposes (i.e., they are not included in the export): 

- INDICATION COMMENT: For comments about/description of the patient's indication. The contents of this comment field is also shown at the [top of the side bar](/manual/side-bar.html#buttons-and-comment-fields) on the CLASSIFICATION page (changes in either place is mirrored in both).
::: warning NOTE
Comments about how the indication or phenotype has influenced the current analysis specifically should be made in the [ANALYSIS SPECIFIC section](/manual/evidence-sections.html#analysis-specific-analyses-only) on the CLASSIFICATION page, not here.
::: 
- REPORT COMMENT: For comments relevant for the sample as a whole (including all variants) and how the report was written.
::: warning NOTE
This is different from comments made in the [REPORT field](/manual/classification-section.html#evaluation-and-report-summarising-comments) on the CLASSIFICATION page, which are connected to a specific variant. 
::: 

## Adding or removing variants from the report export

The report page also lets you export variants in a CLINICAL REPORT using using standard naming conventions together with the classification, as well as any comments you added to the REPORT field in the CLASSIFICATION section.

Variants classified as Class (3,) 4 or 5 (depending on configuration) are automatically added to the report and marked with a `-` sign in the side bar. Not included variants are marked with a `+` sign. If you want to remove or add additional variants, simply click on the `-` or `+` sign, respectively, for the variant.

<div style="text-indent: 4%;"><img src="./img/report_sidebar.png"></div>

Once you are satisfied, copy the text generated in the REPORT field to LIMS software. 