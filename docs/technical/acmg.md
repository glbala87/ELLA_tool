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

### User group rules

[User group](/technical/users.html#user-groups)-specific ACMG value rules. See [usergroups.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/usergroups.json) for examples. 

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `config.acmg` 

The following subkeys define thresholds and values that act as input for the ACMG rules engine, for the given user group: 

Subkey	|	Explanation	|	Values
:---	|	:---	|	:---
`frequency.thresholds` *    |	The population frequency threshold for ACMG criteria BA1 (`hi_freq_cutoff`) and BS1 (`lo_freq_cutoff`).	|	0-1
`frequency.num_thresholds` *    |   The minimum "allele number" (observed chromosomes at a given locus) for each sub-population.  |   [integer]   
`disease_mode`	|	Whether only missense (`MISS`) or loss of function (`LOF`) mutations, or both (`ANY`), are expected to cause disease.	|	`MISS` / `LOF` / `ANY` (default)
`last_exon_important`	|	Whether the last exon is important (`LEI`) or not (`LENI`).	|	`LEI` (default) / `LENI`

\* Similar to [filter frequency thresholds](/technical/filtering.html#frequency-filter), with possibilities for separation of dataset groups and inheritance modes.

#### Gene-specific overrides

To define rules for given genes only (within a user group), place the above subkeys within the `config.acmg.genes` key, providing a HGNC ID for each gene the rules should apply to.

In addition, the subkey `comment` can be defined, specifying information relevant to evaluation of more/all variants in a gene as free text.

## ACMG descriptions

Short (`short_criteria`) and long (`criteria`) descriptions and any `notes` for each ACMG criterion and [REQ](/manual/acmg-rule-engine.html#req-requirements) (shown in UI pop-ups) are given in: 

- File: `/src/api/config/acmgconfig.py`
- Key: `acmgconfig["explanation"]`

For REQs, you can also define which ACMG criteria the REQ relates to in this file, using the key `sources`.


## Classification

Sort order and how long an interpretation should be considered valid (`outdated_after_days`) for clinical classifications is given in:

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment)) 
- Key: `classification.options`

See [`example_config.yml`](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/example_config.yml) for examples.