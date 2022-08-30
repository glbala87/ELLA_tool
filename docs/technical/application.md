# Application configuration

Various settings related to setup of ELLA. See `/example_config.yml` for examples, and [Configuration overview](/technical/configuration.html#application-configuration) for how to specify environment variables.

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `app`

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`links_to_clipboard`    |   Define if links should be copied to clipboard instead of opening a browser. |   Boolean 
`non_production_warning`    |   Show warning (e.g. STAGING or TEST) when running a non-production environment.  |    String
`annotation_service`    |   Define URL for annotation service. |    String (url)
`attachment_storage`    |   Define path to attachment storage.  |   String (path)
`max_upload_size`   |   Define max size of file uploads in bytes. |   Example: `52428800` (= 50 MB)
`feature_flags`   |   Enable or disable special features. Currently includes CNV support only, set by `cnv: !env_bool [ENABLE_CNV, true/false]`    |   Boolean

::: warning NOTE
CNV support is currently experimental and is disabled by default. Enabling this feature will start deposit of CNV alleles and add a CNV mode for variants of type = `SVTYPE`.
:::