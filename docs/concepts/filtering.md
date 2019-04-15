---
title: Filtering
---

# Filters

Filters in _ella_ are applied when loading an analysis, and removes variants from the main view.

Most filters can be used either as a normal filter (filtering out variants) or as an exception to another filter (rescuing variants that would normally be filtered).

Please see the [Technical documentation](/technical/filtering.html#general-filter-config) for further technical specification.

[[toc]]

## Classification filter

The classification filter filters out or rescues alleles that have an existing classification in the in-house database. 

::: danger
The classification filter does not separate between outdated or still valid classifications.
:::

#### Configuration

-   **Class**: List classifications to consider. Must be a subset of the available classes in _ella_.

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

## Consequence filter

The consequence filter filters out or rescues alleles that are annotated with specific [consequences from VEP](https://www.ensembl.org/info/genome/variation/prediction/predicted_data.html).

::: tip TIP
Since any given variant can be annotated with many different consequences, this is typically also used as a filter exception _on itself_. This is done to avoid filtering out variants that are e.g. synonymous in one transcript, but `stop_gained` in another.
:::

#### Configuration

-   **Consequences**: List consequences to use. Must be a subset of the available [VEP consequences](https://www.ensembl.org/info/genome/variation/prediction/predicted_data.html).
-   **Genepanel only**: Specify if only consequences in genes within the current genepanel should be included (`true`/`false`)

##### Example

This configuration will filter out variants that are annotated as either `synonymous_variant` or `stop_retained_variant`.

```json
{
  "name": "consequence",
  "config": {
      "genepanel_only": false
      "consequences": ["synonymous_variant", "stop_retained_variant"]
  }
}
```

## External filter

The external filter filters out or rescues alleles based on annotation from HGMD and/or ClinVar.

::: tip TIP
If you only want to use one of the databases, just omit the other key (`"hgmd"` or `"clinvar"`).
:::

#### Configuration

-   **ClinVar**:

    -   **Number of stars**: Specify a comparison operator (>/</=) and a number (1-4) corresponding to [number of stars in ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/docs/details/#review_status).
    -   **Combinations**: Specify combinations of criterias to compare. Given as source, operator and target.
    -   **Inverse**: Apply to alleles **NOT** fulfulling the given criteria (default `False`).

-   **HGMD**:

    -   **Tags**: List HGMD variant tags to use (one or more of DM/DM?/FTV/DP/DFP/FP).
    -   **Inverse**: Apply to alleles **NOT** fulfulling the given criteria (default `False`).


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

## Frequency filter

The frequency filter filters out alleles based on their population allele frequency. 

May use different frequency thresholds for different dataset groups (data provider/sub-population) and/or inheritance mode. Also supports setting thresholds for number of actual observations required in the dataset.

::: warning NOTE
This filter cannot be used as an exception filter.
:::

#### Configuration

-   **Filter groups**: Categorise dataset providers (e.g. gnomAD) and their sub-populations in groups, which can be referred to when specifying thresholds. A group `external` could for instance consist of gnomAD with sub-populations G, AMR and AFR. This can e.g. be used to separate internal in-house and external datasets.

-   **Number threshold**: Set a threshold for the "Allele number" (number of observed chromosomes at a given locus) for each sub-population. Sub-populations with less observations than the threshold at a given locus (e.g. due to poor coverage) will not be used for filtering at that locus. 

-   **Frequency threshold**: Set population frequency thresholds. They can be defined for two inheritance types, `AD` (autosomal dominant) and `default`. Thresholds set for `AD` applies to genes specified with AD inheritance mode **only**, i.e. not combinations such as AD/AR. `default` applies to everything not in `AD`. For each inheritance mode, you can also configure the thresholds for each filter group (see above) separately.

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

## Inheritance model filter

The inheritance model filter filters out or rescues alleles that are not consistent with the inheritance model for a gene given in the gene panel.

This filter has two different modes:

-   **Recessive non-candidates**: Applies to variants in genes with autosomal recessive (AR) inheritance, where the variant is heterozygous and the only (non-filtered) variant in that gene. Typically used for filtering out variants.
-   **Reccessive candidates**: Applies to variants in genes that are **NOT** autosomal dominant (AD), where the variant is either homozygous or there is at least one other (non-filtered) variant in the same gene. Typically used for rescuing variants from another filter.

::: warning NOTE
This filter is intended for single samples only and _does not use family information_.

By design, only genes specified in the gene panel are checked. This means that if variant A is located in GENE1 and GENE2, and variant B is located in GENE2 and GENE3, but only GENE1 and GENE3 are in the gene panel, both variant A and B would be filtered out, even though they are compound heterozygous candidates for GENE2.
:::

#### Configuration

-   **Filter mode**": Either `recessive_non_candidates` or `recessive_candidates`.

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

## Polypyrimidine filter

The polypyrimidine filter filters out or rescues the following allele changes in the polypyrimidine tract: 

`C>T`, `T>C`, `delCC`, `delTT`, `delCT` and `delTC`

::: warning NOTE
For transcripts on the positive genomic strand, deletions will not be filtered out if they are preceeded by an A, as this might introduce a new AG splice site.
Similarly, on reverse strand transcripts, deletions will not be filtered out if the are preceeded (in genomic coordinates) by a C.

The filter does **not** check for a new splice site, since _ella_ only has access to the base preceeding a deletion from the imported data (VCF).
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

## Quality filter

The quality filter filters out alleles with a low quality, using the VCF _QUAL_ field.

::: warning NOTE
Due to filtering _below_ a certain threshold, this filter is not suitable for exceptions.
:::

#### Configuration

- **Quality** (`qual`): Set threshold value.

##### Example

This configuration will filter out any variant with a _QUAL_ value less than 100.

```json
{
    "name": "quality",
    "config": {
        "qual": 100
    }
}
```

## Region filter

The region filter filters out alleles that fall outside a specified splice or UTR region.

::: warning NOTE
This filter is not suitable as an exception filter.

The genomic regions from the transcript database is used as basis for the filtering. However, if a variant filtered on genomic region is annotated with a cDNA position that says it's within the region, the variant is not filtered. In other words, cDNA information can save a variant from being filtered.
::: 

#### Configuration

-   **Splice region**: Sets number of bases to treat as splice region, upstream from exon start and downstream from exon end. Variants in the intron outside this region will be filtered.
-   **UTR region**: Sets number of bases to treat as UTR region, upstream from coding start and downstream of coding end. Variants in the UTR outside this region will be filtered.

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

## Segregation filter

The segregation filter uses family data to filter out variants that do **NOT** meet any of the following criteria:

-   De novo
-   Compound heterozygous
-   Autosomal/X-linked recessive AND homozygous
-   Inherited from possible mosacism in either parent
-   Parents have no coverage
-   Heterozygous in any unaffected siblings

::: warning NOTE
This filter is not suitable as an exception filter.
:::

#### Configuration

This filter has no configuration.


## Pre-filter (before import)

For large datasets, it is advisable to apply a special pre-filter that removes variants that are *certain* to be benign (e.g. population frequency above 0.05) before importing new data, to reduce the loading time when opening an analysis. 

::: warning NOTE
Variants removed in this way (before import) will not be visible in [FILTERED variants](/manual/filtered-variants.html#filtered-variants) in *ella*. However, *ella* can be configured to include a `VCF` track on the [VISUALISATION page](/manual/visualisation-page.html#analysis-tracks), where these variants would be included.  
:::
