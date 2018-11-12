---
sidebar: auto
---

# Release notes

[[toc]]

## 1.2

### Highlights

#### Family analysis

ella now lets you interpret analyses with variants that have been joint called within a single familiy.

The following segregation models are supported:

- De novo
- Autosomal recessive homozygous
- X-linked recessive
- Compound heterozygous

The most powerful filtering requires two parents to be present in the analysis, but
some segregation filters and tags also apply to analyses with only siblings (unaffected and/or affected).

<div style="text-align: center">
<img style="width: 10rem" src="./img/1-2-family-tags.png">
<br>
<i style="font-size: 80%;">Segregation tags in sidebar</i>
</div>

Variants filtered out by these filters can be found in the `Segregation` category in the excluded variants.


#### Work log

The analysis and variant workflows now have their own `Work log`. The work log currently lets you:

- Update the `Overview comment` (previously `Review comment`)
- Clear any analysis warnings *(analysis only)*. Clearing a warning makes the warning tag disappear from the Overview.
- Adjust the priority of the analysis or variant
- Add messages that should be available to yourself or later interpreters about things that are relevant for the interpretation of the analysis or variant. Messages can contain formatting and images, and are editable until the next interpretation round is started.

All options in the work log can be changed at any time, without having to start a new interpretation round.

<div style="text-align: center;">
<img style="width: 30rem" src="./img/1-2-work-log.png"><br>
<i style="font-size: 80%;">Work log example</i>
</div>

If there are any messages since last time the workflow was `Finalised`, the work log button will appear in purple, along with the current message count.

<div style="text-align: center">
<img style="width: 7rem" src="./img/1-2-worklog-button.png">
<br>
<i style="font-size: 80%;">2 messages since beginning or last finalisation.</i>
</div>

#### Variant warnings

Variants are now tagged with warnings whenever there is something special that considered for the variant in question. The list of warnings will be expanded later, but currently includes:

- Worse consequences in other transcripts
- Other variants are within 3 bp of the variant in the analysis

Variant warnings are implemented for both the variant and analysis workflows, but some warnings are only available for analyses.


<div style="text-align: center">
<img style="width: 40rem" src="./img/1-2-variant-warning-example.png">
<br>
<i style="font-size: 80%;">Example warning.</i>
</div>


<div style="text-align: center">
<img style="width: 25rem" src="./img/1-2-variant-warning-tags.png">
<br>
<i style="font-size: 80%;">Warning tags in sidebar.</i>
</div>


### New features

- Support for family data
- Segregation filter and tags
- Work log
- Variant warnings

### Other additions and fixes
- `Quality` is now it's own section in Classification view (*analysis only*)
- Quality verification for variants in an analysis (`Verified` and `Technical`) is moved from the Info view to the Quality section in the Classification view.
- Variants marked as `Technical` are moved to it's own list in the sidebar.
- Improvements in display of variants with multiple selected transcripts.

## 1.1.2

### Additions and fixes

- Add red 'HOM' tag to top variant bar in order to improve homozygous visibility.
- Merge `utr` and `intron` filters into a new, improved `region` filter.
- Improve search performance (entering a gene is now required for searches using HGVS nomenclature).
- Show more information about the available samples in import view
- Add new external database for gene TP53
- Fix missing Hemi total count for gnomAD


## 1.1.1


### Additions and fixes

- Add BRCA Exchange to external databases for BRCA1 and BRCA2
- Add ability to search using genomic position on format g.123456
- Keep existing reference evaluation data when clicking 'Ignore'
- Fix link and reference description in reference evaluation window.
- Fix issue where some variants would appear with two genepanels in variants overview
- Fix issue where worst consequence would not display correctly for a rare case with variant having intron_variant as consequence in one transcript and splice_region_variant, intron_variant as consequences in another transcript.
- Fix issue importing Pubmed XML data for some references.


## 1.1

### Highlights

#### New import functionality

*Requires access to the import view.*

ella now lets you re-import previously run samples, using either an existing genepanel or a genepanel customised for that specific sample.

This lets you request new analyses directly in the application and shortens the time for reanalysis with a different set of genes.

<div style="text-align: center">
<img style="width: 30rem" src="./img/1-1-import.png">
</div>


#### Frontend code improvements

The frontend code has been refactored to make it more responsive and to make it easier to add new functionality going forward.


### Other additions and fixes

- Display number of excluded references on 'SHOW EXCLUDED' button
- Remove scrollbar on comment fields.
- When there are multiple transcripts in a genepanel, sort them by name. Also display all transcripts in more places, for example in the variants overview.
- Do not add references with Relevance: 'No' to the excluded references list.
- The 'ADD EXCLUDED' window for adding excluded variants now loads faster.
- Search results will now show correctly when typing quickly.
- Many other smaller UI fixes
