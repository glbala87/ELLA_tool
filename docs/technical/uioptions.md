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

Examples also in [usergroups.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/usergroups.json).

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

It is possible to define templates for most comment fields in ELLA, which are available to add for the user in the text format menu. This is a [user group](/technical/users.html#user-groups) specific setting, see [usergroups.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/usergroups.json) for examples. 

Templates can be defined as pure text or with basic html formatting in: 

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `config.comment_templates` 

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`name`  |   Provide a name for the template |   [text]
`comment_fields`    |   Defines where (which comment fields) the template should be available. |   `classificationAnalysisSpecific`, <br>`classificationEvaluation`, <br>`classificationAcmg`,<br>`classificationReport`, <br>`classificationFrequency`,<br>`classificationPrediction`, <br>`classificationExternal`,<br>`classificationReferences`, <br>`reportIndications`, <br>`reportSummary`, <br>`referenceEvaluation`, <br>`workLogMessage`
`template`  |   Specifies the template    |     [pure text or basic html]

### IGV and tracks in VISUAL

Configuration of IGV and tracks shown in VISUAL mode. 

#### General IGV configuration

General configuration of IGV; see `/example_config.yml` for examples.

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `igv`

Subkey	|	Explanation
:---	|	:---    
`reference`    |   Define what to show as reference data. 
`valid_resource_files`    |   Files permitted accessible on `/igv/<file>` resource, relative to `$IGV_DATA` env.    

All tracks and types have sensible configuration values, so configuration files are not strictly necessary. The default values are merged from the default values in `src/api/v1/resources/igv.py` and the default values in [igv.js](https://github.com/igvteam/igv.js/wiki/Tracks-2.0), with the former taking precedence.

#### Types of tracks in VISUAL

Tracks shown in ELLA VISUAL are of three types: `DYNAMIC`, `STATIC` and `ANALYSIS` tracks.

- Four built-in, `DYNAMIC` tracks are available:
    File path | Description
    :--- | :--- 
    `DYNAMIC/variants` | Shows the unfiltered variants in the analysis
    `DYNAMIC/classifications` | Shows the existing classifications from the database
    `DYNAMIC/genepanel` | Shows the transcripts defined in the gene panel
    `DYNAMIC/regions_of_interest` | Shows unfiltered variants as regions of interest

- `STATIC` tracks can be added as files to the folder `$IGV_DATA/tracks`, with path configured as `STATIC/<filename>`.

- `ANALYSIS` tracks are any track imported together with the analyses. with path configured as `ANALYSIS/<filename>`.

#### Supported track formats

The following track formats are supported: 

Track type | Index file
:--- | :--- 
`.bam` | `.bam.bai, .bai`
`.bed` | -
`.bed.gz` | `.bed.gz.tbi`
`.bigWig` | -
`.cram` | `.cram.crai, .crai`
`.gff3.gz` | `.gff3.gz.tbi`
`.gtf.gz` | `.gtf.gz.tbi`
`.vcf` | -
`.vcf.gz` | `.vcf.gz.tbi`

::: warning NOTE
For best performance, we recommend using index and gzipped files whenever applicable.
::: 

#### Track configuration

- File: `$IGV_DATA/track_config.json` (see [track_config_default.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/igv-data/track_config_default.json) for examples)
- Key: [regex]

Configuration of tracks is done using a single JSON file (`$IGV_DATA/track_config.json`; if no configuration is specified, `track_config_default.json` will be used). The keys of the configuration file are regular expressions (regex) that match file paths (see above). If a file path is matched by multiple regexes, their entries are merged (with the order defined by the position within the config file). 

::: warning NOTE
When writing regex for file paths, note that the JSON format requires all characters with regex functions to be double-escaped using `\\`. E.g., `.bed.gz` should be written as `\\.bed\\.gz`.
:::

Each entry of the config file supports these fields:

Field | Description | Values
:--- | :--- | :--
`limit_to_groups` | Controls access to the track. If one or more user groups are listed here, only those user groups will see the tracks, otherwise (`null`) all users will have access. | [[user groups](/technical/users.html#user-groups); list] or `null`
`presets` | Define which preset(s) the track should belong to. Tracks that are found, available and have no associated preset (including `Default`) are available in the UI under the preset `Other`. | [preset name(s); list]
`show` | Define whether the track should belong to the `Default` preset, which is turned on by default when loading VISUAL for a new analysis (all other tracks are turned off and must be switched on manually). | `true`/`false`
`type` | When `roi`, the track will be displayed as a [region of interest](https://github.com/igvteam/igv.js/wiki/Regions-of-Interest) (e.g. useful for marking the region of a variant). | `roi`/`null`
`url` | A template URL to retrieve the track. The URL will be used for igv.js (`igv.url`) | [URL template]
`description` | Track description, shown when hovering over the track selector button. | See [Track selection](https://allel.es/docs/manual/visual.html#track-selection)
`igv` | Supports all the configuration values of igv.js. The value for `name` will be the track's ID, if not set explicitly. | See [igv.js Tracks 2.0](https://github.com/igvteam/igv.js/wiki/Tracks-2.0)

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
`analysis`  |   `allow_unclassified`    |   Allow unclassified variants when finalizing.  |   `True` / `False`

### Define references as IGNORED

Certain references retrieved from annotation sources such as ClinVar are generic and do not contain information relevant for any particular variant classification per se (an example is the [ACMG guidelines](https://pubmed.ncbi.nlm.nih.gov/25741868)). These references can be set to be automatically [IGNORED](/manual/evidence-sections.html#reference-evaluation) in the reference evaluation module. 

This is a [user group](/technical/users.html#user-groups) specific setting, see [usergroups.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/usergroups.json) for examples. PubMed IDs to be ignored should be added in:

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `interpretation.autoIgnoreReferencePubmedIds`
- Value: [list of PubMedIDs (integers)]
