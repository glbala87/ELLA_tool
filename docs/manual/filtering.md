---
title: Filtering
---

# Filters

Most filters in ella can be used either as normal filter (filtering out variants) or as an exception to another filter (rescuing variants that would normally be filtered).

Please see the filtering section in the technical documentation for more details.

[[toc]]

## Classification filter

The classification filter filters out alleles that have a classification in the database.

Only the current classification (i.e. no previous classifications) per variant is used.

::: danger
The classification filter does not separate between outdated and valid classification.
:::

#### Configuration

-   **Class**: What classes to filter. Variant having classifications with these classes will be filtered out. Must be a subset of the available classes in ella.

**Example:**

This configuration will filter out class 1 and 2 from the provided alleles. This filter can be very useful for exception configuration, where one would typically use e.g. `"classes": ["4", "5"]`.

```json
{
    "name": "classification",
    "config": {
        "classes": ["1", "2"]
    }
}
```

## Consequence filter

The consequence filter filters out variants that are annotated with specific consequences from VEP.

The list of consequences must be a subset of the available [VEP consequences](https://www.ensembl.org/info/genome/variation/prediction/predicted_data.html)

::: tip TIP
Since any given variant can be annotated with many different consequences, this is typically also used as an exception filter _on itself_. This is done to avoid filtering out variants that are e.g. synonymous in one transcript, but `stop_gained` in another.
:::

#### Configuration:

-   **Consequences**: List of consequences to filter on.
-   **Genepanel only**: Whether to only look at consequences in genes within the genepanel.

**Example:**

This will filter out variants that are annotated as `synonymous_variant` or `stop_retained_variant`.

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

The external filter filters on two sources of external annotation, namely HGMD and ClinVar.

::: tip TIP
If it is desired to look for variants that _either_ fulfil some criteria in ClinVar _or_ some criteria in HGMD, this filter can be split in two filters, and just omit the `"hgmd"`-key and `"clinvar"`-key respectively.
:::

#### Configuration

-   **Clinvar**:

    -   **Number of stars**: Sets comparison operator (e.g. greater than) and a number, corresponding to number of stars in Clinvar.
    -   **Combinations**: Combinations of criterias to compare. Given as source, operator and target.

-   **HGMD**:
    -   **Tags**: What HGMD tags to filter on.

In addition, both ClinVar and HGMD have the configuration flag `inverse` (default `False`), which can be used to select variants _not_ fulfulling the given criteria.

**Example:**

With this config, the filter will filter out variants where _each_ of these criterias are fulfilled:

-   The number of stars in clinvar is greater than or equal to two
-   The number of pathogenic or likely pathogenic submissions are greater than the number of benign/likely benign submissions
-   The variant is in HGMD with the tag _DM_ or _DM?_

This specific filter configuration is useful for exceptions.

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

The frequency filter filters out variants based on their allele frequency.

Supports different thresholds for different frequency groups and/or inheritance mode. Also supports setting thresholds for amount of data required at the variant loci.

::: warning NOTE
The frequency filter can not be used as an exception filter
:::

#### Configuration

-   **Filter groups**: Categorizes frequency providers (e.g. gnomAD) and their sub-populations in groups, which can be referred to when specifying filter thresholds. A group `external` could for instance consist of gnomAD with sub-populations G, AMR and AFR. A useful usage example for filter groups could be to separate internal in-house and external databases.

-   **Number threshold**: Allows you to specify a threshold for the number count (number of observed alleles) for each subpopulation. If the number is below the threshold, this sub-population is not used for filtering. Use this to prevent populations with small amount of data from being used as part of filtering.

-   **Frequency threshold**: Sets the actual frequency thresholds. They can be defined for two inheritance types, `AD` and `default`. Thresholds set for `AD` applies to genes which has **only** AD inheritance mode, i.e. not a mix like AD/AR or just AR. `default` applies to everything not in `AD`. For each inheritance mode, you also configure the thresholds for each filter group.

Example configuration:

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

The inheritance model filter filters out variants that are not consistant for the given inheritance model, taking a variant's genes' phenotype inheritance into account.

Only the genes specified in the gene panel is used.

This filter has two different modes:

-   **Recessive non-candidates**: For each gene, if the gene has distinct AR inheritance and the variant is heterozygous and the only variant in the gene, filter it out.
-   **Reccessive candidates**: For each gene, if the gene has **not** distinct AD inheritance, and the variant is either homozygous and the only variant in the gene, or there are multiple variants in the gene, filter it out. _This mode is intended used when filter is used as an exception filter_.

::: warning NOTE
This filter works on proband data only and _does not use family information_.
The target usage is single sample analysis.
:::

::: warning NOTE
By design, only the genes specified in the gene panel are checked. If variant A is located in GENE1 and GENE2, and variant B is located in GENE2 and GENE3, but only GENE1 and GENE3 are in the genepanel, both variant A and B would be filtered out, even though they are compound heterozygous candidates for GENE2.
:::

#### Configuration:

-   **Filter mode**": Either `recessive_non_candidates` or `recessive_candidates`.

**Example:**

```json
{
    "name": "inheritance_mode",
    "config": {
        "filter_mode": "recessive_non_candidates"
    }
}
```

## Polypyrimidine filter

The polypyrimidine filter filters out the following variants in the polypyrimidine tract:
**C>T, T>C, delCC, delTT, delCT and delTC**

::: warning NOTE
On positive stranded transcripts, deletions will not be filtered out if they are preceeded by an A, as this might introduce a new AG splice site.
Similarly, on reverse strand transcripts, deletions will not be filtered out if the are preceeded (in genomic coordinates) by a C.
The filter does **not** check for a new splice site, since ella from the imported data (VCF) only has access to the base preceeding a deletion.
:::

#### Configuration:

-   **Polypyrimidine tract region**: Sets interval in number of bases to treat as polypyrimidine tract region, upstream of exon start.

**Example:**

This will filter out the defined polypyrimidine changes in the region between 3 and 20 bases upstream of the exon start.

```json
{
    "name": "ppy",
    "config": {
        "ppy_tract_region": [-20, -3]
    }
}
```

## Quality filter

The quality filter filters out variants with a low quality, using the VCF _QUAL_ field.

::: warning NOTE
Due to filtering _below_ a certain threshold, this is not suitable as an exception filter.
:::

#### Configuration:

```json
{
    "name": "quality",
    "config": {
        "qual": 100
    }
}
```

Specified like this, the filter will filter out variants that have a VCF _QUAL_ below 100.

## Region filter

The region filter filters out alleles that fall outside the region of interest for the analysis. The region is specified in terms of splice regions and UTR regions.

The genomic regions from the transcript database is used as basis for the filtering. However, if a variant filtered on genomic region is annotated with a HGVS c.DNA position that says that it's within the region, the variant is not filtered. In other words, HGVS information can save a variant from being filtered.

#### Configuration:

-   **Splice region**: Sets number of bases to treat as splice region, upstream from exon start and downstream from exon end. Variants in intron outside the splice region will be filtered.
-   **UTR region**: Sets number of bases to treat as UTR region, upstream from coding start and downstream of coding end. Variants in UTR outside the UTR region will be filtered.

**Example:**

Specified like this, this filter will filter out variants that are

1. Intron variants upstream of 12 bases from exon start
1. Intron variants downstream of 10 bases from exon end
1. 5' UTR variants upstream of 10 bases from the coding start
1. 3' UTR variants downstream of 5 bases from the coding end

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

The segregation filter filters out alleles from a family analysis. It will filter out variants that are _not_ candidate variants for any of these categories:

-   De novo
-   Compound heterozygous
-   Autosomal recessive, homozygous
-   X-linked recessive, homozygous
-   Inherited from possible mosacism in either parent
-   Parents have no coverage
-   Not homozygous in any unaffected siblings

::: warning NOTE
This filter is not suitable as an exception filter.
:::

#### Configuration

This filter has no configuration.
