# Concepts


(Describe how the workflow works with interpretation rounds etc...)

E||a's purpose is to help the users classify variants. The users will either
classify a **single variant** or several variants belonging togehther in an analysis.
An **analysis** is the set of variants that are found in a patient **sample** using
a **genepanel** as variant filter. From one sample there can be multiple analyses, one for each gene panel chosen. 

Before a classification is official it must be reviewed by at least one other person.
An official classification will be available when the same variant is found later.

## Workflow
E||a uses the concept **workflow** to guide the users through the classification process.

A workflow is a multi-step process where a user interpret the variant using the information presented by the tool or that is found
outside and then entered into the tool. After the interpretation the user marks the workflow to be ready for review.
 Another user continues the interpretation and can either mark it for review again or finalize it, the latter meaning the variant(s)
  get an official assessment/classification. Each 'review' or 'finalize' is called a **round**. When a workflow is finished
  there could have been many rounds, all available later if one needs to audit the work done in each round. 

The workflow for single variants and analyses are slightly different.

## Single variant
*Allele workflow*
Before an interpretation can be finalized, the variant must be given a classification (1-5).

## Analysis (multiple variants)
*Analysis workflow*
All variants in the analysis must be given a classification before the interpretation is finalized.
Variants that are initially filtered out can be manually included by the user. These variants must
also classified.

# A typical analysis interpretation
 A user selects an analysis and goes through each variant giving them a classification using
  the information made available in the tool. The user can select or enter information like:
  - picking or uploading references and highlighting important or relevant information from them
  - ACMG codes
  - free text
  - attachments (like images)
 
 The analysis is then set to review and another user will either continue the interpretation
  (like adding info, changing classification) of finalizing the analysis.
  
 So the interpretation goes through multiple review rounds before being finalized (see figure):
 
  [Initial round] ---review--> [second round] --review--> [third round] ..... [...] --finalize--> [last round]
  
 
# Interpretation rounds and history
When later opening an analysis, all the rounds of the analysis are available read-only. Any round can be selected
 and the information displayed and entered by the user at that particular round is displayed.
 
Also interpretation of single variant will build an increasing list of rounds. 
   
  
# Reopening an analysis
A finalized variant/analysis can be reopened for further interpretation, thus increasing the list of rounds.
  
     
# Interpretation snapshots
When a variant or analysis is finalized we record several pieces of info in the database:
- classification made by user
- the assessment made by user
- the report made by user
- the annotation/custom annotation that was the foundation what was shown
- the assessment (if any) that already existed and was displayed to user
- the report (if any) that already existed and was displayed to user 

 This enables an audit feature where the tool can show info that was available at the instance a classification was done.
 Otherwise the tool could only display the latest info/most recent info about a variant.



