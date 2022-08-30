# Users and user groups

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

[[toc]]

## Users and passwords

ELLA users and associated data are defined in the file `users.json`. 

To add new or update existing users, run the following command:

``` bash
ella-cli users add_many <path to users.json>
```

This will print a one-time password to screen for each user that was added. This password is auto-expired and should be used by each user to set a new password upon first login.

::: warning NOTE
User configuration history is currently not tracked in the datamodel, so changes should be tracked externally.
:::

User example:

```json
[
    {
        "username": "testuser1",
        "first_name": "Henrik",
        "last_name": "Ibsen",
        "email": "testuser1@foo.bar",
        "group": "testgroup01"
    }
]
```

See also [users.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/users.json) and [Reset user password](/technical/production-tasks.html#reset-user-password).

::: warning NOTE
For simplicity, `password` and `password_expiry` are provided in the testdata version of `users.json`. However, this should _not_ be done in production, as this may have undesired side effects. Instead, use the procedure [above](#users-and-passwords).
:::

## User configuration

Default settings for all users (shallow merged with usergroup's and user's config at runtime). See `/example_config.yml` for examples. 

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `user`

### Password requirements

Requirements for valid password.

- Key: `user.auth`

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`password_expiry_days`  |   Days before password has to be renewed. |   [integer]
`password_minimum_length`   |   Minimum length of valid password. |   [integer]
`password_match_groups`   |   Character types in valid password. |   [regex]
`password_match_groups_descr`   |   Descriptions for character types. |   [free text]
`password_num_match_groups`   |   Number of character types required for valid password.  |   [integer]


### User interface, workflow and ACMG

Settings related to user interface, workflow and ACMG rules. 

- Key: `user.user_config`

See: 
- [Overview](/technical/uioptions.html#overview-and-info-page) (subkey: `overview`)
- [Workflows](/technical/uioptions.html#finalize-requirements) (subkey: `workflows`)
- [ACMG default values and thresholds](/technical/acmg.html#default-values-and-thresholds) (subkey: `acmg`)


## User groups

A user group defines the configuration for different groups of users. This includes settings for: 

- [Gene panels](#user-groups-and-gene-panels)
- [Group settings for the ACMG rules engine](/technical/acmg.html#user-group-overrides)
- [Import and deposit](/technical/import.md)  
- [User interface for groups](/technical/uioptions.html#configure-elements-to-show)

See [usergroups.json](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/usergroups.json) for examples.

To update the user groups, run the following command:

``` bash
ella-cli users add_groups <path to usergroups.json>
```

This will add new or update existing user groups with the new configurations options.

::: warning NOTE
User group configuration history is currently not tracked in the data model, so changes should be tracked externally.
:::

### User groups and gene panels

ELLA's current access model revolves around gene panels, which control which analyses and variants are available to a given user. It is therefore important to ensure that this is configured correctly, and if new gene panels (including updated versions) are added to the system, that the configuration is updated accordingly.

- File: `usergroups.json`
- Key: `genepanels`
- Value: list of `[gene panel name], [version]`
