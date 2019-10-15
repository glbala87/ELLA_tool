# Filtering

[[toc]]

ELLA uses filter chains to reduce the number of variants for interpretation in an analysis. These filter chains are modular, and can consist of multiple filters, each with different configurations.

## General filter configuration

All filter configurations follow this pattern:

```json
{
  "name": "FilterA",
  "config": {
    "<FilterA specific config key>": "<FilterA specific config value>"
  }
},
```

The configuration is specific to the filter with the given name. The available filters can be found in this documentation, and in `api/allelefilter/allelefilter.py`. 

### Default configuration

The default configuration is used as base when applying any custom filter. Custom filters are shallow merged on top of the defaults. Defaults are given in: 

- File: `src/api/config/config.py`
- Key: `filter.default_filter_config`


### Exceptions

For each filter, we can specify a list of exceptions. These are filters of their own, and filters can (mostly) be used both as filters, or as exception to other filters.

To specify exceptions to the config above, we add the `exceptions` key to the config:

```json
{
  "name": "FilterA",
  "config": {
    "<FilterA specific config key>": "<FilterA specific config value>"
  },
  "exceptions": [
    "name": "FilterB",
    "config": {
      "<FilterB specific config key>": "<FilterB specific config value>"
    }
  ]
},
```

This will first run *FilterA* with the given config, and, before filtering out variants, it will exclude from filtering the variants caught by *FilterB* with the given config.

### Update filter configuration

To update the filter configurations, run the following command:
```
ella-cli filterconfigs update <path to filterconfigs.json>
```

## Filter chains

Filters can be chained together to create a *filter chain*. This will run filters in the order specified.

```json
"filterconfig": {
    "filters": [
        {
          "name": "FilterA",
          "config": {
            "<FilterA specific config key>": "<FilterA specific config value>"
          },
          "exceptions": [
            "name": "FilterB",
            "config": {
              "<FilterB specific config key>": "<Value suitable for exception>"
            }
          ]
        },
        {
          "name": "FilterB",
          "config": {
            "<FilterB specific config key>": "<FilterB specific config value>"
          },
          "exceptions": [
            "name": "FilterB",
            "config": {
              "<FilterB specific config key>": "<Value suitable for exception>"
            }
          ]
        },
    ]
}
```

This filter config specifies to first run FilterA on all passed variants/analysis variants, then run FilterB on the variants not filtered by FilterA. Note that both filters have *FilterB* as an exception.

## Available filters and examples

A set of filters are implemented in ELLA, and the modularity of them makes is easy to construct complex filter chains, and reasonably easy to implement new filters.

See [Concepts](/concepts/filtering.md) for per-filter details and examples, and `src/vardb/testdata/filterconfigs.json` for further examples. 

The schema is located in `src/vardb/datamodel/jsonschemas/filterconfig_v1.json`
