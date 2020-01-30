---
title: Overview
---

# Configuration: Overview

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

## Contents

The following pages describe various configurable aspects of ELLA:

- [Application](/technical/application.md)
- [Users and user groups](/technical/users.md)
- [User interface](/technical/uioptions.md)
- [Annotation](/technical/annotation.md)
- [Gene panels](/technical/genepanels.md)
- [Import and deposit](/technical/import.md)
- [Filtering](/technical/filtering.md)
- [ACMG and classification](/technical/acmg.md)


## Overview of config files

### Application configuration

The main configuration of the ELLA application (excluding any data that is imported into the database, such as user/user group specific settings; see [Fixtures](#fixtures)) is set in a YAML file given by the `ELLA_CONFIG` environment variable, e.g. `/config/ella_config.yml`. This can also be used to set defaults for various user group settings. 

In the YAML file, you may use environment variables using YAML constructors, such as `my_key: !env ENVIRONMENT_VARIABLE`, or `my_key: !env [ENVIRONMENT_VARIABLE, "default"]`. Custom YAML constructors available are `!env_bool`, `!env_int`, `!env_float`, and `!file` (file path relative to ELLA root folder).

Options for various settings are described in the [above referred pages](#contents). See also `/example_config.yml` for examples. 

### Fixtures

Fixtures include any kind of configuration data that should be imported into the database. If you have followed the setup described in [Data directory](/technical/production.html#data-directory), the following files are located under `/data/fixtures/`:

File/subfolder | Configuration of ... | More info
:--|:--|:--
`users.json` | User details | [Users](/technical/users.html#users-and-passwords)
`usergroups.json`| User group specific gene panels, ACMG rules, import, UI | [User groups](/technical/users.html#user-groups)
`filterconfigs.json` | Variant filters | [Filtering](/technical/filtering.html)
`genepanels/` | Gene panels (transcripts, phenotypes, ...) | [Gene panels](/technical/genepanels.html)

Examples can be found in `/src/vardb/testdata/`.

### Source code

Some configuration that should usually not be changed is located in the source code. This includes: 

File | Configuration of ... | More info
:--|:--|:--
`/src/api/config/config.py` | VEP and ClinVar related settings | []()
`/src/api/config/acmgconfig.py` | Definition of ACMG criteria and REQs | [ACMG descriptions](/technical/acmg.html#acmg-descriptions)
`/src/rule_engine/mapping_rules.py` | Rules for suggested ACMG criteria and REQs | [ACMG rules engine](/technical/acmg.html#acmg-rules-engine)