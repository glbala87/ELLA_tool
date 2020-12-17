---
title: Quick mode
---

# Quick classification mode

[[toc]]

Instead of performing a full classification, you may instead choose the Quick classification mode by pressing the `QUICK` button at the top of the variant list in the side bar: 

<div style="text-indent: 4%;"><img src="./img/sidebar_modes_quick.png"></div>

This feature is particularly well suited for workflows with large gene panels and many variants. The Quick classification view gives a summary of the most important information necessary for [marking variants](/manual/evidence-sections.html#mark-as-verified-technical-not-relevant) as TECHNICAL (`T`) or NOT RELEVANT (`NR`), or [classifying](/manual/classification-section.html#set-variant-class) as CLASS U (`U`) or CLASS 2 (`2`), and gives you buttons to perform those actions directly:

<div style="text-indent: 4%;"><img src="./img/quick_classification.png"></div>
<br>

The `2` button is disabled until you have added at least one benign ACMG criterion; the most commonly used criteria `BS1` and `BS2` are available as quick buttons. 

Clicking one of the `T`, `NR`, `U` or `2` buttons moves the variant down to the respective section in the sidebar. If applicable, add a comment before moving to the next variant; this will be reflected in the comment field on the CLASSIFICATION page corresponding to the column header (e.g. ANALYSIS SPECIFIC).

When you are done, and ready to do a more thourough interpretation of any remaining variants, click the `FULL` button at the top of the variant list (see also [Evidence sections](/manual/evidence-sections.html) and [Classification section](/manual/classification-section.html)).

::: warning NOTE
The numbers shown in the "Highest frequency" and "Highest count" columns depend on the configuration of the frequency filter (in particular, which populations should be included and the minimum number of observed alleles). Note that if there are multiple frequency rules defined for the same filter setup, these numbers will be calculated based upon the rules in the first filter. 
::: 
