# Users and user groups

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

[[toc]]

## Users

ELLA users and associated data are defined in the file `users.json`. 

To add new or update existing users, run the following command:
```
ella-cli users add_many <path to users.json>
```

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

See also `/src/vardb/testdata/users.json`

## User configuration

Default settings for all users (shallow merged with usergroup's and user's config at runtime). See `/src/api/config/config.py` for examples. 

- File: `/src/api/config/config.py`
- Key: `config.user`


### Authentication: Passwords

Requirements for valid password.

- Key: `config.user.auth`

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`password_expiry_days`  |   Days before password has to be renewed. |   [integer]
`password_minimum_length`   |   Minimum length of valid password. |   [integer]
`password_match_groups`   |   Character types in valid password. |   [regex]
`password_match_groups_descr`   |   Descriptions for character types. |   [free text]
`password_num_match_groups`   |   Number of characted types required for valid password.  |   [integer]


### User interface, workflow and ACMG

Settings related to user interface, workflow and ACMG rules. 

- Key: `config.user.user_config`

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

See `/src/vardb/testdata/usergroups.json` for examples.

To update the user groups, run the following command:
```
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
