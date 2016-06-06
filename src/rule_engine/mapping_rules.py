# coding=utf-8
rules = [
    #### JSON rules (copy/paste entire column between [] in "rules = []", remove last ",")
    ### GP_REQ
    { "code": "REQ_GP_inh_ad", "rule": {"genepanel.gp_inheritance": "autosomal_dominant"}},
    { "code": "REQ_GP_inh_ar", "rule": {"genepanel.gp_inheritance": "autosomal_recessive"}},
    { "code": "REQ_GP_inh_xd", "rule": {"genepanel.gp_inheritance": "x-linked_dominant"}},
    { "code": "REQ_GP_inh_xr", "rule": {"genepanel.gp_inheritance": "x-linked_recessive"}},
    { "code": "REQ_GP_last_exon_important", "rule": {"genepanel.gp_last_exon": "last_exon_important"}},
    { "code": "REQ_GP_last_exon_not_important", "rule": {"genepanel.gp_last_exon": "last_exon_not_important"}},
    { "code": "REQ_GP_lof_missense", "rule": {"genepanel.gp_disease_mode": "lof_missense"}},
    { "code": "REQ_GP_lof_only", "rule": {"genepanel.gp_disease_mode": "lof_only"}},
    { "code": "REQ_GP_missense_only", "rule": {"genepanel.gp_disease_mode": "missense_only"}},
    ### REQ
    { "code": "REQ_aa_diff", "rule": {"refassessment.*.ref_aa_overlap_sim": "diff_prop"}},
    { "code": "REQ_aa_sim", "rule": {"refassessment.*.ref_aa_overlap_sim": "sim_prop"}},
    { "code": "REQ_hi_freq", "rule": {"frequencies.ExAC_cutoff": "≥hi_freq_cutoff"}},
    { "code": "REQ_hi_freq", "rule": {"frequencies.1000G_cutoff": "≥hi_freq_cutoff"}},
    { "code": "REQ_hi_freq", "rule": {"frequencies.ESP6500_cutoff": "≥hi_freq_cutoff"}},
    { "code": "REQ_hi_freq", "rule": {"frequencies.inDB_cutoff": "≥hi_freq_cutoff"}},
    { "code": "REQ_in_autozygous", "rule": {"genomic.autozygosity": "in_autozygous"}},
    { "code": "REQ_in_last_exon", "rule": {"transcript.in_last_exon": "yes"}},
    { "code": "REQ_in_trans_pathogenic", "rule": {"genomic.phase": "in_trans_pathogenic"}},
    { "code": "REQ_inframe", "rule": {"transcript.Consequence": {"$in": ["inframe_insertion", "inframe_deletion"]}}},
    { "code": "REQ_less_common", "rule": {"frequencies.ExAC_cutoff": {"$all": ["≥lo_freq_cutoff", "<hi_freq_cutoff"]}}},
    { "code": "REQ_less_common", "rule": {"frequencies.1000G_cutoff": {"$all": ["≥lo_freq_cutoff", "<hi_freq_cutoff"]}}},
    { "code": "REQ_less_common", "rule": {"frequencies.ESP6500_cutoff": {"$all": ["≥lo_freq_cutoff", "<hi_freq_cutoff"]}}},
    { "code": "REQ_less_common", "rule": {"frequencies.inDB_cutoff": {"$all": ["≥lo_freq_cutoff", "<hi_freq_cutoff"]}}},
    { "code": "REQ_missense", "rule": {"transcript.Consequence": {"$in": ["missense_variant", "protein_altering_variant"]}}},
    { "code": "REQ_no_aa_change", "rule": {"transcript.Consequence": {"$in": ["stop_retained_variant", "5_prime_UTR_variant", "3_prime_UTR_variant", "non_coding_transcript_exon_variant", "non_coding_transcript_variant", "intron_variant", "upstream_gene_variant", "downstream_gene_variant", "intergenic_variant", "synonymous_variant"]}}},
    # Manual edit
    { "code": "REQ_no_splice_effect", "rule": {"transcript.splice_Effect": {"$or": [{"$in": ["predicted_conserved", "consensus_not_affected", "not_transcribed"]}, {"$not": {"$in": ["de_novo"]}}]}}},
    { "code": "REQ_non-conserved", "rule": {"genomic.conservation": "non-conserved"}},
    { "code": "REQ_non-repeat", "rule": {"transcript.domain": "non-repeat"}},
    { "code": "REQ_not_in_last_exon", "rule": {"transcript.in_last_exon": "no"}},
    { "code": "REQ_novel_aa", "rule": {"refassessment.*.ref_aa_overlap_same_novel": "novel_aa"}},
    { "code": "REQ_null", "rule": {"transcript.Consequence": {"$in": ["start_lost", "initiator_codon_variant", "transcript_ablation", "splice_donor_variant", "splice_acceptor_variant", "stop_gained", "frameshift_variant"]}}},
    { "code": "REQ_null_freq", "rule": {"frequencies.ExAC_cutoff": "null_freq"}},
    { "code": "REQ_null_freq", "rule": {"frequencies.1000G_cutoff": "null_freq"}},
    { "code": "REQ_null_freq", "rule": {"frequencies.ESP6500_cutoff": "null_freq"}},
    { "code": "REQ_null_freq", "rule": {"frequencies.inDB_cutoff": "null_freq"}},
    { "code": "REQ_overlap_ben", "rule": {"refassessment.*.ref_aa_overlap": "overlap_ben"}},
    { "code": "REQ_overlap_pat", "rule": {"refassessment.*.ref_aa_overlap": "overlap_pat"}},
    { "code": "REQ_repeat", "rule": {"refassessment.*.ref_repeat_overlap": "repeat"}},
    { "code": "REQ_repeat", "rule": {"genomic.domain": "repeat"}},
    { "code": "REQ_same_aa", "rule": {"refassessment.*.ref_aa_overlap_same_novel": "same_aa"}},
    ### PVS*
    # Manual edit
    { "code": "PVS1","rule": {"$$aggregate": {"$and":["REQ_null",{"$in": ["REQ_GP_lof_missense", "REQ_GP_lof_only"]},{"$or": ["REQ_not_in_last_exon",{"$all": ["REQ_in_last_exon","REQ_GP_last_exon_important"]}]}]}}},
    ### PS*
    { "code": "PS1", "rule": {"$$aggregate": {"$all": ["REQ_overlap_pat", "REQ_same_aa"]}}},
    { "code": "PS2", "rule": {"family.de_novo": "de_novo_confirmed"}},
    { "code": "PS3", "rule": {"refassessment.*.ref_prot": "prot++"}},
    { "code": "PS3", "rule": {"refassessment.*.ref_rna": "rna++"}},
    { "code": "PS3", "rule": {"refassessment.*.ref_msi": "msi++"}},
    { "code": "PS3", "rule": {"refassessment.*.ref_ihc": "mmr_loss++"}},
    { "code": "PS4", "rule": {"refassessment.*.ref_population": "rr_5"}},
    { "code": "PSxPP1", "rule": {"refassessment.*.ref_segregation": "segr+++"}},
    { "code": "PSxPP1", "rule": {"family.segregation": "segr+++"}},
    ### PM*
    { "code": "PM1", "rule": {"refassessment.*.ref_domain_overlap": "crit_domain"}},
    { "code": "PM1", "rule": {"transcript.domain": "crit_domain"}},
    # PM2 (not implemented)
    { "code": "PM3", "rule": {"$$aggregate": {"$all": ["REQ_in_trans_pathogenic", "REQ_GP_inh_ar"]}}},
    { "code": "PM4", "rule": {"transcript.Consequence": "stop_lost"}},
    { "code": "PM4", "rule": {"$$aggregate": {"$all": ["REQ_inframe", "REQ_non-repeat"]}}},
    { "code": "PM5", "rule": {"$$aggregate": {"$all": ["REQ_overlap_pat", "REQ_novel_aa", "REQ_aa_sim"]}}},
    { "code": "PM6", "rule": {"family.de_novo": "de_novo_unconfirmed"}},
    { "code": "PMxN1", "rule": {"$$aggregate": {"$all": ["REQ_in_autozygous", "REQ_GP_inh_ar"]}}},
    { "code": "PMxPP1", "rule": {"refassessment.*.ref_segregation": "segr++"}},
    { "code": "PMxPP1", "rule": {"family.segregation": "segr++"}},
    { "code": "PMxPS3", "rule": {"refassessment.*.ref_prot": "prot+"}},
    { "code": "PMxPS3", "rule": {"refassessment.*.ref_rna": "rna+"}},
    { "code": "PMxPS3", "rule": {"refassessment.*.ref_msi": "msi+"}},
    { "code": "PMxPS3", "rule": {"refassessment.*.ref_mmr": "mmr_loss+"}},
    { "code": "PMxPS4", "rule": {"refassessment.*.ref_population": "in_affecteds"}},
    ### PP*
    { "code": "PP1", "rule": {"refassessment.*.ref_segregation": "segr+"}},
    { "code": "PP1", "rule": {"family.segregation": "segr+"}},
    # Manual edit
    # This rule *must* be placed after rules for PS1 and PM5
    { "code": "PP2","rule": {"$$aggregate": {"$and":["REQ_missense",{"$in": ["REQ_GP_lof_missense","REQ_GP_missense_only"]},{"$not": {"$in": ["PS1","PM5"]}}]}}},
    { "code": "PP3", "rule": {"transcript.splice_Effect": {"$in": ["predicted_lost ", "de_novo"]}}},
    { "code": "PP3", "rule": {"genomic.conservation": "conserved"}},
    # PP4 (not implemented)
    { "code": "PP5", "rule": {"external.[Trusted source]": "Pathogenic"}},
    # Manual edit
    { "code": "PPxPM2", "rule": {"$$aggregate": {"$and": ["REQ_null_freq", {"$not": {"$in": ["REQ_less_common","REQ_hi_freq"]}}]}}},
    { "code": "PPxPM5", "rule": {"$$aggregate": {"$all": ["REQ_overlap_pat", "REQ_novel_aa", "REQ_aa_diff"]}}},
    ### BP*
    { "code": "BP1", "rule": {"$$aggregate": {"$all": ["REQ_missense", "REQ_GP_lof_only"]}}},
    { "code": "BP2", "rule": {"family.phase": "in_cis_pathogenic"}},
    { "code": "BP2", "rule": {"$$aggregate": {"$all": ["REQ_in_trans_pathogenic", "REQ_GP_inh_ad"]}}},
    { "code": "BP3", "rule": {"$$aggregate": {"$all": ["REQ_inframe", "REQ_repeat"]}}},
    # Manual edit
    { "code": "BP4", "rule": {"transcript.splice_Effect": {"$or": [{"$in": ["predicted_conserved", "consensus_not_affected", "not_transcribed"]}, {"$not": {"$in": ["de_novo"]}}]}}},
    { "code": "BP4", "rule": {"genomic.conservation": "non-conserved"}},
    # BP5 (not implemented)
    { "code": "BP6", "rule": {"external.[Trusted source]": "Benign"}},
    { "code": "BP7", "rule": {"$$aggregate": {"$all": ["REQ_no_aa_change", "REQ_non-conserved", "REQ_no_splice_effect"]}}},
    { "code": "BPxBS3", "rule": {"refassessment.*.ref_prot": "prot-"}},
    { "code": "BPxBS3", "rule": {"refassessment.*.ref_rna": "rna-"}},
    { "code": "BPxBS3", "rule": {"refassessment.*.ref_msi": "msi-"}},
    { "code": "BPxPM5", "rule": {"$$aggregate": {"$all": ["REQ_overlap_ben", "REQ_same_aa"]}}},
    ### BS*
    { "code": "BS1", "rule": {"$$aggregate": {"$all": ["REQ_less_common", "REQ_GP_inh_ad"]}}},
    { "code": "BS2", "rule": {"refassessment.*.ref_population": "in_healthy"}},
    { "code": "BS3", "rule": {"refassessment.*.ref_prot": "prot--"}},
    { "code": "BS3", "rule": {"refassessment.*.ref_rna": "rna--"}},
    { "code": "BS3", "rule": {"refassessment.*.ref_msi": "msi--"}},
    { "code": "BS3", "rule": {"refassessment.*.ref_ihc": "mmr_noloss"}},
    { "code": "BS4", "rule": {"refassessment.*.ref_segregation": "segr-"}},
    { "code": "BS4", "rule": {"family.segregation": "segr-"}},
    ### BA*
    { "code": "BA1", "rule": {"frequencies.ExAC_cutoff": "≥hi_freq_cutoff"}},
    { "code": "BA1", "rule": {"frequencies.1000G_cutoff": "≥hi_freq_cutoff"}},
    { "code": "BA1", "rule": {"frequencies.ESP6500_cutoff": "≥hi_freq_cutoff"}},
    { "code": "BA1", "rule": {"frequencies.inDB_cutoff": "≥hi_freq_cutoff"}},


#    {
#        "code": "XXX",
#        "rule": {"$$aggregate": {"$atleast": [1, "REQ-1", "REQ-2", "REQ-3"]}}
#    },

]
