# -*- coding: utf-8 -*-

acmgconfig: dict[str, dict] = {
    "formatting": {
        "operators": {
            "$in": "=",
            "$gt": ">",
            "$lt": "<",
            "$not": "!=",
            "$range": "within",
            "$all": "=",
            "$at_least": "at least",
        }
    },
    "codes": {
        "pathogenic": [
            "PVS",
            "PS",
            "PM",
            "PP",
            "PNW",  # Not ACMG: Added for ability to have criteria without weight
        ],  # Codes starting with entries will be grouped as pathogenic. Also defines sort order.
        "benign": [
            "BNW",  # Not ACMG: Added for ability to have criteria without weight
            "BP",
            "BS",
            "BA",
        ],
        "other": ["OTHER"],
    },
}

acmgconfig["explanation"] = {
    ### REQ_GP
    "REQ_GP_AD": {
        "short_criteria": "AD",
        "sources": [],
        "criteria": "Autosomal dominant inheritance",
    },
    "REQ_GP_AR": {
        "short_criteria": "AR",
        "sources": [],
        "criteria": "Autosomal recessive inheritance",
    },
    "REQ_GP_last_exon_important": {
        "short_criteria": "Last exon important",
        "sources": [],
        "criteria": "The last exon of this gene is important",
    },
    "REQ_GP_last_exon_not_important": {
        "short_criteria": "Last exon not important",
        "sources": [],
        "criteria": "The last exon of this gene is not important",
    },
    "REQ_GP_LOF_missense": {
        "short_criteria": "LOF and missense = disease",
        "sources": [],
        "criteria": "Both loss of function and missense variants cause disease in this gene",
    },
    "REQ_GP_LOF_only": {
        "short_criteria": "Only LOF = disease",
        "sources": [],
        "criteria": "Only loss of function variants cause disease in this gene",
    },
    "REQ_GP_missense_common": {
        "short_criteria": "Missense variation common",
        "sources": [],
        "criteria": "Benign missense variation is common in this gene",
    },
    "REQ_GP_missense_uncommon": {
        "short_criteria": "Missense variation uncommon",
        "sources": [],
        "criteria": "Benign missense variation is uncommon in this gene",
    },
    "REQ_GP_missense_only": {
        "short_criteria": "Only missense = disease",
        "sources": [],
        "criteria": "Only missense variants cause disease in this gene",
    },
    "REQ_GP_XD": {
        "short_criteria": "XD",
        "sources": [],
        "criteria": "X-linked dominant inheritance",
    },
    "REQ_GP_XR": {
        "short_criteria": "XR",
        "sources": [],
        "criteria": "X-linked recessive inheritance",
    },
    ### REQ
    "REQ_>=4affected": {
        "short_criteria": "In >=4 unrelated patients",
        "sources": ["PS4"],
        "criteria": "Observed in four or more unrelated patients and not in controls",
    },
    "REQ_2affected": {
        "short_criteria": "In 2 unrelated patients",
        "sources": ["PPxPS4"],
        "criteria": "Observed in two unrelated patients and not in controls",
    },
    "REQ_3affected": {
        "short_criteria": "In 3 unrelated patients",
        "sources": ["PMxPS4"],
        "criteria": "Observed in three unrelated patients and not in controls",
    },
    "REQ_aa_different": {
        "short_criteria": "Not = reported aa properties",
        "sources": ["PPxPM5"],
        "criteria": "The resulting amino acid has different properties from that reported",
    },
    "REQ_aa_similar": {
        "short_criteria": "= reported aa properties",
        "sources": ["PM5"],
        "criteria": "The resulting amino acid has similar properties to that reported",
    },
    "REQ_abnormal_protein": {
        "short_criteria": "Functional protein damage",
        "sources": ["PS3", "PMxPS3"],
        "criteria": "Well-established in vitro or in vivo functional studies are supportive of a damaging effect on the gene or gene product",
    },
    "REQ_abnormal_RNA": {
        "short_criteria": "Functional RNA damage",
        "sources": ["PS3", "PMxPS3"],
        "criteria": "Well-established in vitro or in vivo functional studies are supportive of a damaging effect on the gene or gene product",
    },
    "REQ_crit_domain_hotspot": {
        "short_criteria": "Critical domain or hotspot",
        "sources": ["PM1"],
        "criteria": "Located in a mutational hot spot and/or critical and well-established functional domain (e.g., active site of an enzyme) without benign variation",
    },
    "REQ_crit_site": {
        "short_criteria": "Critical site",
        "sources": ["PSxPM1"],
        "criteria": "Located in a mutational hot spot and/or critical and well-established functional domain (e.g., active site of an enzyme) without benign variation",
    },
    "REQ_domain_no_benign": {
        "short_criteria": "No benign variation",
        "sources": ["PM1", "PSxPM1"],
        "criteria": "Located in a mutational hot spot and/or critical and well-established functional domain (e.g., active site of an enzyme) without benign variation",
    },
    "REQ_hi_freq": {
        "short_criteria": "High frequency",
        "sources": ["BA1"],
        "criteria": "Allele frequency is >=hi_freq_cutoff in this database",
    },
    "REQ_IHC_HQ": {
        "short_criteria": "Strong functional MMR evidence",
        "sources": ["PS3", "BS3"],
        "criteria": "The functional evidence is strong",
    },
    "REQ_IHC_MQ": {
        "short_criteria": "Moderate functional MMR evidence",
        "sources": ["PMxPS3"],
        "criteria": "The functional evidence is moderate",
    },
    "REQ_in_last_exon": {
        "short_criteria": "In last exon",
        "sources": ["PVS1"],
        "criteria": "The variant is in the last exon of a gene",
    },
    "REQ_in_trans_pathogenic": {
        "short_criteria": "In trans pathogenic",
        "sources": ["PM3", "BP2"],
        "criteria": "The variant is located in trans with a pathogenic variant",
    },
    "REQ_inframe": {
        "short_criteria": "In-frame/stop-loss",
        "sources": ["PM4", "BP3"],
        "criteria": "Protein length changes as a result of in-frame deletions/insertions or stop-loss variants",
    },
    "REQ_less_common": {
        "short_criteria": "Frequency >expected",
        "sources": ["BS1"],
        "criteria": "Allele frequency is greater than expected for disorder",
    },
    "REQ_missense": {
        "short_criteria": "Missense",
        "sources": ["PP2", "BP1"],
        "criteria": "Missense variant",
    },
    "REQ_MMR_loss": {
        "short_criteria": "Loss of MMR",
        "sources": ["PS3", "PMxPS3"],
        "criteria": "Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing",
    },
    "REQ_MSI": {
        "short_criteria": "MSI demonstrated",
        "sources": ["PS3", "PMxPS3"],
        "criteria": "Well-established in vitro or in vivo functional studies are supportive of a damaging effect on the gene or gene product",
    },
    "REQ_MSI_HQ": {
        "short_criteria": "Strong MSI evidence",
        "sources": ["PS3", "BS3"],
        "criteria": "The functional evidence is strong",
    },
    "REQ_MSI_MQ": {
        "short_criteria": "Moderate MSI evidence",
        "sources": ["PMxPS3", "BPxBS3"],
        "criteria": "The functional evidence is moderate",
    },
    "REQ_no_aa_change": {
        "short_criteria": "Synonymous/non-coding",
        "sources": ["BP7"],
        "criteria": "Synonymous or non-coding variant",
    },
    "REQ_no_freq": {
        "short_criteria": "Not in controls",
        "sources": ["PM2", "PPxPM2"],
        "criteria": "Absent from controls in this database",
    },
    "REQ_no_MSI": {
        "short_criteria": "MSI not demonstrated",
        "sources": ["BS3", "BPxBS3"],
        "criteria": "Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing",
    },
    "REQ_no_segregation": {
        "short_criteria": "No segregation",
        "sources": ["BS4", "BPxBS4"],
        "criteria": "Lack of segregation in affected members of a family",
    },
    "REQ_no_splice_effect": {
        "short_criteria": "No splice effect",
        "sources": ["BP7"],
        "criteria": "No splice effect predicted",
    },
    "REQ_normal_protein": {
        "short_criteria": "No functional protein damage",
        "sources": ["BS3", "BPxBS3"],
        "criteria": "Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing",
    },
    "REQ_normal_RNA": {
        "short_criteria": "No functional RNA damage",
        "sources": ["BS3", "BPxBS3"],
        "criteria": "Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing",
    },
    "REQ_non_repeat": {
        "short_criteria": "Not in repeat region",
        "sources": ["PM4"],
        "criteria": "The variant is not located in a repeat region",
    },
    "REQ_not_in_last_exon": {
        "short_criteria": "Not in last exon",
        "sources": ["PVS1"],
        "criteria": "The variant is not located in the last exon of the gene",
    },
    "REQ_novel_aa": {
        "short_criteria": "Not = reported aa change",
        "sources": ["PM5", "PPxPM5"],
        "criteria": "The amino acid change is different from that previously reported",
    },
    "REQ_null_variant": {
        "short_criteria": "Null variant",
        "sources": ["PVS1"],
        "criteria": "Null variant (nonsense, frameshift, canonical +/- 2 bp splice sites, initiation codon, single or multiexon deletion)",
    },
    "REQ_overlap_HQ": {
        "short_criteria": "Strong overlapping aa evidence",
        "sources": ["PS1", "PM5", "PPxPM5"],
        "criteria": "The evidence for reported, overlapping amino acid is strong",
    },
    "REQ_overlap_MQ": {
        "short_criteria": "Moderate overlapping aa evidence",
        "sources": ["PMxPS1", "PPxPM5"],
        "criteria": "The strength of the evidence for reported, overlapping amino acid is moderate",
    },
    "REQ_overlap_pat": {
        "short_criteria": "Pathogenic aa change",
        "sources": ["PS1", "PM5", "PPxPM5"],
        "criteria": "Changes in this amino acid position has previously been reported pathogenic",
    },
    "REQ_protein_HQ": {
        "short_criteria": "Strong functional protein evidence",
        "sources": ["PS3", "BS3"],
        "criteria": "The functional protein evidence is strong",
    },
    "REQ_protein_MQ": {
        "short_criteria": "Moderate functional protein evidence",
        "sources": ["PMxPS3", "BPxBS3"],
        "criteria": "The functional protein evidence is moderate",
    },
    "REQ_repeat": {
        "short_criteria": "In repeat region",
        "sources": ["BP3"],
        "criteria": "The variant is located in a repeat region",
    },
    "REQ_RNA_HQ": {
        "short_criteria": "Strong functional RNA evidence",
        "sources": ["PS3", "BS3"],
        "criteria": "The functional RNA evidence is strong",
    },
    "REQ_RNA_MQ": {
        "short_criteria": "Moderate functional RNA evidence",
        "sources": ["PMxPS3", "BPxBS3"],
        "criteria": "The functional RNA evidence is moderate",
    },
    "REQ_same_aa": {
        "short_criteria": "= reported aa change ",
        "sources": ["PS1"],
        "criteria": "The amino acid change is the same as that previously reported",
    },
    "REQ_segregation": {
        "short_criteria": "Cosegregation",
        "sources": ["PP1", "PMxPP1", "PSxPP1"],
        "criteria": "Cosegregation with disease in multiple affected family members in a gene definitively known to cause the disease",
    },
    "REQ_segregation_HQ": {
        "short_criteria": "Strong cosegregation evidence",
        "sources": ["PSxPP1"],
        "criteria": "The evidence for cosegregation is strong",
    },
    "REQ_segregation_MQ": {
        "short_criteria": "Moderate cosegregation evidence",
        "sources": ["PMxPP1"],
        "criteria": "The evidence for cosegregation is moderate",
    },
    "REQ_segregation_WQ": {
        "short_criteria": "Weak cosegregation evidence",
        "sources": ["PP1"],
        "criteria": "The evidence for cosegregation is weak",
    },
    ### ACMG pathogenic
    "PVS1": {
        "short_criteria": "Null variant",
        "sources": [],
        "notes": "- Caution: Genes where LOF is not a known disease mechanism (e.g. GFAP, MYH7)\n- Caution: LOF variants at the extreme 3' end of a gene\n- Caution: Splice variants that lead to exon skipping but leave remainder of protein intact\n- Caution: When there are multiple transcripts",
        "criteria": "Null variant (nonsense, frameshift, canonical +/- 2 bp splice sites, initiation codon, single or multiexon deletion) in a gene where LOF is a known mechanism of disease.\n",
    },
    "PS1": {
        "short_criteria": "Known pathogenic aa",
        "sources": [],
        "notes": "- Caution: Changes that impact splicing rather than amino acid \n- Example: Val to Leu caused by either G>C or G>T in the same codon",
        "criteria": "Same amino acid change as a previously established pathogenic variant regardless of nucleotide change",
    },
    "PS2": {
        "short_criteria": "De novo (confirmed)",
        "sources": [],
        "notes": "- Note: Confirmation of paternity only is insufficient. Egg donation, surrogate motherhood, errors in embryo transfer, and so on, can contribute to nonmaternity.",
        "criteria": "De novo (both maternity and paternity confirmed) in a patient with the disease and no family history",
    },
    "PS3": {
        "short_criteria": "Functional damage",
        "sources": [],
        "notes": "- Note: Functional studies that have been validated and shown to be reproducible and robust in a clinical diagnostic laboratory setting are considered the most well established.",
        "criteria": "Well-established in vitro or in vivo functional studies supportive of a damaging effect on the gene or gene product",
    },
    "PS4": {
        "short_criteria": "Increased prevalence in patients",
        "sources": [],
        "notes": "- Note: RR or OR >5.0 obtained from case-control studies, CI does not include 1.0\n- Note: In instances of very rare variants where case–control studies may not reach statistical significance, the prior observation of the variant in multiple unrelated patients with the same phenotype, and its absence in controls, may be used as moderate level of evidence",
        "criteria": "The prevalence of the variant in affected individuals is significantly increased compared with the prevalence in controls",
    },
    "PM1": {
        "short_criteria": "Functional domain",
        "sources": [],
        "criteria": "Located in a mutational hot spot and/or critical and well-established functional domain  (e.g., active site of an enzyme) without benign variation",
    },
    "PM2": {
        "short_criteria": "Absent from controls",
        "sources": [],
        "notes": "- Caution: Population data for insertions/deletions may be poorly called by next-generation sequencing",
        "criteria": "Absent from controls (or at extremely low frequency if recessive)",
    },
    "PM3": {
        "short_criteria": "In trans pathogenic & AR",
        "sources": [],
        "notes": "- Note: This requires testing of parents (or offspring) to determine phase.",
        "criteria": "For recessive disorders, detected in trans with a pathogenic variant.",
    },
    "PM4": {
        "short_criteria": "In-frame/stop-loss",
        "sources": [],
        "criteria": "Protein length changes as a result of in-frame deletions/insertions in a nonrepeat region or stop-loss variants.",
    },
    "PM5": {
        "short_criteria": "Novel at known pathogenic aa",
        "sources": [],
        "notes": "- Caution: Changes that impact splicing rather than amino acid. \n- Example: Arg156His is pathogenic; now you observe Arg156Cys",
        "criteria": "Novel missense change at an amino acid residue where a different missense change determined to be pathogenic has been seen before",
    },
    "PM6": {
        "short_criteria": "De novo (unconfirmed)",
        "sources": [],
        "criteria": "Assumed de novo, but without confirmation of paternity and maternity",
    },
    "PP1": {
        "short_criteria": "Cosegregation",
        "sources": [],
        "notes": "- May be used as stronger evidence with increasing segregation data",
        "criteria": "Cosegregation with disease in multiple affected family members in a gene definitively known to cause the disease",
    },
    "PP2": {
        "short_criteria": "Missense: important",
        "sources": [],
        "criteria": "Missense variant in a gene that has a low rate of benign missense variation and in which missense variants are a common mechanism of disease.",
    },
    "PP3": {
        "short_criteria": "Predicted pathogenic",
        "sources": [],
        "notes": "- Caution: Because many algorithms use the same or very similar input for their predictions, each algorithm cannot be counted as an independent criterion. PP3 can be used only once in any evaluation of a variant.",
        "criteria": "Multiple lines of computational evidence support a deleterious effect on the gene or gene product (conservation, evolutionary, splicing impact, etc.)",
    },
    "PP4": {
        "short_criteria": "Phenotype: single gene",
        "sources": [],
        "criteria": "Patient's phenotype or family history is highly specific for a disease with a single genetic etiology",
    },
    "PP5": {
        "short_criteria": "Reported pathogenic, evidence unavailable",
        "sources": [],
        "criteria": "Reputable source recently reports variant as pathogenic, but the evidence is not available to the laboratory to perform an independent evaluation",
    },
    ### ACMG benign
    "BA1": {
        "short_criteria": "High frequency",
        "sources": [],
        "criteria": "Allele frequency is >5 % in ESP, 1000G or ExAC",
    },
    "BS1": {
        "short_criteria": "Frequency >expected",
        "sources": [],
        "criteria": "Allele frequency is greater than expected for disorder",
    },
    "BS2": {
        "short_criteria": "In documented healthy",
        "sources": [],
        "criteria": "Observed in a healthy adult individual for a recessive (homozygous), dominant (heterozygous), or X-linked (hemizygous) disorder, with full penentrance expected at an early age",
    },
    "BS3": {
        "short_criteria": "No functional damage",
        "sources": [],
        "criteria": "Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing",
    },
    "BS4": {
        "short_criteria": "Non-segregation",
        "sources": [],
        "notes": "- Caution: The presence of phenocopies for common phenotypes (i.e., cancer, epilepsy) can mimic lack of segregation among affected individuals. Also, families may have more than one pathogenic variant contributing to an autosomal dominant disorder, further confounding an apparent lack of segregation.",
        "criteria": "Lack of segregation in affected members of a family",
    },
    "BP1": {
        "short_criteria": "Missense; not important",
        "sources": [],
        "criteria": "Missense variant in a gene for which primarily truncating variants are known to cause disease",
    },
    "BP2": {
        "short_criteria": "In trans & AD, or in cis pathogenic",
        "sources": [],
        "criteria": "Observed in trans with a pathogenic variant for a fully penetrant dominant gene/disorder or in cis with a pathogenic variant in any inheritance pattern",
    },
    "BP3": {
        "short_criteria": "In-frame; non-functional",
        "sources": [],
        "criteria": "In-frame insertions/delitions in a repetitive region without a known function",
    },
    "BP4": {
        "short_criteria": "Predicted benign",
        "sources": [],
        "notes": "- Caution: Because many algorithms use the same or very similar input for their predictions, each algorithm cannot be counted as an independent criterion. BP4 can be used only once in any evaluation of a variant.",
        "criteria": "Multiple lines of computational evidence suggest no impact on gene or gene product (conservation, evolutionary, splicing impact, etc.)",
    },
    "BP5": {
        "short_criteria": "Other causative variant found",
        "sources": [],
        "notes": "- Caution: patient can be a carrier of an unrelated pathogenic variant for a recessive disorder, disorders where having multiple variants can contribute to more severe disease, multigenic disorders",
        "criteria": "Variant found in a case with an alternate molecular basis for disease",
    },
    "BP6": {
        "short_criteria": "Reported benign, evidence unavailable",
        "sources": [],
        "criteria": "Reputable source recently reports variant as benign, but the evidence is not available to the laboratory to perform an independent evaluation",
    },
    "BP7": {
        "short_criteria": "Synonymous, no splice effect",
        "sources": [],
        "criteria": "A synonymous variant for which splicing prediction algorithms predict no impact to the splice consensus sequence nor the creation of a new splice site AND the nucleotide is not highly conserved",
    },
    "OTHER": {
        "short_criteria": "Non-ACMG criterion",
        "sources": [],
        "criteria": "Criterion for any other evidence not supported by ACMG criteria",
    },
}
