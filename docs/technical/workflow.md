# Workflow

::: warning NOTE
This documentation is a work in progress and is not currently up to date.

Please contact developers for more details.
:::

[[toc]]

ELLA uses the concept **workflow** to guide the users through the interpretation process.

At the end of the workflow the interpretation if **finalized**, making the interpetation work available in other workflows. Until then the classifications (and other info) made of the variants/alleles in that workflow  is available for users.

A workflow is a multi-step process where a user interpret the variant(s) using the information presented by the tool or that is found outside and then entered into the tool. After the interpretation the user marks the workflow/interpretation to be ready for review. Another user continues the interpretation and can either mark it for review again or finalize it, the latter meaning the variant(s) get an official assessment/classification. Each 'review' or 'finalize' step is called a **round**. When a workflow is finished all the rounds are available later if one needs to audit the work done in each round.

The workflow for single variants and analyses are slightly different:
- In an **allele workflow** a single variant is interpreted and eventually given a classification (1-5).
- In an **analysis workflow** multiple variants are interpreted, and they all need a classification before the analysis can be finalized.

Variants that are initially filtered out can be manually included by the user. These variants must also be classified.

## A typical analysis interpretation
A user selects an analysis and goes through each variant giving them a classification using the information made available in the tool. The classification is set given supporting info such as:
- Relevant references
- Proteting predictions
- ACMG codes calculated by a rules engine

The user will add info such as:
- Free text
- Attachments (e.g. images)

The analysis is then set to review and another user will either continue the interpretation (like adding info, changing classification) or finalizing the analysis.

So the interpretation goes through (possibly multiple)  review rounds before being finalized (see figure):

  [Initial round] ---review--> [second round] --review--> [third round] ..... [...] --finalize--> Done


## Interpretation rounds and history
When later opening an analysis, all the rounds of the analysis are available read-only. Any round can be selected  and the UI will reflect the context at the point of interpreation.

The interpretation of single a variant will also build an increasing list of rounds.


## Reopening an analysis
A finalized variant/analysis can be reopened for further interpretation, thus increasing the list of rounds. It must be finalized before any changes are available in other workflows.


