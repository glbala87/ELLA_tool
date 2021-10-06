# UI/UX

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

[[toc]]

Configuration related to the user interface and user experience in ELLA. Most are defined as default settings for all users, but some settings may be overridden by [user group specific settings](#user-group-specific-settings). 


## Configure elements to show

Configure user interface elements for different pages. See `/example_config.yml` for examples. 


### OVERVIEW and INFO page

Define defaults view on OVERVIEW and INFO pages for all users, or per user group. 

Default settings for all users (overridden by any group settings) are configured in: 

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `user.user_config.overview`

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

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `analysis.priority.display`
- Value: Examples: `"1": "Normal", "2": "High", ...`


### Side bar

Define side bar content for different views in ANALYSES workflows: `full`, `quick`, `visual`, `report`, `list`. 

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `analysis.sidebar.[view]`


Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`columns`   |   Define which columns to show.    |   [Depending on annotation.] 
`classification_options`   |   Define how to group different classifications (existing/current).     |
`comment_type`   |   Define which comment field to show. |   `None`, `analysis`, `evaluation`
`shade_multiple_in_gene`   |   Apply background shade to variants if there are more than one in the same gene.   | `true` / `false`

### Comment field templates

It is possible to define templates for most comment fields in ELLA, which are available to add for the user in the text format menu. This is a [user group](/technical/users.html#user-groups) specific setting, see `/src/vardb/testdata/usergroups.json` for examples. 

Templates can be defined as pure text or with basic html formatting in: 

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `config.comment_templates` 

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`name`  |   Provide a name for the template |   [text]
`comment_fields`    |   Defines where (which comment fields) the template should be available. |   `classificationAnalysisSpecific`, <br>`classificationEvaluation`, <br>`classificationAcmg`,<br>`classificationReport`, <br>`classificationFrequency`,<br>`classificationPrediction`, <br>`classificationExternal`,<br>`classificationReferences`, <br>`reportIndications`, <br>`reportSummary`, <br>`referenceEvaluation`, <br>`workLogMessage`
`template`  |   Specifies the template    |     [pure text or basic html]

### IGV in VISUAL

General configuration of IGV in VISUAL mode. See `/example_config.yml` for examples.

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `igv`

Subkey	|	Explanation
:---	|	:---    
`reference`    |   Define what to show as reference data. 
`valid_resource_files`    |   Files permitted accessible on `/igv/<file>` resource, relative to `$IGV_DATA` env.    

All tracks and types have sensible configuration values, so configuration files are not strictly necessary. The default values are merged from the default values in `src/api/v1/resources/igv.py` and the default values in [igv.js](https://github.com/igvteam/igv.js/wiki/Tracks-2.0), with the former taking precedence.

#### Track configuration

Configuration of tracks is done using a JSON file in the same folder as the track file, named as `<track file>.json`. It supports all the configuration values of [igv.js](https://github.com/igvteam/igv.js/wiki/Tracks-2.0), in addition to the following keys:

- `presets`: List of strings defining which presets it should be in.
- `show`: Boolean (`true`/`false`) indicating whether this track should be shown as default (and be part of the `Default` preset).

#### Dynamic tracks

There are three built-in, dynamic tracks available:

Track	|	Description |   Config file
:---	|	:---    |	:---
`Variants` | Shows the unfiltered variants in the analysis | `$IGV_DATA/tracks/analysis_variants.json`
`Classifications` | Shows the existing classifications from the database | `$IGV_DATA/tracks/classifications.json`
`Genepanel` | Shows the transcripts defined in the gene panel | `$IGV_DATA/tracks/genepanel.json`

#### Static tracks

Static tracks can be added as files:

Type of track	|	Explanation  |  Path
:---	|	:---    |  :---
Global tracks  |  Available to all users  |  `$IGV_DATA/tracks`
User group specific tracks  |  Available to specific user groups only.  |   `$IGV_DATA/usergroups/<group name>/tracks` 
Analysis tracks  |  Specific to the analysis, e.g. bam, vcf, bigwig files.  |  `$ANALYSES_PATH/<analysis name>/tracks`

::: tip TIP
Tracks that are found in these folders and have no associated preset (including `Default`) are available in the UI under the preset `Other`.
:::

### Auto-text in REPORT

Configure text to include automatically for different classifications on the REPORT page. See `/example_config.yml` for examples.

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `report.classification_text`
- Value: `"[class]": "[text]"`

## Workflows 

### Finalize requirements

Define default requirements for finalizing a workflow for all users. Values will be used unless overridden by user group specific settings. See `/example_config.yml` for examples. 

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `user.user_config.workflows`

Separate settings are given for subkeys `allele.finalize_requirements` (VARIANTS workflows) and `analysis.finalize_requirements` (ANALYSES workflows): 

Workflow    |   Subkey	|	Explanation |   Values
:---    |   :---	|	:---    |	:---
`allele` or `analysis`  |   `workflow_status`  |   Workflow statuses allowing finalization. |   [list of statuses]
`analysis`  |   `allow_not_relevant`    |   Allow variants marked as "Not relevant" when finalizing.    |   `True` / `False`
`analysis`  |   `allow_technical`    |   Allow variants marked as "Technical" when finalizing.    |  `True` / `False`
`analysis`  |   `allow_unclassified`    |   Allow unclassified variants when finalizing.  |   `True` / `False`

### Define references as IGNORED

Certain references retrieved from annotation sources such as ClinVar are generic and do not contain information relevant for any particular variant classification per se (an example is the [ACMG guidelines](https://pubmed.ncbi.nlm.nih.gov/25741868)). These references can be set to be automatically [IGNORED](/manual/evidence-sections.html#reference-evaluation) in the reference evaluation module. 

This is a [user group](/technical/users.html#user-groups) specific setting, see `/src/vardb/testdata/usergroups.json` for examples. PubMed IDs to be ignored should be added in:

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `interpretation.autoIgnoreReferencePubmedIds`
- Value: [list of PubMedIDs (integers)]
