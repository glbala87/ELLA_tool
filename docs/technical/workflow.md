# Workflow

::: warning NOTE
This documentation is a work in progress and is not currently up to date.

Please contact developers for more details.
:::

[[toc]]

ELLA uses the concept **workflow** to guide the users through the interpretation process. This section details the technical aspects of this concept. See [Concepts](/docs/concepts/workflows.md) for descriptions aimed at end users.

## Steps and rounds

A workflow is a process where an analysis or variant goes through multiple **rounds** of interpretation/review, performed by different users. The possible steps are: 

`NOT READY` - `INTERPRETATION` - `REVIEW` - `MEDICAL REVIEW` - `FINALIZE`

New analysis/variants that have not yet been opened by any user are automatically placed in `INTERPRETATION`, all other steps must be chosen by a user.

Each finished workflow step is called a **round**. At the end of a round, users may choose a workflow step that requires review by others, or **finalize** the analysis/variant. Only after this final step has been taken, the results are made "official" and available to other users and workflows.

## Single variants and analyses

The workflow for single variants and analyses are slightly different:
- In an **allele workflow** a single variant is interpreted and eventually given a classification (1-5).
- In an **analysis workflow** multiple variants are interpreted, and they all need a classification before the analysis can be finalized.

Variants that initially have been filtered out need no further action by the user. However, any filtered variants that are manually included by the user must also be subsequently classified.

## A typical analysis interpretation
A user selects an analysis and goes through each variant giving them a classification using the information made available in the tool. The classification is set given supporting info such as:

- Relevant references
- Bioinformatic predictions
- ACMG criteria calculated by a rules engine

The user will add info such as:

- Free text
- Pre-defined choices in forms (e.g. from reference evaluation)
- Attachments (e.g. images)

The analysis is then set to review and another user will either continue the interpretation (like adding info, changing classification) or finalizing the analysis.

So the interpretation goes through (possibly multiple) review rounds before being finalized:

  [Initial round] ---review--> [second round] --review--> [third round] ..... [...] --finalize--> Done


## Interpretation rounds and history

A record is kept of all rounds, in case an audit is needed. 

When opening a previously finalized analysis, all the previous rounds of the analysis are available read-only. When selecting a particular round, the UI will reflect the informational context at the point of interpretation.

The interpretation of single a variant will also build an incremental list of rounds.


## Reopening an analysis
A finalized variant/analysis can be reopened for further interpretation, thus increasing the list of rounds. It must be finalized before any changes are available in other workflows.


