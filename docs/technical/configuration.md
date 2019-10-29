---
title: Overview
---

# Configuration: Overview

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

## Contents

These sections describe various configurable aspects of ELLA:

- [Users and user groups](/technical/users.md)
- [Gene panels](/technical/genepanels.md)
- [Filtering](/technical/filtering.md)
- [ACMG and classification](/technical/acmg.md)
- [Import and deposit](/technical/import.md)
- [User interface](/technical/uioptions.md)

## Overview of config files

### Source code

- `/src/api/config/config.py`
- `/src/api/config/acmgconfig.py`
- `/src/rule_engine/mapping_rules.py`

### Fixtures

If you have followed the setup described in [Data directory](/technical/production.html#data-directory), these files are located under `/data/fixtures/`. Examples can be found in `/src/vardb/testdata/`.

- `users.json`
- `usergroups.json`
- `filterconfigs.json`
- `genepanels/`

::: warning NOTE
Do not provide *password* and *password_expiry* in `users.json`. A one-time password that can be used to change password will be generated for each new user added.
:::
