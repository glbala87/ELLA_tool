# Import and deposit

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

[[toc]]

Options for import or deposit of variants and/or samples.

## Import

[TODO]

- File: `/src/api/config/config.py`
- Key: `config.import` 

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`automatic_deposit_with_sample_id`  |   [TODO]  |   `True` / `False`
`preimport_script`  |   [TODO]  |   [path]


## Deposit

Processes that should be run when new analyses are deposited into ELLA, configured per [user group](/technical/users.html#user-groups). See `/src/vardb/testdata/usergroups.json` for examples.  

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `config.deposit.analysis`

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`pattern`   |   What analysis name should be matched for this configuration block (e.g. search for user group specific parts in analysis names).    |   [regex]
`postprocess`   |  Processes that should be applied after analyses have been loaded into ELLA.  |   `analysis_not_ready_findings`: Places analyses that have any class 3-5 variants in the "Not ready" section on the OVERVIEW page. `analysis_finalize_without_findings`: Analyses that have no variants that need further work (only benign, no technical issues) are automatically finalized, without any user interaction. 
`prefilter` |   Whether to prefilter this analysis (e.g. high-frequent variants), useful for limiting resource use for large gene panels. Note that these will not be available in the "FILTERED" variants list.    |   `true`/`false`
		
Note that only one user group and one configuration can match any given analysis name. 


## Default import gene panel

Gene panel that should be pre-selected when importing data through the [IMPORT function](/manual/data-import-reanalyses.html#import-variant-data), configured per [user group](/technical/users.html#user-groups). See `/src/vardb/testdata/usergroups.json` for examples. : 

- File: `usergroups.json` (see [user groups](/technical/users.html#user-groups))
- Key: `default_import_genepanel`
- Value: `[gene panel name], [version]`