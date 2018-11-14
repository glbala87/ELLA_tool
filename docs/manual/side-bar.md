---
title: Side bar
---

# Side bar: Variant list and quick classification (ANALYSES only)

[[toc]]

The variants in your sample (ANALYSES mode) are listed in the side bar to the left:

<div style="text-indent: 4%;"><img src="./img/sidebar.png"></div>

Names (variant HGVSc and gene) and inheritance is displayed as specified by the default transcript in the gene panel. If there is more than one default transcript, all versions are shown.

## Filtered variants

Some variants have been automatically filtered from view before you start an analysis. These variants are still accessible via a button at the top of the variant list: 

<div style="text-indent: 4%;"><img src="./img/filtered_btn.png"></div>

In this particular sample, there are a total of 3407 filtered variants, and none of these have been added back manually to the analysis by the user. Pushing the button brings up a window where you may select individual variants and add them back to the analysis:

<div style="text-indent: 4%;"><img src="./img/filtered.png"></div>

The filters are configured to your user group/gene panel, but usually include, in this order:

  - FREQUENCY: Variants with a population frequency above the threshold for neutral variants (ACMG criterion BA1), predefined for the corresponding gene in the gene panel

  - REGION: UTR variants outside c.-20/c\*20, intron variants outside +6/-20, and other, custom regions defined outside the scope of analysis. Variants are not excluded if they are annotated with a “worse” consequence than UTR/intron in an alternative RefSeq NM\_ transcript for that gene.

  - QUALITY: Variants not meeting minimum quality criteria (if set).

  - SEGREGATION: Most of these filters are relevant for trio/family data only (joint called), except the last. These filters includes variants that are *not*:
    
      - De novo (family).
      - Autosomal recessive homozygous (family).
      - X-linked recessive (family).
      - Compound heterozygous (family).
	  - Single, non-filtered variant in a gene with automsomal recessive inheritance, except if loss-of-function. 

In addition, there may be other filters, depending on the configuration of your user group/gene panel. Examples: 

  - POLYPYRIMIDINE: Variants 1-2 nt in the intronic polypyrimidine tract (-20,-3) that only involve changes to/from pyrimidines (C/T)
  
  - CONSEQUENCE: Synonymous variants

## Quick classification

Instead of performing a full classification, you may instead choose to use the Quick classification mode by pressing the button at the top of the variant list: 

<div style="text-indent: 4%;"><img src="./img/quick_classification_btn.png"></div>

This feature is particularly well suited for workflows with large gene panels and many variants. The Quick classification view gives a summary of the most important information necessary for marking variants as `Technical` or `Not relevant` (see [Mark as verified/technical/not relevant](/manual/evidence-sections.html#mark-as-verified-technical-not-relevant)), or classifying as `Class U` or `Class 2` (see [Set variant class](/manual/classification-section.html#set-variant-class)), and gives you buttons to perform those actions directly:

<div style="text-indent: 4%;"><img src="./img/quick_classification.png"></div>

Clicking one of these buttons moves the variant down to the respective section in the sidebar. If applicable, add a comment in the EVALUATION column before moving to the next variant. 

When you are done, and ready to do a more thourough interpretation of any remaining variants, click the FULL CLASSIFICATION button at the top of the variant list (see also [Evidence sections](/manual/evidence-sections.html) and [Classification section](/manual/classification-section.html))

## Variant tags

If applicable, variants in the variant list are tagged with:

  - `!` [Variant warnings](/manual/top-bar.html#variant-warnings)

  - `S` Segregation. Depdending on data, changes to:
    
      - `D` De novo
      - `A` Autosomal recessive homozygous
      - `X` X-linked recessive
      - `C` Compound heterozygous

  - `O` Homozygous/hemizygous genotype

  - `Q` Quality issues (= [NEEDS VERIFICATION](/manual/evidence-sections.html#quality-information)). Depending on actions in the [QUALITY section](/manual/evidence-sections.html#quality), this tag may be replaced by:
    
      - `V` Verified (green)
      - `T` Technical (red)

  - `R` Reference available

  - Shaded background: More than one variant in the same gene (in current sample)

::: tip
Hold the mouse cursor over a tag to see the full label.
:::

## Sorting

The default sorting of this list is Inheritance – Gene – HGVSc. You can change the sorting by clicking on any of the list headers:

  - First click sorts descending (↓)
  - Second click sorts ascending (↑)
  - Third click returns to default sort

## Existing and new classifications  

Existing or newly set classes are given in the right-most column: 

<div style="text-indent: 4%;"><img src="./img/classified_variants.png"></div>

An arrow (→) indicates that a new classification will be created, and any existing class is given to the left of the arrow. If this classification is also outdated (long since last interpretation), an `*` is added to the existing class.

::: warning NOTE
Outdated variants marked with `*` in CLASSIFIED VARIANTS should be re-interpreted before you finish the analysis.
:::

## Mark as reviewed

You can toggle a blue colouring of the background of the class by clicking on it in the side bar: 

<div style="text-indent: 4%;"><img src="./img/mark_reviewed.png"></div>

This can be used to indicates which variants have been reviewed, i.e. to keep track of the work done in a review round. 
