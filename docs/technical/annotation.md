# Annotation

[[toc]]

Configuration of both deposit and view of annotation is defined using a YAML-file (see [annotation-config.yml](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/annotation-config.yml) for an example), deposited in the database using the [ella-cli](/technical/production-tasks.html). This file should contain two keys: 

- `deposit`: Defines how the VCF data in the `INFO` column should be imported into the database.
- `view`: Defines how the resulting annotation JSON (the `annotations` column in the `annotation` table) should be shown in the user interface. 

Using the ella-cli to deposit this file, a row is inserted into the `annotationconfig` table. This table is created and populated by the migration script, using an import config that reflects the legacy annotation import (see `src/vardb/datamodel/migration/alembic/data/annotation-config-legacy.yml`).

Subsequently, for each variant in the VCF, the latest inserted row in the `annotationconfig` table determines how its `INFO` field should be deconstructed, and further, how it should be displayed in the front end.

In addition to the config provided in this table, some configuration relevant for annotation (frequency groups) is defined in the [application configuration](#application-configuration) (`ella-config.yml`).

## Annotation deposit

- File: `annotation-config.yml` 
- Key: `deposit`

All current annotation converters read info from the VCF `INFO` field. The [generic converters](#generic-annotation-converters) should be able to handle most annotation, but [specific converters](#specific-annotation-converters) are necessary in some cases. 

The list under this key follows this structure:

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`name` | Name of the annotation converter to use.  | [string] (See available options below)
`converter_config`  | Config for the annotation converter specified | [object]

The `converter_config.elements` list describes where to get annotation from, and where in the annotation JSON the results should go:

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`source` | VCF `INFO` field to fetch raw annotation from  | [string]
`target`  | JSON path describing where the converted annotation should end up | [string] Paths are split on `.`
`additional_sources` | Additional VCF `INFO` fields used | List of string (optional, only used in specific converters)
[converter specific] | Various converter specific keys | See description for each of the converters below


::: warning NOTE
Target paths beginning with `frequencies`, `transcripts` and `references` hold special meaning.
:::

### Generic annotation converters

There are currently four available generic annotation converters: 

- [keyvalue](#keyvalue-keyvalueconverter-py): Use key/value pairs.
- [json](#json-jsonconverter-py): Use base16/32/64-encoded JSON data.
- [mapping](#mapping-mappingconverter-py): Use character separated key/value structures.
- [meta](#meta-metaconverter-py): Use VCF `###INFO` header to create JSON structures.

Of these, the `json`-converter gives the most flexibility, and `keyvalue` the most transparency.

All of the examples below generate the same output structure to the column `annotations` in the `annotation` table:

``` yml
{
   "PATH": {
       "TO": {
           "TARGET": {
               "foo": 1,
               "bar": 2
           }
       }
   }
}
```

#### keyvalue (`keyvalueconverter.py`)

Read key/value pairs from annotation. 

Specific configuration:

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`target_mode` | How the processed data should be inserted into the JSON | `insert` (default), `extend`, `append`, `merge`
`target_type` | Type to convert the value to | `identity` (default), `float`, `int`, `bool`, `string`
`target_type_throw`* | Whether to throw an error if casting fails | [bool] Default: `true`
`split`**  | String to split raw annotation value on | [string] (optional)

*: If `target_type_throw` is set to False, it will be treated as no annotation found if casting fails.
**: If `split` is defined, the returned value be a list of `target_type` elements.

Example config using annotation values `FOO=1;BAR=2`: 

``` yml
- name: keyvalue
  converter_config:
       elements:
           - source: FOO
             target: PATH.TO.TARGET.foo
             target_type: int
           - source: BAR
             target: PATH.TO.TARGET.bar
             target_type: int
```

#### json (`jsonconverter.py`)

Reads base16/32/64 encoded JSON data and parses it.

Specific configuration:
Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`encoding` | Which encoding the raw data is encoded in | `base16` (default), `base32`, `base64`
`subpath` | Subpath to extract data from | [string] Path split on `.`

Example config using annotation value `MYJSON=7B22666F6F223A20312C2022626172223A20327D`:

``` yml
- name: json
  converter_config:
     elements:
          - source: MYJSON
            target: PATH.TO.TARGET
            encoding: base16
```


Note: `base64.b16encode(json.dumps({"foo": 1, "bar": 2}).encode()).decode() == '7B22666F6F223A20312C2022626172223A20327D'`

#### mapping (`mappingconverter.py`)

Reads character separated (e.g. `,`) key/value structures, separated with e.g. `:`.

Specific configuration:
Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`item_separator` | Separator for the key/value pairs | [string] Default: `,`
`keyvalue_separator` | Separator between key and value | [string] Default: `:`
`target_type` | Type to convert the value to | `identity` (default), `float`, `int`, `bool`, `string`
`target_type_throw`* | Whether to throw an error if casting fails | [bool] Default: `true`

*: If `target_type_throw` is set to False, it will be treated as no annotation found if casting fails.

Example config using annotation value `DABLA=foo:1,bar:2`:

``` yml
- name: mapping
  converter_config:
      elements:
          - source: DABLA
            target: PATH.TO.TARGET
            item_separator: ',' # Default value
            keyvalue_separator: ':' # Default value
            value_target_type: int
```

#### meta (`metaconverter.py`)

Use meta information (`##INFO` header) to create JSON structures, where keys are fetched from the header, and values from the annotation. Requires the meta information line to match a given regex pattern for extracting keys.

Specific configuration:
Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`list_separator` | Split into lists | [string] (optional)
`value_separator` | String that values are split on | [string] Default `\|`
`meta_pattern` | Regex used to fetch keys from the meta description field | Regex string, default: `r"(?i)[a-z_]+\|[a-z_\|]+"`
`subelements` | List of configs | Valid [keyvalue](#keyvalue-keyvalueconverterpy) configs

Example config using header line (meta information) `##INFO=<ID=DABLA,Number=.,Type=String,Description="Format: foo|bar">` and annotation value `DABLA=1|2`:

``` yml
- name: meta
  converter_config:
      elements:
          - source: DABLA
            target: PATH.TO.TARGET
            meta_pattern: (?i)[a-z_]+\|[a-z_\|]+
            element_separator: "|"
            subelements:
                - source: foo
                  target_type: int
                - source: bar
                  target_type: int
```

### Specific annotation converters

In addition to the generic annotation converters, the following specific converters are available:

- `clinvarjson`: Convert current ClinVar data to form expected by database.
- `clinvarreferences`: Read data from ClinVar JSON structure.
- `hgmd`: Read HGMD specific fields.
- `hgmdextrarefs`:  Read data from `HGMD__EXTRAREFS`.
- `vep`:  Read VEP CSQ-field.


## Annotation view

- File: `annotation-config.yml` 
- Key: `view`

With the annotation JSON structure built by the `deposit` key, the `view` key determines what and how the annotation should displayed in the front end's [Classification](/manual/classification-page) page.

The list defined under this key defines the key components required for showing annotation:

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`section` | Define which section of the classification page the annotation should be shown in  | `analysis`, `classification`, `frequency`, `external`, `prediction` or `references`
`template`  |  HTML template to use  | `frequencyDetails`, `itemList`, `keyValue` or `clinvarDetails`. See html-files in `src/webui/src/js/widgets/annotation/`.
`source`  | Which part of the annotation JSON that should be passed to the template |   [string] Paths are split on `.`
`title`  | Title of the sectionbox used to display the annotation |   [string] Default: Last part of the `source`.
`url`*   | Link target of the title | [string] (optional)
`url_empty`*  | Link target of the title when no annotation is available | [string] (optional)
`config`  | Configuration of the view, specific to each template | [object]

*: URLs can be written as template strings, using the `allele` object and `attrs.linkText`. See [annotation-config.yml](https://gitlab.com/alleles/ella-testdata/-/blob/main/testdata/fixtures/annotation-config.yml) for examples.


### Templates

#### frequencyDetails

Shows frequency details in table form. Expects the data for the table to be a nested map:

```json
{
    "column1_key": {
        "row1_key": <value>,
        "row2_key": <value>,
        ...
    },
    "column2_key": {
        "row1_key": <value>,
        "row2_key": <value>,
        ...
    }
}
```

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`key_column` | Row column name | [string]
`columns` | Columns to show | Map of annotation JSON key -> column header display
`rows` | Rows to show | Map of annotation JSON key -> row title display
`filter` | JSON key to fetch filter values | [string] (optional) Filter values not equal to `PASS` will show as a warning
`precision`  |  Float precision (for strings).  |   [integer] (Default: 6)
`scientific_threshold`  |   Convert to scientific notation for frequencies below 10^-[x]. |   [integer] (Default: 4)

#### itemList

Creates a simple list of items, optionally with a URL on each item.

On the config object, under the key `items`, the following config structure is expected:

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`subsource` | Path on the `source` object | [string] (optional)
`url` | URL to link from to from list item | [string] (optional)
`type` | Type of data found at subsource | [string] `object` / `primitives` (default)
`key` | Key to fetch data from | [string] (Only applicable if `type` is `object`)

#### keyValue

Fetches key/value pairs and displays them.

On the config object, under they key `names` an object of this structure is expected:

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`names` | Mapping of keys to display names | Key is used to fetch data from `source`, display name is what is shown in the UI

#### clinvarDetails

Shows data from ClinVar in a format defined by [ella-anno](https://gitlab.com/alleles/ella-anno) and the [ClinVar converter](#specific-annotation-converters). This does not require a special config (should be set to `{}`).

## Application configuration

### Included transcripts

Configure types of transcripts to include from the annotation using regex, e.g. `NM_.*` for RefSeq transcripts.

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `transcripts.inclusion_regex`

### Frequency groups

Defines which data should be in the `external` and `internal` frequency groups in the [frequency filter](/technical/filtering.html#frequency-filter) and [ACMG frequency](/technical/acmg.html#user-group-rules) configuration.

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `frequencies.groups`

Note that this config should match groups defined in `annotation-config.yml`. 

### Region

Settings related to the REGION section on the CLASSIFICATION page. 

- File: `ella_config.yml` (set by `ELLA_CONFIG` [env variable](/technical/production.html#setup-environment))
- Key: `similar_alleles`

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`max_variants`    |   Max variants to display in each of the section's cards.  |    [integer]
`max_genomic_distance`  |  Distance in base pairs from a variant (in either direction) within which other, finalized assessments should be searched for.  |   [integer] (bp)
