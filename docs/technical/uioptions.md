# User interface

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

[[toc]]

Configuration related to the user interface. Most are defined as default settings for all users, but some settings may be overridden by [user group specific settings](#user-group-specific-settings). 


## Configure elements to show

Configure user interface elements for different pages. See `/src/api/config/config.py` for examples.


### OVERVIEW and INFO page

Define defaults view on OVERVIEW and INFO pages for all users, or per user group. 

Default settings for all users (overriddden by any group settings) are configured in: 

- File: `/src/api/config/config.py`
- Key: `config.user.user_config.overview`

User group settings are configured in: 

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `config.overview` 

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`views`  |   Tabs to show on the OVERVIEW page.   |   `variants`: Variant centered workflow; <br>`analyses-by-findings`: Sample centered workflow, grouped by the findings in the analysis;<br>`import`: Manual import
`show_variant_report`   |   Show/hide externally generated variant report on INFO page.   |   `true`/`false`

Examples also in `/src/vardb/testdata/usergroups.json`.

#### Priority

Define how to display priority values from pipeline. 

- File: `/src/api/config/config.py`
- Key: `config.analysis.priority.display`
- Value: Examples: `"1": "Normal", "2": "High", ...`


### Side bar

Define side bar content for different views in ANALYSES workflows: `full`, `quick`, `visual`, `report`, `list`. 

- Key: `config.analysis.sidebar.[view]`


Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`columns`   |   Define which columns to show.    |   [Depending on annotation.] 
`classification_options`   |   Define how to group different classifications (existing/current).     |
`comment_type`   |   Define which comment field to show. |   `None`, `analysis`, `evaluation`
`shade_multiple_in_gene`   |   Apply background shade to variants if there are more than one in the same gene.   | `true` / `false`

### IGV

Configuration of IGV in VISUAL mode. See `/src/api/config/config.py` for examples.

- File: `/src/api/config/config.py`
- Key: `config.igv`

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`reference`    |   Define what to show as reference data. |  
`valid_resource_files`    |   Files permitted accessible on `/igv/<file>` resource, relative to `$IGV_DATA` env.    |    


### Comment templates

It is possible to define templates for most comment fields in ELLA, which are available to add for the user in the text format menu. This is a [user group](/technical/users.html#user-groups) specific setting, see `/src/vardb/testdata/usergroups.json` for examples. 

Templates can be defined as pure text or with basic html formatting in: 

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `config.comment_templates` 

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`name`  |   Provide a name for the template |   [text]
`comment_fields`    |   Defines where (which comment fields) the template should be available. |   `classificationAnalysisSpecific`, <br>`classificationEvaluation`, <br>`classificationAcmg`,<br>`classificationReport`, <br>`classificationFrequency`,<br>`classificationPrediction`, <br>`classificationExternal`,<br>`classificationReferences`, <br>`reportIndications`, <br>`reportSummary`, <br>`referenceEvaluation`, <br>`workLogMessage`
`template`  |   Specifies the template    |     [pure text or basic html]


## Workflows 

### Finalize requirements

Define default requirements for finalizing a workflow for all users. Values will be used unless overridden by user group specific settings. See `/src/api/config/config.py` for examples. 

- File: `/src/api/config/config.py`
- Key: `config.user.user_config.workflows`

Separate settings are given for subkeys `allele.finalize_requirements` (VARIANTS workflows) and `analysis.finalize_requirements` (ANALYSES workflows): 

Workflow    |   Subkey	|	Explanation |   Values
:---    |   :---	|	:---    |	:---
`allele` or `analysis`  |   `workflow_status`  |   Workflow statuses allowing finalization. |   [list of statuses]
`analysis`  |   `allow_not_relevant`    |   Allow variants marked as "Not relevant" when finalizing.    |   `True` / `False`
`analysis`  |   `allow_technical`    |   Allow variants marked as "Technical" when finalizing.    |  `True` / `False`
`analysis`  |   `allow_unclassified`    |   Allow unclassified variants when finalizing. Note: This setting implies `allow_technical` and `allow_notrelevant` |   `True` / `False`

### Define references as IGNORED

Certain references retrieved from annotation sources such as ClinVar are generic and do not contain information relevant for any particular variant classification per se (an example is the [ACMG guidelines](https://www.ncbi.nlm.nih.gov/pubmed/25741868)). These references can be set to be automatically [IGNORED](/manual/evidence-sections.html#reference-evaluation) in the reference evaluation module. 

This is a [user group](/technical/users.html#user-groups) specific setting, see `/src/vardb/testdata/usergroups.json` for examples. PubMed IDs to be ignored should be added in:

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `interpretation.autoIgnoreReferencePubmedIds`
- Value: [list of PubMedIDs (integers)]

## Annotation

Define options for different annotation shown in ELLA. See `/src/api/config/config.py` for examples.

[TODO]


### ClinVar

Settings related to ClinVar annotation. 

- File: `/src/api/config/config.py`
- Key: `config.annotation.clinvar`

[TODO]

### Frequencies

Settings related to population frequency annotation. 

- File: `/src/api/config/config.py`
- Key: `config.frequencies`

#### Groups

The key `config.frequencies.groups` defines which data should be in the `external` and `internal` frequency groups. 

#### View

The key `config.frequencies.view` defines how frequency data should be shown.

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`groups`    |   Define how to group frequency annotation data.  |
`precision`  |  Float precision (for strings).  |   [integer]
`scientific_threshold`  |   Convert to scientific notation for frequencies below 10^-[x]. |   [integer]
`indications_threshold`  |   Define max threshold to show indications from internal database (depends on how the internal database is set up).  |   [integer]
`[translations]`  |   Define key to be used to link/lookup other sources of information.    |

### Custom annotation

[TODO]

- Key: `custom_annotation`

## Report: Auto-text

Configure text to include automatically for different classifications on the REPORT page. See `/src/api/config/config.py` for examples.

- File: `/src/api/config/config.py`
- Key: `config.report.classification_text`
- Value: `"[class]": "[text]"`


## Transcripts: Consequence and included

Configure use of transcripts. See `/src/api/config/config.py` for examples.

- File: `/src/api/config/config.py`
- Key: `config.transcripts`

Subkey | Explanation    |   Values
:---    |   :---    |   :---
`consequences`  |   Define order of severity for transcript consequences given by VEP (high to low). This is used for searching for "worse consequence".    |   [list of consequences ordered from more to less severe]
`inclusion_regex`   |   Types of transcripts to include, e.g. "NM_.*" for RefSeq transcripts.   |   [regex]
