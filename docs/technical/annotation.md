# Annotation

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

[[toc]]

## Included transcripts

Configure types of transcripts to include from the annotation using regex, e.g. `NM_.*` for RefSeq transcripts.

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `transcripts.inclusion_regex`

## Frequencies

Settings related to population frequency annotation displayed in the FREQUENCY section on the CLASSIFICATION page and in side bars. 

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `frequencies`

### Groups

The key `frequencies.groups` defines which data should be in the `external` and `internal` frequency groups. Note that this also determines which groups can be used in the [frequency filter](/technical/filtering.html#frequency-filter) and [ACMG frequency](/technical/acmg.html#user-group-rules) configuration. 

### View

The key `frequencies.view` defines how frequency data should be shown.

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`groups`    |   Define how to group frequency annotation data.  |
`precision`  |  Float precision (for strings).  |   [integer]
`scientific_threshold`  |   Convert to scientific notation for frequencies below 10^-[x]. |   [integer]
`indications_threshold`  |   Define max threshold to show indications from internal database (depends on how the internal database is set up).  |   [integer]
`[translations]`  |   Define key to be used to link/lookup other sources of information.    |

## Region

Settings related to the REGION section on the CLASSIFICATION page. 

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `similar_alleles`

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`max_variants`    |   Max variants to display in each of the section's cards.  |    [integer]
`max_genomic_distance`  |  Distance in base pairs from a variant (in either direction) within which other, finalized assessments should be searched for.  |   [integer] (bp)

## Consequence 

Define order of severity for transcript consequences given by VEP (high to low). This is used for displaying a warning about "worse consequence" on the CLASSIFICATION page and in the side bar.

- File: `/src/api/config/config.py`
- Key: `config.transcripts.consequences`

## Custom annotation

[TODO]

- Key: `custom_annotation`