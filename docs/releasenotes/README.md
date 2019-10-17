---
title: Latest release
---

# Release notes: Latest release

See [Older releases](/releasenotes/olderreleases.md) for earlier versions.

## Version 1.8

Release date: [TBD]

### Highlights

#### Finalize variant in analysis

[WIP] It is now possible to finalize a variant interpretation within an ANALYSIS workflow. 

#### User group tags and warnings

[WIP] Every variant interpretation now gets tagged with the user group finalizing the workflow. Whenever a user opens a variant interpretation that was previously finalized by a user from another user group, ELLA now displays a warning. This is to ensure that current interpretations included in a clinical report always reflects the procedures of the current user group. 

#### ACMG: Add "other" and unweighted criteria

Sometimes, criteria that don't match the ACMG guidelines are important for a variant interpretation, e.g. the ENIGMA criteria for the BRCA1/BRCA2 genes. ELLA now allows adding these to the interpretation as a generic `OTHER` criterion. The type and impact on the classification should be given in this criterion's comment field once added. 

In addition, users can often spend significant time evaluating an ACMG criterion for a particular interpretation, but in the end decide that the requirements are not met. ELLA now allows setting an added ACMG criterion as `NOT WEIGHTED`, so that comments related to this work can be properly recorded.

<div style="text-indent: 4%;">
    <img src="./img/1-8-ACMG-other-unweighted.png">
    <br>
    <div style="font-size: 80%;">
        <strong>Figure: </strong>The new "other" criterion and unweighted option for ACMG criteria.
    </div>
    <br>
</div>

Note that neither "other" or unweighted ACMG criteria are counted in the calculation of suggested classification.

#### Filter improvements: Gene and allele ratio

The filter settings now allows using genes as a variable in rules for filters or exceptions. This allows conditioning any rule on the presence/absence of a gene. 

In addition, it is now also possible to use allele ratio a variable in the quality filter. In our experience, this gives a more powerful filter than using the `qual` variable, removing more true technical variants, but with the caveat that mosaic variants may be missed. 


### All changes

- [WIP] Finalize variant in analysis.
- [WIP] User group tags and warnings.
- [MR !317] Added possibility to configure certain reference PubMed IDs to be automatically IGNORED, relevant for recurring, generic references from the annotation that are not relevant to variant interpretation. See [Technical documentation](/technical/uioptions.html#define-references-as-ignored) for details.
- [MR !318] Made controls FULL - QUICK - VISUAL and INDICATION comment field in the sidebar sticky to reduce need for scrolling when there are many variants.
- [MR !318] Made collision warnings below the top bar sticky and collapsible.
- [MR !319] Improved Technical documentation
- [MR !320] Fixed bug causing inability to finish an analysis workflow when all variants were marked as "Not relevant".
- [MR !322] Added better test data.
- [MR !324] [Add non-ACMG criteria](#acmg-add-other-and-unweighted-criteria).
- [MR !324] [Set ACMG criterion as unweighted](#acmg-add-other-and-unweighted-criteria).
- [MR !325] Increased number of retrieved reference search results. 
- [MR !326] Fixed bug causing no alerts when navigating away from interpretation view with unsaved work.
- [MR !327] [Added gene filter to filter out (or rescue) variants in specific genes](#filter-improvements-gene-and-allele-ratio) [**TODO**: Update Concepts].
- [MR !331] [Added possibility to use allele ratio in quality filter](#filter-improvements-gene-and-allele-ratio)
