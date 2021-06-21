# Annotation

::: warning NOTE
This documentation is a work in progress and is incomplete.

Please contact developers for more details.
:::

[[toc]]

Configuration of both deposit and view of annotation is defined in `annotation-config.yml`, see `src/vardb/testdata/` for an example. The keys `deposit` and `view` define what should happen in the [backend](#annotation-deposit) and [frontend](#annotation-view), respectively. In addition, some configuration relevant for annotation is defined in the [application configuration](#application-configuration) (`ella-config.yml`).

## Annotation deposit

Import of annotation is determined by the latest inserted row in the `annotationconfig` table. This table is created and populated by the migration script, using an import config that reflects the current annotation import.

- File: `annotation-config.yml` 
- Key: `deposit`

All current annotation converters read info from the VCF `INFO` field. The [generic converters](#generic-annotation-converters) should be able to handle most annotation, but [specific converters](#specific-annotation-converters) are necessary in some cases. 

### Generic annotation converters

There are currently four available generic annotation converters: 

- [keyvalue](#keyvalue-keyvalueconverter-py): Use key/value pairs.
- [json](#json-jsonconverter-py): Use base16/32/64-encoded JSON data.
- [mapping](#mapping-mappingconverter-py): Use character separated key/value structures.
- [meta](#meta-metaconverter-py): Use VCF `###INFO` header to create JSON structures.

Of these, the `json`-converter gives the most flexibility, and `keyvalue` the most transparency.

#### Converter output

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

Example config using header line (meta information) `##INFO=<ID=DABLA,Number=.,Type=String,Description="Format: foo|bar">` and annotation value `DABLA=1|2`:

``` yml
- name: meta
  converter_config:
      elements:
          - source: DABLA
            target: PATH.TO.TARGET
            meta_pattern: (?i)[a-z_]+\|[a-z_\|]+ # Default: Used to fetch keys
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

TODO: subkeys, examples 

<!-- Old key/description -->

TODO: Rewrite, what should be removed? 

The key `frequencies.view` defines how frequency data should be shown. 

Subkey	|	Explanation |   Values
:---	|	:---    |	:---
`groups`    |   Define how to group frequency annotation data.  |
`precision`  |  Float precision (for strings).  |   [integer]
`scientific_threshold`  |   Convert to scientific notation for frequencies below 10^-[x]. |   [integer]
`indications_threshold`  |   Define max threshold to show indications from internal database (depends on how the internal database is set up).  |   [integer]
`[translations]`  |   Define key to be used to link/lookup other sources of information.    |

<!-- END old key -->

NOTE: Related `frequencies.groups` is still defined in the application config (`ella-config.yml`).


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
