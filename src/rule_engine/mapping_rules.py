# coding=utf-8
rules = [
    #### JSON rules (copy/paste entire column between [] in "rules = []", remove last ",")
    ### GP_REQ
    { "code": "REQ_GP_AD", "rule": {"genepanel.inheritance": "AD"}},
    { "code": "REQ_GP_AR", "rule": {"genepanel.inheritance": "AR"}},
    { "code": "REQ_GP_XD", "rule": {"genepanel.inheritance": "XD"}},
    { "code": "REQ_GP_XR", "rule": {"genepanel.inheritance": "XR"}},
    { "code": "REQ_GP_last_exon_important", "rule": {"genepanel.last_exon_important": "LEI"}},
    { "code": "REQ_GP_last_exon_not_important", "rule": {"genepanel.last_exon_important": "LENI"}},
    { "code": "REQ_GP_LOF_missense", "rule": {"genepanel.disease_mode": "ANY"}},
    { "code": "REQ_GP_missense_common", "rule": {"genepanel.disease_mode": "MISSCOMM"}},
    { "code": "REQ_GP_missense_uncommon", "rule": {"genepanel.disease_mode": "MISSUNC"}},
    { "code": "REQ_GP_LOF_only", "rule": {"genepanel.disease_mode": "LOF"}},
    { "code": "REQ_GP_missense_only", "rule": {"genepanel.disease_mode": "MISS"}},
    ### REQ
    { "code": "REQ_>=4affected", "rule": {"refassessment.*.ref_population_affecteds": "in_many_aff"}},
    { "code": "REQ_2affected", "rule": {"refassessment.*.ref_population_affecteds": "in_few_aff"}},
    { "code": "REQ_3affected", "rule": {"refassessment.*.ref_population_affecteds": "in_more_aff"}},
    { "code": "REQ_aa_different", "rule": {"refassessment.*.ref_aa_overlap_sim": "diff_prop"}},
    { "code": "REQ_aa_similar", "rule": {"refassessment.*.ref_aa_overlap_sim": "sim_prop"}},
    { "code": "REQ_abnormal_protein", "rule": {"refassessment.*.ref_prot": "prot_abnormal"}},
    { "code": "REQ_abnormal_RNA", "rule": {"refassessment.*.ref_rna": "rna_abnormal"}},
    { "code": "REQ_crit_domain_hotspot", "rule": {"refassessment.*.ref_domain_overlap": {"$in": ["crit_domain", "mut_hotpot"]}}},
    { "code": "REQ_crit_site", "rule": {"refassessment.*.ref_domain_overlap": "crit_site"}},
    { "code": "REQ_domain_no_benign", "rule": {"refassessment.*.ref_domain_benign": "no_benign_variation"}},
    { "code": "REQ_hi_freq", "rule": {"frequencies.commonness": "common"}},
    { "code": "REQ_IHC_HQ", "rule": {"refassessment.*.ref_ihc_quality": "ihc_HQ"}},
    { "code": "REQ_IHC_MQ", "rule": {"refassessment.*.ref_ihc_quality": "ihc_MQ"}},
    { "code": "REQ_in_last_exon", "rule": {"transcript.in_last_exon": "yes"}},
    { "code": "REQ_in_trans_pathogenic", "rule": {"refassessment.*.ref_phase": "in_trans_pathogenic"}},
    { "code": "REQ_in_trans_pathogenic", "rule": {"genomic.phase": "in_trans_pathogenic"}},
    { "code": "REQ_inframe", "rule": {"transcript.consequences": {"$in": ["inframe_insertion", "inframe_deletion"]}}},
    { "code": "REQ_less_common", "rule": {"frequencies.commonness": "less_common"}},
    { "code": "REQ_missense", "rule": {"transcript.consequences": {"$in": ["missense_variant", "protein_altering_variant"]}}},
    { "code": "REQ_MMR_loss", "rule": {"refassessment.*.ref_ihc": "mmr_loss"}},
    { "code": "REQ_MSI", "rule": {"refassessment.*.ref_msi": "msi"}},
    { "code": "REQ_MSI_HQ", "rule": {"refassessment.*.ref_msi_quality": "msi_HQ"}},
    { "code": "REQ_MSI_MQ", "rule": {"refassessment.*.ref_msi_quality": "msi_MQ"}},
    { "code": "REQ_no_aa_change", "rule": {"transcript.consequences": {"$in": ["stop_retained_variant", "synonymous_variant"]}}},
    { "code": "REQ_no_MSI", "rule": {"refassessment.*.ref_msi": "no_msi"}},
    { "code": "REQ_no_segregation", "rule": {"refassessment.*.ref_segregation": "no_segr"}},
    # Manual edit
    { "code": "REQ_no_splice_effect", "rule": {"$or": [{"prediction.splice_Effect": {"$in": ["predicted_conserved", "consensus_not_affected", "not_transcribed"]}},{"prediction.splice_Effect": {"$not": {"$in": ["de_novo"]}}}]}},
    # Manual edit
    { "code": "REQ_no_splice_effect", "rule": {"$or": [{"prediction.splice_Effect_manual": {"$in": ["predicted_conserved", "consensus_not_affected", "not_transcribed"]}},{"prediction.splice_Effect_manual": {"$not": {"$in": ["de_novo"]}}}]}},
    { "code": "REQ_normal_protein", "rule": {"refassessment.*.ref_prot": "prot_normal"}},
    { "code": "REQ_normal_RNA", "rule": {"refassessment.*.ref_rna": "rna_normal"}},
    { "code": "REQ_not_in_last_exon", "rule": {"transcript.in_last_exon": "no"}},
    { "code": "REQ_novel_aa", "rule": {"refassessment.*.ref_aa_overlap_same_novel": "novel_aa"}},
    { "code": "REQ_null_variant", "rule": {"transcript.consequences": {"$in": ["start_lost", "initiator_codon_variant", "transcript_ablation", "splice_donor_variant", "splice_acceptor_variant", "stop_gained", "frameshift_variant"]}}},
    { "code": "REQ_no_freq", "rule": {"frequencies.commonness": "null_freq"}},
    { "code": "REQ_non_repeat", "rule": {"prediction.domain": "non_repeat"}},
    { "code": "REQ_overlap_HQ", "rule": {"refassessment.*.ref_aa_overlap_quality": "overlap_HQ"}},
    { "code": "REQ_overlap_MQ", "rule": {"refassessment.*.ref_aa_overlap_quality": "overlap_MQ"}},
    { "code": "REQ_overlap_pat", "rule": {"refassessment.*.ref_aa_overlap": "overlap_pat"}},
    { "code": "REQ_protein_HQ", "rule": {"refassessment.*.ref_prot_quality": "prot_HQ"}},
    { "code": "REQ_protein_MQ", "rule": {"refassessment.*.ref_prot_quality": "prot_MQ"}},
    { "code": "REQ_repeat", "rule": {"refassessment.*.ref_repeat_overlap": "repeat"}},
    { "code": "REQ_repeat", "rule": {"prediction.domain": "repeat"}},
    { "code": "REQ_RNA_HQ", "rule": {"refassessment.*.ref_rna_quality": "rna_HQ"}},
    { "code": "REQ_RNA_MQ", "rule": {"refassessment.*.ref_rna_quality": "rna_MQ"}},
    { "code": "REQ_same_aa", "rule": {"refassessment.*.ref_aa_overlap_same_novel": "same_aa"}},
    { "code": "REQ_segregation", "rule": {"refassessment.*.ref_segregation": "segr"}},
    { "code": "REQ_segregation_HQ", "rule": {"refassessment.*.ref_segregation_quality": "segr_HQ"}},
    { "code": "REQ_segregation_MQ", "rule": {"refassessment.*.ref_segregation_quality": "segr_MQ"}},
    { "code": "REQ_segregation_WQ", "rule": {"refassessment.*.ref_segregation_quality": "segr_WQ"}},
    ### PVS*
    # Manual edit
    { "code": "PVS1","rule": {"$$aggregate": {"$and":["REQ_null_variant",{"$in": ["REQ_GP_LOF_missense", "REQ_GP_LOF_only"]},{"$or": ["REQ_not_in_last_exon",{"$all": ["REQ_in_last_exon","REQ_GP_last_exon_important"]}]}]}}},
    ### PS*
    { "code": "PS1", "rule": {"$$aggregate": {"$all": ["REQ_overlap_pat", "REQ_same_aa", "REQ_overlap_HQ"]}}},
    { "code": "PS2", "rule": {"refassessment.*.ref_de_novo": "de_novo_confirmed"}},
    { "code": "PS2", "rule": {"family.de_novo": "de_novo_confirmed"}},
    { "code": "PS3", "rule": {"$$aggregate": {"$all": ["REQ_abnormal_protein", "REQ_protein_HQ"]}}},
    { "code": "PS3", "rule": {"$$aggregate": {"$all": ["REQ_abnormal_RNA", "REQ_RNA_HQ"]}}},
    { "code": "PS3", "rule": {"$$aggregate": {"$all": ["REQ_MSI", "REQ_MSI_HQ"]}}},
    { "code": "PS3", "rule": {"$$aggregate": {"$all": ["REQ_MMR_loss", "REQ_IHC_HQ"]}}},
    { "code": "PS4", "rule": {"$$aggregate": {"$all": ["REQ_>=4affected", "REQ_no_freq"]}}},
    { "code": "PSxPM1", "rule": {"$$aggregate": {"$all": ["REQ_crit_site", "REQ_domain_no_benign"]}}},
    { "code": "PSxPM1", "rule": {"prediction.domain": "crit_site"}},
    { "code": "PSxPP1", "rule": {"$$aggregate": {"$all": ["REQ_segregation", "REQ_segregation_HQ"]}}},
    ### PM*
    { "code": "PM1", "rule": {"prediction.domain": "crit_domain"}},
    { "code": "PM1", "rule": {"$$aggregate": {"$all": ["REQ_crit_domain_hotspot", "REQ_domain_no_benign"]}}},
    # PM2 (no rule)
    { "code": "PM3", "rule": {"$$aggregate": {"$all": ["REQ_in_trans_pathogenic", "REQ_GP_AR"]}}},
    { "code": "PM4", "rule": {"transcript.consequences": "stop_lost"}},
    # Manual edit
    { "code": "PM4", "rule": {"$$aggregate": {"$all": ["REQ_inframe", "REQ_non_repeat"]}}},
    { "code": "PM5", "rule": {"$$aggregate": {"$all": ["REQ_overlap_pat", "REQ_novel_aa", "REQ_aa_similar", "REQ_overlap_HQ"]}}},
    { "code": "PM6", "rule": {"refassessment.*.ref_de_novo": "de_novo_unconfirmed"}},
    { "code": "PM6", "rule": {"family.de_novo": "de_novo_unconfirmed"}},
    { "code": "PMxPP1", "rule": {"$$aggregate": {"$all": ["REQ_segregation", "REQ_segregation_MQ"]}}},
    { "code": "PMxPS1", "rule": {"$$aggregate": {"$all": ["REQ_overlap_pat", "REQ_same_aa", "REQ_overlap_MQ"]}}},
    { "code": "PMxPS3", "rule": {"$$aggregate": {"$all": ["REQ_abnormal_protein", "REQ_protein_MQ"]}}},
    { "code": "PMxPS3", "rule": {"$$aggregate": {"$all": ["REQ_abnormal_RNA", "REQ_RNA_MQ"]}}},
    { "code": "PMxPS3", "rule": {"$$aggregate": {"$all": ["REQ_MSI", "REQ_MSI_MQ"]}}},
    { "code": "PMxPS3", "rule": {"$$aggregate": {"$all": ["REQ_MMR_loss", "REQ_IHC_MQ"]}}},
    { "code": "PMxPS4", "rule": {"$$aggregate": {"$all": ["REQ_3affected", "REQ_no_freq"]}}},
    ### PP*
    { "code": "PP1", "rule": {"$$aggregate": {"$all": ["REQ_segregation", "REQ_segregation_WQ"]}}},
    # Manual edit
    { "code": "PP2","rule": {"$$aggregate": {"$and": [{"$all": ["REQ_missense", "REQ_GP_missense_uncommon"]}, {"$in": ["REQ_GP_LOF_missense","REQ_GP_missense_only"]}]}}},
    { "code": "PP3", "rule": {"transcript.splice_Effect": {"$in": ["predicted_lost", "de_novo"]}}},
    { "code": "PP3", "rule": {"prediction.splice_Effect_manual": {"$in": ["predicted_lost", "de_novo"]}}},
    { "code": "PP3", "rule": {"prediction.orth_conservation": "conserved"}},
    { "code": "PP3", "rule": {"prediction.para_conservation": "conserved"}},
    # PP4 (no rule)
    { "code": "PP5", "rule": {"external.[Trusted source]": "Pathogenic"}},
    # Manual edit
    { "code": "PPxPM2", "rule": {"$$aggregate": {"$and": ["REQ_no_freq", {"$not": {"$in": ["REQ_less_common","REQ_hi_freq"]}}]}}},
    { "code": "PPxPM5", "rule": {"$$aggregate": {"$or": [{"$all": ["REQ_overlap_pat", "REQ_novel_aa", "REQ_aa_similar", "REQ_overlap_MQ"]}, {"$all": ["REQ_overlap_pat", "REQ_novel_aa", "REQ_aa_different", "REQ_overlap_HQ"]}]}}},
    { "code": "PPxPS4", "rule": {"$$aggregate": {"$all": ["REQ_2affected", "REQ_no_freq"]}}},
    ### BA*
    { "code": "BA1", "rule": {"frequencies.commonness": "common"}},
    ### BS*
    { "code": "BS1", "rule": {"$$aggregate": {"$all": ["REQ_less_common", "REQ_GP_AD"]}}},
    { "code": "BS2", "rule": {"refassessment.*.ref_population_healthy": "in_healthy"}},
    { "code": "BS3", "rule": {"$$aggregate": {"$all": ["REQ_normal_protein", "REQ_protein_HQ"]}}},
    { "code": "BS3", "rule": {"$$aggregate": {"$all": ["REQ_normal_RNA", "REQ_RNA_HQ"]}}},
    { "code": "BS3", "rule": {"$$aggregate": {"$all": ["REQ_no_MSI", "REQ_MSI_HQ"]}}},
    { "code": "BS3", "rule": {"$$aggregate": {"$all": ["REQ_MMR_loss", "REQ_IHC_HQ"]}}},
    { "code": "BS4", "rule": {"$$aggregate": {"$all": ["REQ_no_segregation", "REQ_segregation_HQ"]}}},
    { "code": "BSxBP7", "rule": {"$$aggregate": {"$all": ["REQ_no_aa_change", "REQ_no_splice_effect"]}}},
    ### BP*
    { "code": "BP1", "rule": {"$$aggregate": {"$all": ["REQ_missense", "REQ_GP_LOF_only"]}}},
    { "code": "BP2", "rule": {"refassessment.*.ref_phase": "in_cis_pathogenic"}},
    { "code": "BP2", "rule": {"family.phase": "in_cis_pathogenic"}},
    { "code": "BP2", "rule": {"$$aggregate": {"$all": ["REQ_in_trans_pathogenic", "REQ_GP_AD"]}}},
    { "code": "BP3", "rule": {"$$aggregate": {"$all": ["REQ_inframe", "REQ_repeat"]}}},
    # Manual edit
    { "code": "BP4", "rule": {"transcript.splice_Effect": {"$or": [{"$in": ["predicted_conserved", "consensus_not_affected", "not_transcribed"]}, {"$not": {"$in": ["de_novo"]}}]}}},
    { "code": "BP4", "rule": {"prediction.splice_Effect_manual": {"$or": [{"$in": ["predicted_conserved", "consensus_not_affected", "not_transcribed"]}, {"$not": {"$in": ["de_novo"]}}]}}},
    { "code": "BP4", "rule": {"prediction.orth_conservation": "non-conserved"}},
    { "code": "BP4", "rule": {"prediction.para_conservation": "non-conserved"}},
    # BP5 (no rule)
    { "code": "BP6", "rule": {"external.[Trusted source]": "Benign"}},
    # BP7 (no rule)
    { "code": "BPxBS3", "rule": {"$$aggregate": {"$all": ["REQ_normal_protein", "REQ_protein_MQ"]}}},
    { "code": "BPxBS3", "rule": {"$$aggregate": {"$all": ["REQ_normal_RNA", "REQ_RNA_MQ"]}}},
    { "code": "BPxBS3", "rule": {"$$aggregate": {"$all": ["REQ_no_MSI", "REQ_MSI_MQ"]}}},
    { "code": "BPxBS4", "rule": {"$$aggregate": {"$all": ["REQ_no_segregation", "REQ_segregation_MQ"]}}}




#    {
#        "code": "XXX",
#        "rule": {"$$aggregate": {"$atleast": [1, "REQ-1", "REQ-2", "REQ-3"]}}
#    },

]
