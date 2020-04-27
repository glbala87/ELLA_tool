# Filtering

[[toc]]

ELLA uses filter chains when loading an analysis to reduce the number of variants for interpretation. These filter chains are modular, and can consist of multiple filters, each with different configurations.

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

The configuration is specific to the filter with the given name. The available filters can be found in this documentation, and in `/src/api/allelefilter/allelefilter.py`. 

### Exceptions

For each filter, we can specify a list of exceptions, i.e. rules for when the filter should not apply. Many filter rules can be used both as filters or as exception to other filters.

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

### Filter chains

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

### Update filter configuration

To update the filter configurations, run the following command:
```
ella-cli filterconfigs update <path to filterconfigs.json>
```

## Available filters and examples

A set of filters are implemented in ELLA, and are described below. The modularity of these filters makes is easy to construct complex filter chains, and reasonably easy to implement new filters. Most filters can be used either as a normal filter (filtering out variants) or as an exception to another filter (rescuing variants that would normally be filtered).

- [Classification filter](#classification-filter)
- [Consequence filter](#consequence-filter)
- [External filter](#external-filter)
- [Frequency filter](#frequency-filter)
- [Gene filter](#gene-filter)
- [Inheritance model filter](#inheritance-model-filter)
- [Polypyrimidine filter](#polypyrimidine-filter)
- [Quality filter](#quality-filter)
- [Region filter](#region-filter)
- [Segregation filter](#segregation-filter)
- [Pre-filter (before import)](#pre-filter-before-import)

See also `/src/vardb/testdata/filterconfigs.json` for examples of a complete setup. The schema is located in `/src/vardb/datamodel/jsonschemas/filterconfig_v1.json`.

### Classification filter

The classification filter filters out or rescues alleles that have an existing classification in the in-house database. 

::: danger WARNING
The classification filter does not separate between outdated or still valid classifications.
:::

#### Configuration

-   **Classes** (`classes`): List classifications to consider. Must be a subset of the available classes in ELLA.

##### Example

This configuration will filter out alleles with class 1 and 2 (change to e.g. `"classes": ["4", "5"]` to instead rescue alleles with class 4 and 5).

```json
{
    "name": "classification",
    "config": {
        "classes": ["1", "2"]
    }
}
```

### Consequence filter

The consequence filter filters out or rescues alleles that are annotated with specific [consequences from VEP](https://www.ensembl.org/info/genome/variation/prediction/predicted_data.html).

::: tip TIP
Since any given variant can be annotated with many different consequences, this is typically also used as a filter exception _on itself_. This is done to avoid filtering out variants that are e.g. synonymous in one transcript, but `stop_gained` in another.
:::

#### Configuration

-   **Consequences** (`consequences`): List consequences to use. Must be a subset of the available [VEP consequences](https://www.ensembl.org/info/genome/variation/prediction/predicted_data.html).

-   **Gene panel only** (`genepanel_only`): Specify if only consequences in genes within the current gene panel should be included (`true`/`false`)

##### Example

This configuration will filter out variants that are annotated as either `synonymous_variant`, `stop_retained_variant` or `start_retained_variant`.

```json
{
  "name": "consequence",
  "config": {
      "genepanel_only": false
      "consequences": ["synonymous_variant", "stop_retained_variant", "start_retained_variant"]
  }
}
```

### External filter

The external filter filters out or rescues alleles based on annotation from HGMD and/or ClinVar.

::: tip TIP
If you only want to use one of the databases, just omit the other key (`hgmd` or `clinvar`).
:::

#### Configuration

-   **ClinVar**:

    -   **Number of stars** (`num_stars`): Specify a comparison operator (>/</=) and a number (1-4) corresponding to [number of stars in ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/docs/details/#review_status).
    -   **Combinations** (`combinations`): Specify combinations of criteria to compare. Given as source, operator and target.
    -   **Inverse** (`inverse`): Apply to alleles **NOT** fulfilling the given criteria (default `False`).

-   **HGMD**:

    -   **Tags** (`tags`): List HGMD variant tags to use (one or more of DM/DM?/FTV/DP/DFP/FP).
    -   **Inverse** (`inverse`): Apply to alleles **NOT** fulfilling the given criteria (default `False`).


##### Example

This configuration is useful for exceptions, and will rescue alleles where _each_ of these criterions are fulfilled:

-   The variant is in ClinVar and the number of stars is two or more.
-   The number of `pathogenic` or `likely pathogenic` submissions are greater than the number of `benign`or `likely benign` submissions.
-   The variant is in HGMD with the tags `DM` or `DM?`.

```json
{
    "name": "external",
    "config": {
        "clinvar": {
            "num_stars": [">=", 2],
            "combinations": [["pathogenic", ">", "benign"]],
            "inverse" False,
        },
        "hgmd": {
            "tags": ["DM", "DM?"],
            "inverse" False,
        }
    }
}
```

### Frequency filter

The frequency filter filters out alleles based on their population allele frequency. 

May use different frequency thresholds for different data set groups (data provider/sub-population) and/or inheritance mode. Also supports setting thresholds for number of actual observations required in the data set.

::: warning NOTE
This filter cannot be used as an exception filter.
:::

#### Configuration

-   **Filter groups** (`groups`): Categorize data set providers (e.g. gnomAD) and their sub-populations in groups, which can be referred to when specifying thresholds. A group `external` could for instance consist of gnomAD with sub-populations G, AMR and AFR. This can e.g. be used to separate internal in-house and external data sets.

-   **Number threshold** (`num_thresholds`): Set a threshold for the "Allele number" (number of observed chromosomes at a given locus) for each sub-population. Sub-populations with less observations than the threshold at a given locus (e.g. due to poor coverage) will not be used for filtering at that locus. 

-   **Frequency threshold** (`thresholds`): Set population frequency thresholds (0-1). They can be defined for two inheritance types, `AD` (autosomal dominant) and `default`. Thresholds set for `AD` applies to genes specified with AD inheritance mode **only**, i.e. not combinations such as AD/AR. `default` applies to everything not in `AD`. For each inheritance mode, you can also configure the thresholds for each filter group (see above) separately.

##### Example

This configuration will filter out variants that are:

1. GnomAD genomes or exomes, total populations (`external`, `G`)
    - More than 5000 observed chromosomes
    - Higher than 0.005 frequency in AD genes
    - Higher than 0.01 frequency for other inheritance modes

2. In-house database (`internal`, `OUSWES`)
    - Higher than 0.05 frequency for any inheritance mode

```json
{
    "name": "frequency",
    "config": {
        "groups": {
            "external": {
                "GNOMAD_GENOMES": ["G"],
                "GNOMAD_EXOMES": ["G"]
            },
            "internal": {
                "inDB": ["OUSWES"]
            }
        },
        "num_thresholds": {
            "GNOMAD_GENOMES": {
                "G": 5000
            },
            "GNOMAD_EXOMES": {
                "G": 5000
            }
        },
        "thresholds": {
            "AD": {
                "external": 0.005,
                "internal": 0.05
            },
            "default": {
                "external": 0.01,
                "internal": 0.05
            }
        }
    }
}
```

### Gene filter

The gene filter filters out or rescues alleles that are within a given gene. 

:::warning NOTE
The annotation is matched on gene panel with transcript (excluding RefSeq versioning). This means that it will only take into account variants annotated with gene panel transcript(s).
:::


#### Configuration

- **Genes** (`genes`): List of HGNC IDs to apply filter to.

- **Filter mode** (`mode`); either: 

    - **All** (`all`) (default): Variant must be annotated with genes specified in `genes` *only*. This is useful for filtering out.
    - **One** (`one`): Variant must be annotated with _at least_ one gene from `genes` (but could be annotated with other genes). This is useful for exceptions.

- **Inverse** (`inverse`): Apply to alleles **NOT** fulfilling the given criteria (default `False`)

##### Examples

This configuration will filter out all variants annotated with BRCA1 (1100) and/or BRCA2 (1101), but not if they are also annotated on gene panel transcripts for any other gene:

```json
{
    "name": "gene",
    "config": {
        "genes": [1100, 1101],
        "mode": "all",
    }
}
```

This configuration will filter out all variants _not_ annotated with either BRCA1 (1100) or BRCA2 (1101):
    
```json
{
    "name": "gene",
    "config": {
      "genes": [1100, 1101],
      "mode": "one",
      "inverse": True,
   }
}
```

### Inheritance model filter

The inheritance model filter filters out or rescues alleles that are not consistent with the inheritance model for a gene given in the gene panel.

::: warning NOTE
This filter is intended for single samples only and _does not use family information_.

By design, only genes specified in the gene panel are checked. This means that if variant A is located in GENE1 and GENE2, and variant B is located in GENE2 and GENE3, but only GENE1 and GENE3 are in the gene panel, both variant A and B would be filtered out, even though they are compound heterozygous candidates for GENE2.
:::

#### Configuration

-   **Filter mode** (`filter_mode`); either:

    -   **Recessive non-candidates** (`recessive_non_candidates`): Applies to variants in genes with autosomal recessive (AR) inheritance, where the variant is heterozygous and the only (non-filtered) variant in that gene. Typically used for filtering out variants.
    -   **Recessive candidates** (`recessive_candidates`): Applies to variants in genes that are **NOT** autosomal dominant (AD), where the variant is either homozygous or there is at least one other (non-filtered) variant in the same gene. Typically used for rescuing variants from another filter.


##### Example

This configuration will filter out variants meeting the criteria for _Recessive non-candidates_.

```json
{
    "name": "inheritance_mode",
    "config": {
        "filter_mode": "recessive_non_candidates"
    }
}
```

### Polypyrimidine filter

The polypyrimidine filter filters out or rescues the following allele changes in the polypyrimidine tract: 

`C>T`, `T>C`, `delCC`, `delTT`, `delCT` and `delTC`

::: warning NOTE
For transcripts on the positive genomic strand, deletions will not be filtered out if they are preceded by an A, as this might introduce a new AG splice site.
Similarly, on reverse strand transcripts, deletions will not be filtered out if the are preceded (in genomic coordinates) by a C.

The filter does **not** check for a new splice site, since ELLA only has access to the base preceding a deletion from the imported data (VCF).
:::

#### Configuration

-   **Polypyrimidine tract region** (`ppy_tract_region`): Set interval in number of bases to treat as polypyrimidine tract region, upstream of exon start.

##### Example

This configuration will filter out the specified polypyrimidine changes in the region between 3 and 20 bases upstream of the exon start.

```json
{
    "name": "ppy",
    "config": {
        "ppy_tract_region": [-20, -3]
    }
}
```

### Quality filter

The quality filter filters out alleles with a low quality, either using the VCF _QUAL_ field or the allele ratio. The latter is calculated in ELLA as alternative allele reads/total reads (presented as "Ratio" in the Quality card). 

::: warning NOTE
Due to filtering _below_ a certain threshold, this filter is not suitable for exceptions.

Also note that although a skewed allele ratio is most often indicative of technical artifacts, it may also indicate _somatic mosaicism_. This variable should therefore not be used in patients where mosaicism is suspected. 
:::

#### Configuration

- **Quality** (`qual`): Set threshold value (integer).
- **Allele ratio** (`allele_ratio`): Set threshold value (0-1).

##### Example

This configuration will filter out any variant with _QUAL_ <100 AND allele ratio <0.25:

```json
{
    "name": "quality",
    "config": {
        "qual": 100,
        "allele_ratio": 0.25
    }
}
```

### Region filter

The region filter filters out alleles that fall outside a specified splice or UTR region.

::: warning NOTE
This filter is not suitable as an exception filter.

The genomic regions from the transcript database is used as basis for the filtering. However, if a variant filtered on genomic region is annotated with a cDNA position that says it's within the region, the variant is not filtered. In other words, cDNA information can save a variant from being filtered.
::: 

#### Configuration

-   **Splice region** (`splice_region`): Sets number of bases to treat as splice region, upstream from exon start and downstream from exon end. Variants in the intron outside this region will be filtered.
-   **UTR region** (`utr_region`): Sets number of bases to treat as UTR region, upstream from coding start and downstream of coding end. Variants in the UTR outside this region will be filtered.

##### Example

This configuration will filter out:

1. Intron variants 
    - Upstream (5') of 12 bases from exon start AND
    - Downstream (3') of 10 bases from exon end

2. UTR variants 
    - Upstream (5') of 10 bases from the coding start OR
    - Downstream (3') of 5 bases from the coding end

```json
{
    "name": "region",
    "config": {
        "splice_region": [-12, 10],
        "utr_region": [10, 5]
    }
}
```

### Segregation filter

The segregation filter uses family data to filter out any variants that do **NOT** meet any of the following criteria:

- [De novo variant](#de-novo-variant)
- [Compound heterozygous candidate](#compound-heterozygous-candidate)
- [Homozygous recessive variant](#homozygous-recessive-variant) 
- [Inherited mosaicism](#inherited-mosaicism)
- Either parent is missing a genotype

This filter has no regular configuration, although some settings may be adjusted in the source code.

::: warning NOTES
- This filter is not suitable as an exception filter.
- For the purposes below, variants in the pseudo-autosomal X-chromosome regions PAR1 and PAR2 (X:60001-2699520 and X:154931044-155260560 on GRCh37) are treated as autosomal, _not_ X-linked.
:::

#### De novo variant

Designating a variant as de novo is based on rules given in [Vigeland et al. (2016)](https://doi.org/10.1093/bioinformatics/btw046). Genotype inheritance patterns that designates a variant allele "1" (reference = "0") as de novo in the child (father + mother = child) are:

- For autosomal or pseudo-autosomal regions:
    - 0/0 + 0/0 = 0/1
    - 0/0 + 0/0 = 1/1
    - 0/0 + 0/1 = 1/1
    - 0/1 + 0/0 = 1/1
- For X-linked regions, child is a boy:
    - 0 + 0/0 = 1
- For X-linked regions, child is a girl:
    - 0 + 0/0 = 0/1
    - 0 + 0/0 = 1/1
    - 0 + 0/1 = 1/1

::: warning NOTE
If a male trio member is reported as heterozygous for an X-linked variant, the variant will be filtered out.
:::

#### Compound heterozygous candidate

Variants are designated as compound heterozygous candidates based on the rule set from [Kamphans et al. (2013)](https://doi.org/10.1371/journal.pone.0070151): 

1. A variant has to be in a heterozygous state in all affected individuals.
2. A variant must not occur in a homozygous state in any of the unaffected individuals.
3. A variant that is heterozygous in an affected child must be heterozygous in exactly one of the parents.
4. A gene must have two or more heterozygous variants in each of the affected individuals.
5. There must be at least one variant transmitted from the paternal side and one transmitted from the maternal side.

::: warning NOTE
For the third rule, note this excerpt from the article:

"[This rule] is applicable only if we assume that no de novo mutations occurred. The number of de novo mutations is estimated to be below five per exome per generation, thus, the likelihood that an individual is compound heterozygous and at least one of these mutations arose de novo is low. If more than one family member is affected, de novo mutations are even orders of magnitudes less likely as a recessive disease cause. On the other hand, excluding these variants from the further analysis helps to remove many sequencing artifacts."
::: 

#### Homozygous recessive variant

This rule set checks for homo-/hemizygous variants. The following conditions must be met:

- For autosomal or pseudo-autosomal regions:
    - Homozygous in the proband and any affected siblings.
    - Heterozygous in both parents.
    - Not homozygous in unaffected siblings.
- For X-linked regions: 
    - Homo-/hemizygous in the proband and any affected siblings (note: for girls this requires a de novo, but still valid case).
    - Heterozygous in mother.
    - Not present in father.
    - Not homo-/hemizygous in unaffected siblings


#### Inherited mosaicism

This rule set checks whether a variant is inherited from a parent with possible allelic mosaicism (excluding cases where the other parent has a normal genotype). The following conditions must be met:

- Proband: 
    - Has variant.
    - Genotype is heterozygous or hemizygous (for X-linked regions). 
- Either parent has an `allele_ratio` between given thresholds: 
    - For autosomal or pseudo-autosomal regions: [0, 0.3]
    - For X-linked regions: 
        - Mother: [0, 0.3]
        - Father: [0, 0.8]
- Other parent does not have an `allele_ratio` outside given thresholds (i.e., rule fails if the other parent has a normal genotype).

### Pre-filter (before import)

For large data sets, it is advisable to apply a special pre-filter that removes variants that are *certain* to be benign (e.g. population frequency above 0.05) before importing new data, to reduce the loading time when opening an analysis. 

::: warning NOTE
Variants removed in this way (before import) will not be visible in [FILTERED variants](/manual/filtered-variants.html#filtered-variants) in ELLA. However, ELLA can be configured to include a `VCF` track in the [VISUAL mode](/manual/visual.html#analysis-tracks), where these variants would be included.  
:::
