---
title: ACMG and classification
---

# ACMG criteria and classification

::: warning NOTE
This documentation is a work in progress and is not currently up to date.

Please contact developers for more details.
:::

[[toc]]


## ACMG rules engine

Rules for suggested ACMG criteria are defined in JSON format in:

- File: `/src/rule_engine/mapping_rules.py`
- Key: `rules`

See `/src/rule_engine/README` for details.

### Default values and thresholds

- File: `/src/api/config/config.py`
- Key: `config.user.user_config.acmg`

The following subkeys define default thresholds and values that act as input for the ACMG rules engine. These settings are used if there are no override values defined per [user group](#user-group-overrides) or [gene](#gene-specific-overrides): 

Subkey	|	Explanation	|	Values
:---	|	:---	|	:---
`frequency.thresholds` *    |	The population frequency threshold for ACMG criteria BA1 (`hi_freq_cutoff`) and BS1 (`lo_freq_cutoff`).	|	0-1
`frequency.num_thresholds` *    |   The minimum "allele number" (observed chromosomes at a given locus) for each sub-population.  |   [integer]   
`disease_mode`	|	Whether only missense (`MISS`) or loss of function (`LOF`) mutations, or both (`ANY`), are expected to cause disease.	|	`MISS` / `LOF` / `ANY` (default)
`last_exon_important`	|	Whether the last exon is important (`LEI`) or not (`LENI`).	|	`LEI` (default) / `LENI`

\* Similar to [filter frequency thresholds](/concepts/filtering.html#frequency-filter), with possibilities for separation of dataset groups and inheritance modes.

### User group overrides

[User group](/technical/users.html#user-groups)-specific ACMG value rules. See `/src/vardb/testdata/usergroups.json` for examples. 

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `config.acmg` 

These subkeys define shallow merge overrides of the defaults ([see above](#default-value-rules) for explanation), for the given user group: 

- `frequency.thresholds`
- `frequency.num_thresholds`
- `disease_mode`
- `last_exon_important`

#### Gene-specific overrides

To define rules for given genes only (within a user group), place the above subkeys within the `config.acmg.genes` key, providing a HGNC ID for each gene the rules should apply to.

In addition, the subkey `comment` can be defined, specifying information relevant to evaluation of more/all variants in a gene as free text.

## ACMG descriptions

Short (`short_criteria`) and long (`criteria`) descriptions and any `notes` for each ACMG criterion and [REQ](/concepts/acmg-rule-engine.html#req-requirements) (shown in UI pop-ups) are given in: 

- File: `/src/api/config/acmgconfig.py`
- Key: `acmgconfig["explanation"]`

For REQs, you can also define which ACMG criteria the REQ relates to in this file, using the key `sources`.


## Classification

Sort order and time to outdated (how long an interpretation is considered valid) for clinical classifications is given in:

- File: `/src/api/config/config.py` 
- Key: `classification.options`