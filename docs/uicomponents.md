# UI

## Pages / views
The views and corresponding routes are defined in index.js:
- overview of analysis and samples
- analysis interpretation
- variant interpretation
- login

## Overview
There are two overview pages, one for analysis and one for alleles/variants.
The categorization is mostly done in backend.

**Code**
- api/v1/resources/overview.py
- webui/src/js/views/overviews/analysisSelection.directive.js
- webui/src/js/views/overviews/alleleSelection.directive.js
- webui/src/js/widgets/analysisList.directive.js
- webui/src/js/widgets/alleleList.directive.js

## Analysis interpretation
Multiple alleles; details of the first is shown.
Apart from the **allele sidebar**, the rest of the page is very similar to allele interpretation.

Variants that are excluded can be manually included.

If there has been multiple interpretation rounds, each can be opened. The ones with status "Done" can only be imported read-only.

### Details on loading data
The route /analysis/:analysisId is rendered (mainly) by directives workflowAnalysis.directive.js) and interpretation.directive.js which basically:
- loads interpretations rounds
- selects a round (usually the latest)
- loads that round's alleles, ACMG codes and references.


<div style="text-align:center"><img src="img/load_analysis.png"></div>

The directives chooses the last interpretion round as the 'selected' one.
If this round is 'Done' we make a copy of it (to make sure  we don't accidently change it) and uses the copy as 'selected'.
A flag is set on the copy to indicate that we want the latest entities to be loaded for this allele (like annotations, assessments).
This allows us to choose a static interpretation page using the entities found in the snapshots or a "dynamic" interpretation using the latest entities (annotations, assessments etc). Both have the same state, showing the same classification, comments etc.

**Code related to static/dynamic interpretations pages**
- WorkflowAlleleController.reloadInterpretationData
- WorkflowAnalysisController.reloadInterpretationData


**Code:**
- api.util.interpretationdataloader.InterpretationDataLoader
- api.v1.resources.workflow.analysis.AnalysisInterpretationAllelesListResource
- api.v1.resources.workflow.analysis.AnalysisInterpretationResource
- api.util.allelefilter.AlleleFilter
- api/schemas
- webui/src/js/views/workflow/workflowAnalysis.directive.js
- webui/src/js/views/workflow/interpretation.directive.j
- webui/src/js/views/alleleSidebar.directive.js

## Allele interpretation
Only a single allele is displayed. The various interpretation rounds are not accessible in the UI.

Loading a single allele similar but simpler:
- load allele data (variant, annotation): /alleles/?q=[genepanel, chr, position, ..]
- load genepanel (phenotypes, transcript, config): /genepanels/NAME/VERSION/
- find ACMG codes: /acmg/alleles/ (POST)
- load interpretation rounds: /workflows/alleles/576/interpretations/
- find references

Note that interpreation rounds are not needed to load allele data.


**Code*
- api/schemas
- webui/src/js/views/workflow/workflowAllele.directive.js
- webui/src/js/views/workflow/interpretation.directive.j