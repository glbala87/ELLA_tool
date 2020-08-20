# Production tasks using the ella-cli

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

This page describes common production tasks that can be performed with the [ELLA command line interface](/technical/#command-line-interface-ella-cli) (ella-cli). 

::: tip TIP
The `--help` flag will show information for most `ella-cli` commands and options.
:::

[[toc]]

## Manage broadcast messages

To add a new broadcast message for all users (shown below the top banner, e.g. for notifications of planned downtime), run: 

``` bash
ella-cli broadcast new <message>
```

To deactivate a previously added message, run: 

``` bash
ella-cli broadcast list # get active message_id
ella-cli broadcast deactivate <message_id>
```

Add the `--all` or `--tail` flag to the `ella-cli broadcast list` command to show all or the last 10 broadcasts, respectively (including inactive).

## Reset user password

To reset the password for a single user, run: 

``` bash
ella-cli users reset_password <username>
```

This will print a new one-time password to screen, and must be changed upon first new login.

See also [Users and passwords](/technical/users.html#users-and-passwords).

## Delete analysis

To delete an existing analysis (e.g. wrong import), run: 

``` bash
ella-cli delete analysis <analysis_id>
```

where `analysis_id` is the last part of the URL shown in ELLA, e.g. [...]/workflows/analyses/**12345**. 

Note that this will not delete any interpretations that have been performed within the analysis; instead, `analysis_id` is set to `NULL` in the `alleleassessment`, `referenceassessment`, `allelereport` and `geneassessment` tables. This means that any associated allele assessments will appear as having been done in a variant workflow (i.e. independent of the analysis) after analysis deletion.


## Delete allele interpretation

To delete interpretation rounds for an individual allele since last finalize, run: 

``` bash
ella-cli delete alleleinterpretation <allele_id>
```

where `allele_id` is the last part of the URL shown in ELLA when opening the variant in variant interpretation mode, e.g. [...]/workflows/variants/[...]&allele_id=**123**

To delete all interpretation rounds (not only since last finalize; use with caution), add the `--delete-all` flag. This will cascade the delete operation to `alleleinterpretationsnapshot`, `interpretationstatehistory` and `interpretationlog`.

Note that neither option deletes allele assessments (the finalized snapshot that includes a classification, see [Datamodel](/technical/datamodel.html#introduction)).