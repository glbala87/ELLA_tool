# Filtering

[[toc]]



*ella* uses filter chains to reduce the number of variants for interpretation in an analysis. These filter chains are modular, and can consist of multiple filters, each with different configurations.



## General filter config

All filter configs follow the patterns like this:

```json
{
  "name": "FilterA",
  "config": {
    "<FilterA specific config key>": "<FilterA specific config value>"
  }
},
```

The config is specific to the filter with the given name. The available filters can be found in this documentation, and in `api/allelefilter/allelefilter.py`.


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

This filter config specifies to first run FilterA on all passed variants/analysis variants, then run FilterB on the variants not filtered by FilterA. Note that both filters have *FilterB* as an exception, and these will



## Available filters

A set of filters are implemented in ella, and the modularity of them makes is easy to construct complex filter chains, and reasonably easy to implement new filters.

Please see the user documentation for per-filter details.
