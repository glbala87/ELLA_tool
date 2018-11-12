# Preconfigured Gene panels

Analyses in *ella* are restricted to genes included in predefined gene panels. These must be configured separately as part of department procedures, and no configuration is done within *ella* itself. In addition to specifying which genes to analyse, the following information is currently configured:

|Setting			|Options																							 		 				|Defaults								   |
|-------------------|:-------------------------------------------------------------------------------------------------------------------------:|-----------------------------------------:|
|Inheritance\*		|Autosomal dominant (AD), autosomal recessive (AR), X-linked dominant (XD) or X-linked recessive (XR)		 				|-										   |
|Phenotypes\*		|Which disease mutations in the gene have been associated with (restricted to diseases investigated at AMG). 				|-										   |
|Frequency cutoff	|The population frequency thresholds for ACMG criterion BA1 and BS1, separate for internal/external datasets.				|External: 0.001/0.005<br>Internal: 1/0.05 |
|Disease mode		|Whether only missense (MISS) or loss of function (LOF) mutations, or both (ANY), are expected to cause disease in the gene.|ANY									   |
|Last exon			|Whether the last exon is important (LEI) or not (LENI).																	|LEI									   |
|Gene information	|Information relevant to evaluation of more/all variants in a gene.															|-										   |

\*Configured using OMIM and manual curation

The information provided in the gene panel is visible by clicking on the gene name in the [top bar of the CLASSIFACTION page](../manual/top-bar.md).