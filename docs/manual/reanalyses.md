---
title: Reanalyses
---

# Reanalyses and custom gene panels 

[[toc]]

By default, *ella* uses predefined gene panels for all samples. However, you may create a new analysis of a previously run HTS sample (for which a larger set of genes was sequenced) using the IMPORT function available in the vertical sidebar:

<div style="text-indent: 4%;"><img src="./img/overview_sidebar.png"></div>

In the IMPORT ANALYSIS section, start typing the analysis ID in the SAMPLE box and select from the results.

## Use existing gene panel

If you use the default `NO` for CUSTOM GENEPANEL, only existing (standard) gene panels are shown:

<div style="text-indent: 4%;"><img src="./img/reanalysis_existing.png"></div>

  - Select the desired gene panel from the GENEPANEL list (<span style="color:red">1</span>).

  - Once you are satisfied with the selection displayed in the “Summary” at the bottom, click the 
  `+ IMPORT` button (<span style="color:red">2</span>) to import.

## Use custom gene panel

If you choose YES for CUSTOM GENEPANEL, you may add any combination of genes from existing gene panels:

<div style="text-indent: 4%;"><img src="./img/reanalysis_custom.png"></div>

  - Add a name in the CUSTOM GENEPANEL NAME field (<span style="color:red">1</span>) (max 12 characters, do not use the same name more than once per day to ensure a unique name)

  - Add genes by selecting an existing gene panel (<span style="color:red">2</span>) under ADD TRANSCRIPTS, then click
    
      - `ADD ALL` (<span style="color:red">3</span>) to add all genes in the selected gene panel, or
      - `ADD` (<span style="color:red">4</span>; next to a gene) to add that particular gene only. Start typing a gene name in the FILTER box (<span style="color:red">5</span>) to quickly locate a gene in the list. Genes that have already been added are greyed out.

  - Repeat the above if you need to choose from more than one existing gene panel. 

  - Once you are satisfied with the selection displayed in the ADDED list at the bottom (<span style="color:red">6</span>), click the `+ IMPORT` button to import.
