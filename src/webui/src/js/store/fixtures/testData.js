const testUiConfig = {
    app: {
        links_to_clipboard: false,
        non_production_warning: null,
        annotation_service: 'http://172.17.0.1:6000',
        attachment_storage: '/ella/attachments/',
        max_upload_size: 52428800
    },
    user: {
        auth: {
            password_expiry_days: 90,
            password_minimum_length: 8,
            password_match_groups: ['.*[A-Z].*', '.*[a-z].*', '.*[0-9].*', '.*[^A-Za-z0-9].*'],
            password_match_groups_descr: [
                'Uppercase letters [A-Z]',
                'Lowercase letters [a-z]',
                'Digits [0-9]',
                'Special characters'
            ],
            password_num_match_groups: 3
        },
        user_config: {
            overview: {
                views: ['variants', 'analyses-by-classified', 'import'],
                show_variant_report: true
            },
            workflows: {
                allele: {
                    finalize_requirements: {
                        workflow_status: ['Interpretation', 'Review']
                    }
                },
                analysis: {
                    finalize_requirements: {
                        workflow_status: [
                            'Not ready',
                            'Interpretation',
                            'Review',
                            'Medical review'
                        ],
                        allow_notrelevant: false,
                        allow_technical: true,
                        allow_unclassified: false
                    }
                }
            },
            acmg: {
                genes: {
                    '1101': {
                        comment: 'a comment from the ACMG config',
                        frequency: {
                            thresholds: {
                                external: {
                                    hi_freq_cutoff: 0.008,
                                    lo_freq_cutoff: 0.0005
                                },
                                internal: {
                                    hi_freq_cutoff: 0.008,
                                    lo_freq_cutoff: 0.0005
                                }
                            }
                        },
                        disease_mode: 'ANY',
                        last_exon_important: 'LENI'
                    }
                },
                frequency: {
                    thresholds: {
                        AD: {
                            external: {
                                hi_freq_cutoff: 0.005,
                                lo_freq_cutoff: 0.001
                            },
                            internal: {
                                hi_freq_cutoff: 0.05,
                                lo_freq_cutoff: 1
                            }
                        },
                        default: {
                            external: {
                                hi_freq_cutoff: 0.01,
                                lo_freq_cutoff: 1
                            },
                            internal: {
                                hi_freq_cutoff: 0.05,
                                lo_freq_cutoff: 1
                            }
                        }
                    },
                    num_thresholds: {
                        GNOMAD_EXOMES: {
                            G: 5000,
                            AFR: 5000,
                            AMR: 5000,
                            EAS: 5000,
                            FIN: 5000,
                            NFE: 5000,
                            OTH: 5000,
                            SAS: 5000
                        },
                        GNOMAD_GENOMES: {
                            G: 5000,
                            AFR: 5000,
                            AMR: 5000,
                            EAS: 5000,
                            FIN: 5000,
                            NFE: 5000,
                            OTH: 5000,
                            SAS: 5000
                        }
                    }
                },
                disease_mode: 'ANY',
                last_exon_important: 'LEI'
            },
            deposit: {
                analysis: [
                    {
                        pattern: '^NonExistingPattern.*',
                        postprocess: [
                            'analysis_not_ready_findings',
                            'analysis_finalize_without_findings'
                        ]
                    }
                ]
            },
            comment_templates: [
                {
                    name: 'Example template',
                    template:
                        '<h3>Example template</h3><ol><li>Example one</li><li>Example two</li><li>Example three</li></ol>',
                    comment_fields: [
                        'classificationAnalysisSpecific',
                        'classificationEvaluation',
                        'classificationAcmg',
                        'classificationReport',
                        'classificationFrequency',
                        'classificationPrediction',
                        'classificationExternal',
                        'classificationReferences',
                        'reportIndications',
                        'reportSummary',
                        'referenceEvaluation',
                        'workLogMessage'
                    ]
                }
            ]
        }
    },
    analysis: {
        priority: {
            display: {
                '1': 'Normal',
                '2': 'High',
                '3': 'Urgent'
            }
        },
        sidebar: {
            full: {
                columns: [],
                classification_options: [],
                shade_multiple_in_gene: true
            },
            quick: {
                columns: ['qual', 'dp', 'ratio', 'hi-freq', 'hi-count', 'external'],
                classification_options: ['technical', 'notrelevant', 'classu', 'class2'],
                narrow_comment: false,
                shade_multiple_in_gene: true
            },
            visual: {
                columns: ['qual', 'ratio'],
                classification_options: ['technical'],
                narrow_comment: true,
                shade_multiple_in_gene: true
            },
            report: {
                columns: [],
                classification_options: [],
                shade_multiple_in_gene: true
            },
            list: {
                columns: ['qual', 'dp', 'ratio', 'hi-freq', 'hi-count', 'external'],
                classification_options: [],
                shade_multiple_in_gene: false
            }
        }
    },
    annotation: {
        clinvar: {
            clinical_significance_status: {
                'criteria provided, conflicting interpretations': 1,
                'criteria provided, multiple submitters, no conflicts': 2,
                'criteria provided, single submitter': 1,
                'no assertion criteria provided': 0,
                'no assertion provided': 0,
                'practice guideline': 4,
                'reviewed by expert panel': 3
            }
        }
    },
    frequencies: {
        groups: {
            external: {
                GNOMAD_GENOMES: ['G', 'AFR', 'AMR', 'EAS', 'FIN', 'NFE', 'OTH', 'SAS'],
                GNOMAD_EXOMES: ['G', 'AFR', 'AMR', 'EAS', 'FIN', 'NFE', 'OTH', 'SAS']
            },
            internal: {
                inDB: ['OUSWES']
            }
        },
        view: {
            groups: {
                GNOMAD_GENOMES: ['G', 'AFR', 'AMR', 'ASJ', 'EAS', 'FIN', 'NFE', 'OTH', 'SAS'],
                GNOMAD_EXOMES: ['G', 'AFR', 'AMR', 'ASJ', 'EAS', 'FIN', 'NFE', 'OTH', 'SAS'],
                ExAC: ['G', 'AFR', 'AMR', 'EAS', 'FIN', 'NFE', 'OTH', 'SAS'],
                '1000g': ['G', 'AMR', 'ASN', 'EUR', 'EAS', 'SAS'],
                esp6500: ['AA', 'EA'],
                inDB: ['OUSWES']
            },
            precision: 6,
            scientific_threshold: 4,
            indications_threshold: 10,
            GNOMAD_GENOMES: {
                G: 'TOT',
                AFR: 'AFR',
                AMR: 'LAT',
                ASJ: 'ASJ',
                EAS: 'EA',
                FIN: 'E(F)',
                NFE: 'E(NF)',
                OTH: 'OTH',
                SAS: 'SA'
            },
            GNOMAD_EXOMES: {
                G: 'TOT',
                AFR: 'AFR',
                AMR: 'LAT',
                ASJ: 'ASJ',
                EAS: 'EA',
                FIN: 'E(F)',
                NFE: 'E(NF)',
                OTH: 'OTH',
                SAS: 'SA'
            },
            ExAC: {
                G: 'TOT',
                AFR: 'AFR',
                AMR: 'LAT',
                EAS: 'EA',
                FIN: 'E(F)',
                NFE: 'E(NF)',
                OTH: 'OTH',
                SAS: 'SA'
            }
        }
    },
    classification: {
        gene_groups: {
            MMR: ['MLH1', 'MSH2', 'MSH6', 'PMS2']
        },
        options: [
            {
                name: 'Class U',
                value: 'U'
            },
            {
                name: 'Class 1',
                value: '1'
            },
            {
                name: 'Class 2',
                value: '2',
                outdated_after_days: 180
            },
            {
                name: 'Class 3',
                value: '3',
                outdated_after_days: 180,
                include_report: true,
                include_analysis_with_findings: true
            },
            {
                name: 'Class 4',
                value: '4',
                outdated_after_days: 180,
                include_report: true,
                include_analysis_with_findings: true
            },
            {
                name: 'Class 5',
                value: '5',
                outdated_after_days: 365,
                include_report: true,
                include_analysis_with_findings: true
            },
            {
                name: 'Drug response',
                value: 'DR'
            }
        ]
    },
    report: {
        classification_text: {
            '1': 'Ikke sykdomsgivende variant',
            '2': 'Sannsynlig ikke sykdomsgivende variant',
            '3': 'Variant med usikker betydning',
            '4': 'Sannsynlig sykdomsgivende variant',
            '5': 'Sykdomsgivende variant'
        }
    },
    transcripts: {
        consequences: [
            'transcript_ablation',
            'splice_donor_variant',
            'splice_acceptor_variant',
            'stop_gained',
            'frameshift_variant',
            'start_lost',
            'initiator_codon_variant',
            'stop_lost',
            'inframe_insertion',
            'inframe_deletion',
            'missense_variant',
            'protein_altering_variant',
            'transcript_amplification',
            'splice_region_variant',
            'incomplete_terminal_codon_variant',
            'synonymous_variant',
            'start_retained_variant',
            'stop_retained_variant',
            'coding_sequence_variant',
            'mature_miRNA_variant',
            '5_prime_UTR_variant',
            '3_prime_UTR_variant',
            'non_coding_transcript_exon_variant',
            'non_coding_transcript_variant',
            'intron_variant',
            'NMD_transcript_variant',
            'upstream_gene_variant',
            'downstream_gene_variant',
            'TFBS_ablation',
            'TFBS_amplification',
            'TF_binding_site_variant',
            'regulatory_region_variant',
            'regulatory_region_ablation',
            'regulatory_region_amplification',
            'feature_elongation',
            'feature_truncation',
            'intergenic_variant'
        ],
        inclusion_regex: 'NM_.*'
    },
    igv: {
        reference: {
            fastaURL: '//igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta',
            cytobandURL: '//igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt'
        },
        valid_resource_files: [
            'cytoBand.txt',
            'human_g1k_v37_decoy.fasta',
            'human_g1k_v37_decoy.fasta.fai'
        ]
    },
    import: {
        automatic_deposit_with_sample_id: false,
        preimport_script: '/ella/src/api/config/../../../scripts/preimport.py'
    },
    acmg: {
        formatting: {
            operators: {
                $in: '=',
                $gt: '>',
                $lt: '<',
                $not: '!=',
                $range: 'within',
                $all: '=',
                $at_least: 'at least'
            }
        },
        codes: {
            pathogenic: ['PVS', 'PS', 'PM', 'PP'],
            benign: ['BP', 'BS', 'BA']
        },
        explanation: {
            REQ_GP_AD: {
                short_criteria: 'AD',
                sources: [],
                criteria: 'Autosomal dominant inheritance'
            },
            REQ_GP_AR: {
                short_criteria: 'AR',
                sources: [],
                criteria: 'Autosomal recessive inheritance'
            },
            REQ_GP_last_exon_important: {
                short_criteria: 'Last exon important',
                sources: [],
                criteria: 'The last exon of this gene is important'
            },
            REQ_GP_last_exon_not_important: {
                short_criteria: 'Last exon not important',
                sources: [],
                criteria: 'The last exon of this gene is not important'
            },
            REQ_GP_LOF_missense: {
                short_criteria: 'LOF and missense = disease',
                sources: [],
                criteria: 'Both loss of function and missense variants cause disease in this gene'
            },
            REQ_GP_LOF_only: {
                short_criteria: 'Only LOF = disease',
                sources: [],
                criteria: 'Only loss of function variants cause disease in this gene'
            },
            REQ_GP_missense_common: {
                short_criteria: 'Missense variation common',
                sources: [],
                criteria: 'Benign missense variation is common in this gene'
            },
            REQ_GP_missense_uncommon: {
                short_criteria: 'Missense variation uncommon',
                sources: [],
                criteria: 'Benign missense variation is uncommon in this gene'
            },
            REQ_GP_missense_only: {
                short_criteria: 'Only missense = disease',
                sources: [],
                criteria: 'Only missense variants cause disease in this gene'
            },
            REQ_GP_XD: {
                short_criteria: 'XD',
                sources: [],
                criteria: 'X-linked dominant inheritance'
            },
            REQ_GP_XR: {
                short_criteria: 'XR',
                sources: [],
                criteria: 'X-linked recessive inheritance'
            },
            'REQ_>=4affected': {
                short_criteria: 'In >=4 unrelated patients',
                sources: ['PS4'],
                criteria: 'Observed in four or more unrelated patients and not in controls'
            },
            REQ_2affected: {
                short_criteria: 'In 2 unrelated patients',
                sources: ['PPxPS4'],
                criteria: 'Observed in two unrelated patients and not in controls'
            },
            REQ_3affected: {
                short_criteria: 'In 3 unrelated patients',
                sources: ['PMxPS4'],
                criteria: 'Observed in three unrelated patients and not in controls'
            },
            REQ_aa_different: {
                short_criteria: 'Not = reported aa properties',
                sources: ['PPxPM5'],
                criteria: 'The resulting amino acid has different properties from that reported'
            },
            REQ_aa_similar: {
                short_criteria: '= reported aa properties',
                sources: ['PM5'],
                criteria: 'The resulting amino acid has similar properties to that reported'
            },
            REQ_abnormal_protein: {
                short_criteria: 'Functional protein damage',
                sources: ['PS3', 'PMxPS3'],
                criteria:
                    'Well-established in vitro or in vivo functional studies are supportive of a damaging effect on the gene or gene product'
            },
            REQ_abnormal_RNA: {
                short_criteria: 'Functional RNA damage',
                sources: ['PS3', 'PMxPS3'],
                criteria:
                    'Well-established in vitro or in vivo functional studies are supportive of a damaging effect on the gene or gene product'
            },
            REQ_crit_domain_hotspot: {
                short_criteria: 'Critical domain or hotspot',
                sources: ['PM1'],
                criteria:
                    'Located in a mutational hot spot and/or critical and well-established functional domain (e.g., active site of an enzyme) without benign variation'
            },
            REQ_crit_site: {
                short_criteria: 'Critical site',
                sources: ['PSxPM1'],
                criteria:
                    'Located in a mutational hot spot and/or critical and well-established functional domain (e.g., active site of an enzyme) without benign variation'
            },
            REQ_domain_no_benign: {
                short_criteria: 'No benign variation',
                sources: ['PM1', 'PSxPM1'],
                criteria:
                    'Located in a mutational hot spot and/or critical and well-established functional domain (e.g., active site of an enzyme) without benign variation'
            },
            REQ_hi_freq: {
                short_criteria: 'High frequency',
                sources: ['BA1'],
                criteria: 'Allele frequency is >=hi_freq_cutoff in this database'
            },
            REQ_IHC_HQ: {
                short_criteria: 'Strong functional MMR evidence',
                sources: ['PS3', 'BS3'],
                criteria: 'The functional evidence is strong'
            },
            REQ_IHC_MQ: {
                short_criteria: 'Moderate functional MMR evidence',
                sources: ['PMxPS3'],
                criteria: 'The functional evidence is moderate'
            },
            REQ_in_last_exon: {
                short_criteria: 'In last exon',
                sources: ['PVS1'],
                criteria: 'The variant is in the last exon of a gene'
            },
            REQ_in_trans_pathogenic: {
                short_criteria: 'In trans pathogenic',
                sources: ['PM3', 'BP2'],
                criteria: 'The variant is located in trans with a pathogenic variant'
            },
            REQ_inframe: {
                short_criteria: 'In-frame/stop-loss',
                sources: ['PM4', 'BP3'],
                criteria:
                    'Protein length changes as a result of in-frame deletions/insertions or stop-loss variants'
            },
            REQ_less_common: {
                short_criteria: 'Frequency >expected',
                sources: ['BS1'],
                criteria: 'Allele frequency is greater than expected for disorder'
            },
            REQ_missense: {
                short_criteria: 'Missense',
                sources: ['PP2', 'BP1'],
                criteria: 'Missense variant'
            },
            REQ_MMR_loss: {
                short_criteria: 'Loss of MMR',
                sources: ['PS3', 'PMxPS3'],
                criteria:
                    'Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing'
            },
            REQ_MSI: {
                short_criteria: 'MSI demonstrated',
                sources: ['PS3', 'PMxPS3'],
                criteria:
                    'Well-established in vitro or in vivo functional studies are supportive of a damaging effect on the gene or gene product'
            },
            REQ_MSI_HQ: {
                short_criteria: 'Strong MSI evidence',
                sources: ['PS3', 'BS3'],
                criteria: 'The functional evidence is strong'
            },
            REQ_MSI_MQ: {
                short_criteria: 'Moderate MSI evidence',
                sources: ['PMxPS3', 'BPxBS3'],
                criteria: 'The functional evidence is moderate'
            },
            REQ_no_aa_change: {
                short_criteria: 'Synonymous/non-coding',
                sources: ['BP7'],
                criteria: 'Synonymous or non-coding variant'
            },
            REQ_no_freq: {
                short_criteria: 'Not in controls',
                sources: ['PM2', 'PPxPM2'],
                criteria: 'Absent from controls in this database'
            },
            REQ_no_MSI: {
                short_criteria: 'MSI not demonstrated',
                sources: ['BS3', 'BPxBS3'],
                criteria:
                    'Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing'
            },
            REQ_no_segregation: {
                short_criteria: 'No segregation',
                sources: ['BS4', 'BPxBS4'],
                criteria: 'Lack of segregation in affected members of a family'
            },
            REQ_no_splice_effect: {
                short_criteria: 'No splice effect',
                sources: ['BP7'],
                criteria: 'No splice effect predicted'
            },
            REQ_normal_protein: {
                short_criteria: 'No functional protein damage',
                sources: ['BS3', 'BPxBS3'],
                criteria:
                    'Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing'
            },
            REQ_normal_RNA: {
                short_criteria: 'No functional RNA damage',
                sources: ['BS3', 'BPxBS3'],
                criteria:
                    'Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing'
            },
            REQ_non_repeat: {
                short_criteria: 'Not in repeat region',
                sources: ['PM4'],
                criteria: 'The variant is not located in a repeat region'
            },
            REQ_not_in_last_exon: {
                short_criteria: 'Not in last exon',
                sources: ['PVS1'],
                criteria: 'The variant is not located in the last exon of the gene'
            },
            REQ_novel_aa: {
                short_criteria: 'Not = reported aa change',
                sources: ['PM5', 'PPxPM5'],
                criteria: 'The amino acid change is different from that previously reported'
            },
            REQ_null_variant: {
                short_criteria: 'Null variant',
                sources: ['PVS1'],
                criteria:
                    'Null variant (nonsense, frameshift, canonical +/- 2 bp splice sites, initiation codon, single or multiexon deletion)'
            },
            REQ_overlap_HQ: {
                short_criteria: 'Strong overlapping aa evidence',
                sources: ['PS1', 'PM5', 'PPxPM5'],
                criteria: 'The evidence for reported, overlapping amino acid is strong'
            },
            REQ_overlap_MQ: {
                short_criteria: 'Moderate overlapping aa evidence',
                sources: ['PMxPS1', 'PPxPM5'],
                criteria:
                    'The strength of the evidence for reported, overlapping amino acid is moderate'
            },
            REQ_overlap_pat: {
                short_criteria: 'Pathogenic aa change',
                sources: ['PS1', 'PM5', 'PPxPM5'],
                criteria:
                    'Changes in this amino acid position has previously been reported pathogenic'
            },
            REQ_protein_HQ: {
                short_criteria: 'Strong functional protein evidence',
                sources: ['PS3', 'BS3'],
                criteria: 'The functional protein evidence is strong'
            },
            REQ_protein_MQ: {
                short_criteria: 'Moderate functional protein evidence',
                sources: ['PMxPS3', 'BPxBS3'],
                criteria: 'The functional protein evidence is moderate'
            },
            REQ_repeat: {
                short_criteria: 'In repeat region',
                sources: ['BP3'],
                criteria: 'The variant is located in a repeat region'
            },
            REQ_RNA_HQ: {
                short_criteria: 'Strong functional RNA evidence',
                sources: ['PS3', 'BS3'],
                criteria: 'The functional RNA evidence is strong'
            },
            REQ_RNA_MQ: {
                short_criteria: 'Moderate functional RNA evidence',
                sources: ['PMxPS3', 'BPxBS3'],
                criteria: 'The functional RNA evidence is moderate'
            },
            REQ_same_aa: {
                short_criteria: '= reported aa change ',
                sources: ['PS1'],
                criteria: 'The amino acid change is the same as that previously reported'
            },
            REQ_segregation: {
                short_criteria: 'Cosegregation',
                sources: ['PP1', 'PMxPP1', 'PSxPP1'],
                criteria:
                    'Cosegregation with disease in multiple affected family members in a gene definitively known to cause the disease'
            },
            REQ_segregation_HQ: {
                short_criteria: 'Strong cosegregation evidence',
                sources: ['PSxPP1'],
                criteria: 'The evidence for cosegregation is strong'
            },
            REQ_segregation_MQ: {
                short_criteria: 'Moderate cosegregation evidence',
                sources: ['PMxPP1'],
                criteria: 'The evidence for cosegregation is moderate'
            },
            REQ_segregation_WQ: {
                short_criteria: 'Weak cosegregation evidence',
                sources: ['PP1'],
                criteria: 'The evidence for cosegregation is weak'
            },
            PVS1: {
                short_criteria: 'Null variant',
                sources: [],
                notes:
                    "- Caution: Genes where LOF is not a known disease mechanism (e.g. GFAP, MYH7)\n- Caution: LOF variants at the extreme 3' end of a gene\n- Caution: Splice variants that lead to exon skipping but leave remainder of protein intact\n- Caution: When there are multiple transcripts",
                criteria:
                    'Null variant (nonsense, frameshift, canonical +/- 2 bp splice sites, initiation codon, single or multiexon deletion) in a gene where LOF is a known mechanism of disease.\n'
            },
            PS1: {
                short_criteria: 'Known pathogenic aa',
                sources: [],
                notes:
                    '- Caution: Changes that impact splicing rather than amino acid \n- Example: Val to Leu caused by either G>C or G>T in the same codon',
                criteria:
                    'Same amino acid change as a previously established pathogenic variant regardless of nucleotide change'
            },
            PS2: {
                short_criteria: 'De novo (confirmed)',
                sources: [],
                notes:
                    '- Note: Confirmation of paternity only is insufficient. Egg donation, surrogate motherhood, errors in embryo transfer, and so on, can contribute to nonmaternity.',
                criteria:
                    'De novo (both maternity and paternity confirmed) in a patient with the disease and no family history'
            },
            PS3: {
                short_criteria: 'Functional damage',
                sources: [],
                notes:
                    '- Note: Functional studies that have been validated and shown to be reproducible and robust in a clinical diagnostic laboratory setting are considered the most well established.',
                criteria:
                    'Well-established in vitro or in vivo functional studies supportive of a damaging effect on the gene or gene product'
            },
            PS4: {
                short_criteria: 'Increased prevalence in patients',
                sources: [],
                notes:
                    '- Note: RR or OR >5.0 obtained from case-control studies, CI does not include 1.0\n- Note: In instances of very rare variants where case–control studies may not reach statistical significance, the prior observation of the variant in multiple unrelated patients with the same phenotype, and its absence in controls, may be used as moderate level of evidence',
                criteria:
                    'The prevalence of the variant in affected individuals is significantly increased compared with the prevalence in controls'
            },
            PM1: {
                short_criteria: 'Functional domain',
                sources: [],
                criteria:
                    'Located in a mutational hot spot and/or critical and well-established functional domain  (e.g., active site of an enzyme) without benign variation'
            },
            PM2: {
                short_criteria: 'Absent from controls',
                sources: [],
                notes:
                    '- Caution: Population data for insertions/deletions may be poorly called by next-generation sequencing',
                criteria: 'Absent from controls (or at extremely low frequency if recessive)'
            },
            PM3: {
                short_criteria: 'In trans pathogenic & AR',
                sources: [],
                notes:
                    '- Note: This requires testing of parents (or offspring) to determine phase.',
                criteria: 'For recessive disorders, detected in trans with a pathogenic variant.'
            },
            PM4: {
                short_criteria: 'In-frame/stop-loss',
                sources: [],
                criteria:
                    'Protein length changes as a result of in-frame deletions/insertions in a nonrepeat region or stop-loss variants.'
            },
            PM5: {
                short_criteria: 'Novel at known pathogenic aa',
                sources: [],
                notes:
                    '- Caution: Changes that impact splicing rather than amino acid. \n- Example: Arg156His is pathogenic; now you observe Arg156Cys',
                criteria:
                    'Novel missense change at an amino acid residue where a different missense change determined to be pathogenic has been seen before'
            },
            PM6: {
                short_criteria: 'De novo (unconfirmed)',
                sources: [],
                criteria: 'Assumed de novo, but without confirmation of paternity and maternity'
            },
            PP1: {
                short_criteria: 'Cosegregation',
                sources: [],
                notes: '- May be used as stronger evidence with increasing segregation data',
                criteria:
                    'Cosegregation with disease in multiple affected family members in a gene definitively known to cause the disease'
            },
            PP2: {
                short_criteria: 'Missense: important',
                sources: [],
                criteria:
                    'Missense variant in a gene that has a low rate of benign missense variation and in which missense variants are a common mechanism of disease.'
            },
            PP3: {
                short_criteria: 'Predicted pathogenic',
                sources: [],
                notes:
                    '- Caution: Because many algorithms use the same or very similar input for their predictions, each algorithm cannot be counted as an independent criterion. PP3 can be used only once in any evaluation of a variant.',
                criteria:
                    'Multiple lines of computational evidence support a deleterious effect on the gene or gene product (conservation, evolutionary, splicing impact, etc.)'
            },
            PP4: {
                short_criteria: 'Phenotype: single gene',
                sources: [],
                criteria:
                    "Patient's phenotype or family history is highly specific for a disease with a single genetic etiology"
            },
            PP5: {
                short_criteria: 'Reported pathogenic, evidence unavailable',
                sources: [],
                criteria:
                    'Reputable source recently reports variant as pathogenic, but the evidence is not available to the laboratory to perform an independent evaluation'
            },
            BA1: {
                short_criteria: 'High frequency',
                sources: [],
                criteria: 'Allele frequency is >5 % in ESP, 1000G or ExAC'
            },
            BS1: {
                short_criteria: 'Frequency >expected',
                sources: [],
                criteria: 'Allele frequency is greater than expected for disorder'
            },
            BS2: {
                short_criteria: 'In documented healthy',
                sources: [],
                criteria:
                    'Observed in a healthy adult individual for a recessive (homozygous), dominant (heterozygous), or X-linked (hemizygous) disorder, with full penentrance expected at an early age'
            },
            BS3: {
                short_criteria: 'No functional damage',
                sources: [],
                criteria:
                    'Well-established in vitro or in vivo functional studies show no damaging effect on protein function or splicing'
            },
            BS4: {
                short_criteria: 'Non-segregation',
                sources: [],
                notes:
                    '- Caution: The presence of phenocopies for common phenotypes (i.e., cancer, epilepsy) can mimic lack of segregation among affected individuals. Also, families may have more than one pathogenic variant contributing to an autosomal dominant disorder, further confounding an apparent lack of segregation.',
                criteria: 'Lack of segregation in affected members of a family'
            },
            BP1: {
                short_criteria: 'Missense; not important',
                sources: [],
                criteria:
                    'Missense variant in a gene for which primarily truncating variants are known to cause disease'
            },
            BP2: {
                short_criteria: 'In trans & AD, or in cis pathogenic',
                sources: [],
                criteria:
                    'Observed in trans with a pathogenic variant for a fully penetrant dominant gene/disorder or in cis with a pathogenic variant in any inheritance pattern'
            },
            BP3: {
                short_criteria: 'In-frame; non-functional',
                sources: [],
                criteria:
                    'In-frame insertions/delitions in a repetitive region without a known function'
            },
            BP4: {
                short_criteria: 'Predicted benign',
                sources: [],
                notes:
                    '- Caution: Because many algorithms use the same or very similar input for their predictions, each algorithm cannot be counted as an independent criterion. BP4 can be used only once in any evaluation of a variant.',
                criteria:
                    'Multiple lines of computational evidence suggest no impact on gene or gene product (conservation, evolutionary, splicing impact, etc.)'
            },
            BP5: {
                short_criteria: 'Other causative variant found',
                sources: [],
                notes:
                    '- Caution: patient can be a carrier of an unrelated pathogenic variant for a recessive disorder, disorders where having multiple variants can contribute to more severe disease, multigenic disorders',
                criteria: 'Variant found in a case with an alternate molecular basis for disease'
            },
            BP6: {
                short_criteria: 'Reported benign, evidence unavailable',
                sources: [],
                criteria:
                    'Reputable source recently reports variant as benign, but the evidence is not available to the laboratory to perform an independent evaluation'
            },
            BP7: {
                short_criteria: 'Synonymous, no splice effect',
                sources: [],
                criteria:
                    'A synonymous variant for which splicing prediction algorithms predict no impact to the splice consensus sequence nor the creation of a new splice site AND the nucleotide is not highly conserved'
            }
        }
    },
    custom_annotation: {
        external: [
            {
                key: 'LOVD_InSiGHT-APC',
                name: 'LOVD - InSiGHT APC',
                only_for_genes: [583],
                url_for_genes: {
                    '583': 'https://insight-database.org/#tabs-2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'UMD-APC',
                name: 'UMD',
                only_for_genes: [583],
                url_for_genes: {
                    '583': 'http://www.umd.be/APC/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-APC',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [583],
                url_for_genes: {
                    '583':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=APC'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-APC',
                name: 'X - LOVD - Shared APC (not in use)',
                only_for_genes: [583],
                url_for_genes: {
                    '583': 'https://databases.lovd.nl/shared/view/APC'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-BMPR1A',
                name: 'LOVD - Shared BMPR1A',
                only_for_genes: [1076],
                url_for_genes: {
                    '1076': 'https://databases.lovd.nl/shared/view/BMPR1A'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'BRCA_Exchange-BRCA1',
                name: 'BRCA Exchange',
                only_for_genes: [1100],
                url_for_genes: {
                    '1100': 'https://brcaexchange.org/variants?search=BRCA1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_IARC_HCI-BRCA1',
                name: 'LOVD IARC HCI',
                only_for_genes: [1100],
                url_for_genes: {
                    '1100': 'http://hci-exlovd.hci.utah.edu/home.php?select_db=BRCA1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-BRCA1',
                name: 'LOVD - Shared BRCA1',
                only_for_genes: [1100],
                url_for_genes: {
                    '1100': 'https://databases.lovd.nl/shared/view/BRCA1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'UMD_BRCAshare-BRCA1',
                name: 'UMD BRCAshare',
                only_for_genes: [1100],
                url_for_genes: {
                    '1100': 'http://www.umd.be/BRCA1/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'BIC-BRCA1',
                name: 'X - BIC (not in use)',
                only_for_genes: [1100],
                url_for_genes: {
                    '1100': 'http://www.research.nhgri.nih.gov/projects/bic/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-BRCA1',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [1100],
                url_for_genes: {
                    '1100':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=BRCA1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'BRCA_Exchange-BRCA2',
                name: 'BRCA Exchange',
                only_for_genes: [1101],
                url_for_genes: {
                    '1101': 'https://brcaexchange.org/variants?search=BRCA2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_IARC_HCI-BRCA2',
                name: 'LOVD IARC HCI',
                only_for_genes: [1101],
                url_for_genes: {
                    '1101': 'http://hci-exlovd.hci.utah.edu/home.php?select_db=BRCA2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-BRCA2',
                name: 'LOVD - Shared BRCA2',
                only_for_genes: [1101],
                url_for_genes: {
                    '1101': 'https://databases.lovd.nl/shared/view/BRCA2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'UMD_BRCAshare-BRCA2',
                name: 'UMD BRCAshare',
                only_for_genes: [1101],
                url_for_genes: {
                    '1101': 'http://www.umd.be/BRCA2/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'BIC-BRCA2',
                name: 'X - BIC (not in use)',
                only_for_genes: [1101],
                url_for_genes: {
                    '1101': 'http://www.research.nhgri.nih.gov/projects/bic/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-BRCA2',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [1101],
                url_for_genes: {
                    '1101':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=BRCA2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_InSiGHT-CDH1',
                name: 'LOVD - InSiGHT CDH1',
                only_for_genes: [1748],
                url_for_genes: {
                    '1748': 'https://insight-database.org/#tabs-9'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-CDH1',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [1748],
                url_for_genes: {
                    '1748':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=CDH1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-CDH1',
                name: 'X - LOVD - Shared CDH1 (not in use)',
                only_for_genes: [1748],
                url_for_genes: {
                    '1748': 'https://databases.lovd.nl/shared/view/CDH1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-CDKN2A',
                name: 'LOVD - Shared CDKN2A',
                only_for_genes: [1787],
                url_for_genes: {
                    '1787': 'https://databases.lovd.nl/shared/view/CDKN2A'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD-DICER1',
                name: 'LOVD',
                only_for_genes: [17098],
                url_for_genes: {
                    '17098':
                        'https://grenada.lumc.nl/LOVD2/mendelian_genes/home.php?select_db=DICER1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-DICER1',
                name: 'LOVD - Shared DICER1',
                only_for_genes: [17098],
                url_for_genes: {
                    '17098': 'https://databases.lovd.nl/shared/genes/DICER1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-EXT1',
                name: 'LOVD - Shared EXT1',
                only_for_genes: [3512],
                url_for_genes: {
                    '3512': 'https://databases.lovd.nl/shared/view/EXT1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_medgen-EXT1',
                name: 'X - LOVD medgen (not in use)',
                only_for_genes: [3512],
                url_for_genes: {
                    '3512': 'http://medgen.ua.ac.be/LOVDv.2.0/home.php?select_db=EXT1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-EXT2',
                name: 'LOVD - Shared EXT2',
                only_for_genes: [3513],
                url_for_genes: {
                    '3513': 'https://databases.lovd.nl/shared/view/EXT2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_medgen-EXT2',
                name: 'X - LOVD medgen (not in use)',
                only_for_genes: [3513],
                url_for_genes: {
                    '3513': 'http://medgen.ua.ac.be/LOVDv.2.0/home.php?select_db=EXT2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-FLCN ',
                name: 'LOVD - Shared FLCN',
                only_for_genes: [27310],
                url_for_genes: {
                    '27310': 'https://databases.lovd.nl/shared/view/FLCN'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-HOXB13',
                name: 'LOVD - Shared HOXB13',
                only_for_genes: [5112],
                url_for_genes: {
                    '5112': 'https://databases.lovd.nl/shared/genes/HOXB13'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_hci_priors-MLH1',
                name: 'LOVD hci priors',
                only_for_genes: [7127],
                url_for_genes: {
                    '7127': 'http://hci-lovd.hci.utah.edu/home.php?select_db=MLH1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_InSiGHT-MLH1',
                name: 'LOVD - InSiGHT MLH1',
                only_for_genes: [7127],
                url_for_genes: {
                    '7127': 'https://insight-database.org/#tabs-3'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'UMD-MLH1',
                name: 'UMD',
                only_for_genes: [7127],
                url_for_genes: {
                    '7127': 'http://www.umd.be/MLH1/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-MLH1',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [7127],
                url_for_genes: {
                    '7127':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=MLH1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-MLH1',
                name: 'X - LOVD - Shared MLH1 (not in use)',
                only_for_genes: [7127],
                url_for_genes: {
                    '7127': 'https://databases.lovd.nl/shared/view/MLH1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_hci_priors-MSH2',
                name: 'LOVD hci priors',
                only_for_genes: [7325],
                url_for_genes: {
                    '7325': 'http://hci-lovd.hci.utah.edu/home.php?select_db=MSH2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_InSiGHT-MSH2',
                name: 'LOVD - InSiGHT MSH2',
                only_for_genes: [7325],
                url_for_genes: {
                    '7325': 'https://insight-database.org/#tabs-4'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'UMD-MSH2',
                name: 'UMD',
                only_for_genes: [7325],
                url_for_genes: {
                    '7325': 'http://www.umd.be/MSH2/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-MSH2',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [7325],
                url_for_genes: {
                    '7325':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=MSH2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-MSH2',
                name: 'X - LOVD - Shared MSH2 (not in use)',
                only_for_genes: [7325],
                url_for_genes: {
                    '7325': 'https://databases.lovd.nl/shared/view/MSH2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_hci_priors-MSH6',
                name: 'LOVD hci priors',
                only_for_genes: [7329],
                url_for_genes: {
                    '7329': 'http://hci-lovd.hci.utah.edu/home.php?select_db=MSH6'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_InSiGHT-MSH6',
                name: 'LOVD - InSiGHT MSH6',
                only_for_genes: [7329],
                url_for_genes: {
                    '7329': 'https://insight-database.org/#tabs-5'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'UMD-MSH6',
                name: 'UMD',
                only_for_genes: [7329],
                url_for_genes: {
                    '7329': 'http://www.umd.be/MSH6/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-MSH6',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [7329],
                url_for_genes: {
                    '7329':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=MSH6'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-MSH6',
                name: 'X - LOVD - Shared MSH6 (not in use)',
                only_for_genes: [7329],
                url_for_genes: {
                    '7329': 'https://databases.lovd.nl/shared/view/MSH6'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_InSiGHT-MUTYH',
                name: 'LOVD - InSiGHT MUTYH',
                only_for_genes: [7527],
                url_for_genes: {
                    '7527': 'https://insight-database.org/#tabs-8'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'UMD-MUTYH',
                name: 'UMD',
                only_for_genes: [7527],
                url_for_genes: {
                    '7527': 'http://www.umd.be/MUTYH/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-MUTYH',
                name: 'X - LOVD - Shared MUTYH (not in use)',
                only_for_genes: [7527],
                url_for_genes: {
                    '7527': 'https://databases.lovd.nl/shared/view/MUTYH'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-PALB2',
                name: 'LOVD - Shared PALB2',
                only_for_genes: [26144],
                url_for_genes: {
                    '26144': 'https://databases.lovd.nl/shared/view/PALB2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-PALB2',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [26144],
                url_for_genes: {
                    '26144':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=PALB2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_hci_priors-PMS2',
                name: 'LOVD hci priors',
                only_for_genes: [9122],
                url_for_genes: {
                    '9122': 'http://hci-lovd.hci.utah.edu/home.php?select_db=PMS2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_InSiGHT-PMS2',
                name: 'LOVD - InSiGHT PMS2',
                only_for_genes: [9122],
                url_for_genes: {
                    '9122': 'https://insight-database.org/#tabs-6'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-PMS2',
                name: 'X - LOVD - Shared PMS2 (not in use)',
                only_for_genes: [9122],
                url_for_genes: {
                    '9122': 'https://databases.lovd.nl/shared/view/PMS2'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-POLD1',
                name: 'LOVD - Shared POLD1',
                only_for_genes: [9175],
                url_for_genes: {
                    '9175': 'https://databases.lovd.nl/shared/view/POLD1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-POLE',
                name: 'LOVD - Shared POLE',
                only_for_genes: [9177],
                url_for_genes: {
                    '9177': 'https://databases.lovd.nl/shared/view/POLE'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared -PTEN',
                name: 'LOVD - Shared PTEN',
                only_for_genes: [9588],
                url_for_genes: {
                    '9588': 'https://databases.lovd.nl/shared/view/PTEN'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_whole_genome-PTEN',
                name: 'LOVD whole genome',
                only_for_genes: [9588],
                url_for_genes: {
                    '9588': 'http://databases.lovd.nl/whole_genome/view/PTEN'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-PTEN',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [9588],
                url_for_genes: {
                    '9588':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=PTEN'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_lohmann-RB1',
                name: 'LOVD lohmann',
                only_for_genes: [9884],
                url_for_genes: {
                    '9884':
                        'http://rb1-lsdb.d-lohmann.de/variants.php?action=search_unique&select_db=RB1'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-SDHB',
                name: 'LOVD - Shared SDHB',
                only_for_genes: [10681],
                url_for_genes: {
                    '10681': 'https://databases.lovd.nl/shared/view/SDHB'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-SDHD',
                name: 'LOVD - Shared SDHD',
                only_for_genes: [10683],
                url_for_genes: {
                    '10683': 'https://databases.lovd.nl/shared/view/SDHD'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'ARUP-SMAD4',
                name: 'ARUP',
                only_for_genes: [6770],
                url_for_genes: {
                    '6770': 'http://arup.utah.edu/database/SMAD4/SMAD4_display.php'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-SMAD4',
                name: 'LOVD - Shared SMAD4',
                only_for_genes: [6770],
                url_for_genes: {
                    '6770': 'https://databases.lovd.nl/shared/view/SMAD4'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-STK11',
                name: 'LOVD - Shared STK11',
                only_for_genes: [11389],
                url_for_genes: {
                    '11389': 'https://databases.lovd.nl/shared/view/STK11'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-STK11',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [11389],
                url_for_genes: {
                    '11389':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=STK11'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'IARC-TP53',
                name: 'IARC',
                only_for_genes: [11998],
                url_for_genes: {
                    '11998': 'http://p53.iarc.fr/TP53GeneVariations.aspx'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_shared-TP53',
                name: 'LOVD - Shared TP53',
                only_for_genes: [11998],
                url_for_genes: {
                    '11998': 'https://databases.lovd.nl/shared/view/TP53'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'TP53-web-site',
                name: 'The TP53 Web Site',
                only_for_genes: [11998],
                url_for_genes: {
                    '11998': 'http://p53.fr/download-the-database'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'UMD-VHL',
                name: 'UMD',
                only_for_genes: [12687],
                url_for_genes: {
                    '12687': 'http://www.umd.be/VHL/'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'VHLdb-VHL',
                name: 'VHLdb',
                only_for_genes: [12687],
                url_for_genes: {
                    '12687': 'http://vhldb.bio.unipd.it/mutations'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'LOVD_genomed_China-VHL',
                name: 'X - LOVD genomed China (not in use)',
                only_for_genes: [12687],
                url_for_genes: {
                    '12687':
                        'http://www.genomed.org/lovd2/variants.php?action=search_unique&select_db=VHL'
                },
                options: [
                    ['Pathogenic', 'pathogenic'],
                    ['Likely pathogenic', 'likely_pathogenic'],
                    ['Uncertain significance', 'uncertain_significance'],
                    ['Likely benign', 'likely_benign'],
                    ['Benign', 'benign'],
                    ['Conflicting', 'conflicting'],
                    ['Indirectly relevant', 'indirectly_relevant'],
                    ['Nothing found', 'none_found'],
                    ['Other', 'other']
                ]
            },
            {
                key: 'other_extdb',
                name: 'Other',
                text: true
            }
        ],
        prediction: [
            {
                key: 'ortholog_conservation',
                name: 'Ortholog conservation',
                options: [['Conserved', 'conserved'], ['Non-conserved', 'non-conserved']]
            },
            {
                key: 'paralog_conservation',
                name: 'Paralog conservation',
                options: [['Conserved', 'conserved'], ['Non-conserved', 'non-conserved']]
            },
            {
                key: 'dna_conservation',
                name: 'DNA conservation',
                options: [['Conserved', 'conserved'], ['Non-conserved', 'non-conserved']]
            },
            {
                key: 'domain',
                name: 'Domain',
                options: [
                    ['Critical functional domain', 'critical_domain'],
                    ['Critical functional amino acid', 'critical_site']
                ]
            },
            {
                key: 'repeat',
                name: 'Repeat',
                options: [['Repeat region', 'repeat'], ['Non-repeat region', 'non_repeat']]
            },
            {
                key: 'splice_Effect_manual',
                name: 'Splice site effect',
                options: [
                    ['Splice site lost', 'predicted_lost'],
                    ['De novo splice site', 'de_novo'],
                    ['No splice site effect', 'no_effect']
                ]
            }
        ]
    }
}

const testAlleleState = {
    2118: {
        change_to: 'T',
        genome_reference: 'GRCh37',
        chromosome: '13',
        vcf_alt: 'T',
        open_end_position: 32890607,
        change_from: 'G',
        vcf_ref: 'G',
        start_position: 32890606,
        vcf_pos: 32890607,
        change_type: 'SNP',
        id: 2118,
        samples: [
            {
                sex: null,
                father_id: null,
                identifier: 'brca_sample_1',
                sample_type: 'HTS',
                proband: true,
                family_id: null,
                mother_id: null,
                sibling_id: null,
                affected: true,
                id: 7,
                date_deposited: '2019-06-17T11:00:40.627960+00:00',
                genotype: {
                    variant_quality: 5000,
                    id: 6088,
                    filter_status: 'PASS',
                    sequencing_depth: 187,
                    type: 'Heterozygous',
                    genotype_quality: 99,
                    allele_depth: {
                        T: 80,
                        'REF (G)': 107
                    },
                    multiallelic: false,
                    allele_ratio: 0.42780748663101603,
                    needs_verification: false,
                    needs_verification_checks: {
                        snp: true,
                        pass: true,
                        qual: true,
                        dp: true,
                        allele_ratio: true,
                        hts: true
                    },
                    formatted: 'G/T'
                }
            }
        ],
        annotation: {
            external: {
                HGMD: {
                    tag: 'DM',
                    codon: 4,
                    acc_num: 'CM082514',
                    disease: 'Breast and/or ovarian cancer'
                },
                CLINVAR: {
                    items: [
                        {
                            rcv: 'SCV000296805',
                            submitter: 'GeneKor MSA',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '01/11/2017',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000323955',
                            submitter: 'ENIGMA',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '18/10/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'RCV000257718',
                            submitter: '',
                            traitnames: 'Breast-ovarian cancer, familial 2',
                            variant_id: '51063',
                            last_evaluated: '18/10/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'RCV000239090',
                            submitter: '',
                            traitnames: 'not provided',
                            variant_id: '51063',
                            last_evaluated: '01/11/2017',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000326495',
                            submitter: 'CIMBA',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '02/10/2015',
                            clinical_significance_descr: 'Pathogenic'
                        }
                    ],
                    variant_id: 51063,
                    variant_description: 'reviewed by expert panel'
                }
            },
            prediction: {},
            references: [
                {
                    sources: ['HGMD'],
                    pubmed_id: 17453335,
                    source_info: {
                        HGMD: 'Primary literature report. No comments.'
                    }
                }
            ],
            frequencies: {},
            transcripts: [
                {
                    exon: '2/27',
                    HGVSc: 'c.10G>T',
                    HGVSp: 'p.Gly4Ter',
                    dbsnp: ['rs397507571'],
                    codons: 'Gga/Tga',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    protein: 'NP_000050.2',
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.10G>T',
                    amino_acids: 'G/*',
                    consequences: ['stop_gained'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 0,
                    coding_region_distance: 0
                },
                {
                    dbsnp: ['rs397507571'],
                    strand: -1,
                    symbol: 'ZAR1L',
                    hgnc_id: 37116,
                    transcript: 'NM_001136571.1',
                    consequences: ['upstream_gene_variant'],
                    in_last_exon: 'no',
                    is_canonical: true
                }
            ],
            worst_consequence: ['NM_000059.3'],
            filtered_transcripts: ['NM_000059.3'],
            annotation_id: 2122,
            schema_version: 1,
            filtered: [
                {
                    exon: '2/27',
                    HGVSc: 'c.10G>T',
                    HGVSp: 'p.Gly4Ter',
                    dbsnp: ['rs397507571'],
                    codons: 'Gga/Tga',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    protein: 'NP_000050.2',
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.10G>T',
                    amino_acids: 'G/*',
                    consequences: ['stop_gained'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 0,
                    coding_region_distance: 0
                }
            ]
        },
        tags: ['has_references'],
        urls: {
            exac: 'http://exac.broadinstitute.org/variant/13-32890607-G-T',
            '1000g':
                'http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=13:32890607-32890607',
            ensembl:
                'http://grch37.ensembl.org/Homo_sapiens/Location/View?r=13%3A32890607-32890607',
            gnomad: 'http://gnomad.broadinstitute.org/region/13-32890597-32890617',
            hgmd: 'https://portal.biobase-international.com/hgmd/pro/mut.php?accession=CM082514',
            clinvar: 'https://www.ncbi.nlm.nih.gov/clinvar/variation/51063'
        },
        formatted: {
            hgvsg: 'g.32890607G>T',
            alamut: 'Chr13(GRCh37):g.32890607G>T',
            genomicPosition: '13:32890607',
            display: 'BRCA2 c.10G>T',
            sampleType: 'H',
            inheritance: 'AD'
        },
        links: {
            workflow:
                '/workflows/variants/GRCh37/13-32890607-G-T?gp_name=HBOC&gp_version=v01&allele_id=2118'
        }
    },
    2119: {
        change_to: '',
        genome_reference: 'GRCh37',
        chromosome: '13',
        vcf_alt: 'G',
        open_end_position: 32890647,
        change_from: 'AC',
        vcf_ref: 'GAC',
        start_position: 32890645,
        vcf_pos: 32890645,
        change_type: 'del',
        id: 2119,
        samples: [
            {
                sex: null,
                father_id: null,
                identifier: 'brca_sample_1',
                sample_type: 'HTS',
                proband: true,
                family_id: null,
                mother_id: null,
                sibling_id: null,
                affected: true,
                id: 7,
                date_deposited: '2019-06-17T11:00:40.627960+00:00',
                genotype: {
                    variant_quality: 5000,
                    id: 6089,
                    filter_status: 'PASS',
                    sequencing_depth: 187,
                    type: 'Heterozygous',
                    genotype_quality: 99,
                    allele_depth: {
                        G: 80,
                        'REF (GAC)': 107
                    },
                    multiallelic: false,
                    allele_ratio: 0.42780748663101603,
                    needs_verification: true,
                    needs_verification_checks: {
                        snp: false,
                        pass: true,
                        qual: true,
                        dp: true,
                        allele_ratio: true,
                        hts: true
                    },
                    formatted: 'AC/-'
                }
            }
        ],
        annotation: {
            external: {
                HGMD: {
                    tag: 'DM',
                    codon: 16,
                    acc_num: 'CD961847',
                    disease: 'Breast cancer'
                },
                CLINVAR: {
                    items: [
                        {
                            rcv: 'RCV000131871',
                            submitter: '',
                            traitnames: 'Hereditary cancer-predisposing syndrome',
                            variant_id: '51814',
                            last_evaluated: '12/12/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000279262',
                            submitter: 'GeneDx',
                            traitnames: 'Not Provided',
                            variant_id: '',
                            last_evaluated: '21/01/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000282398',
                            submitter: 'ENIGMA',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '22/04/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'RCV000113063',
                            submitter: '',
                            traitnames: 'Breast-ovarian cancer, familial 2',
                            variant_id: '51814',
                            last_evaluated: '22/04/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000694829',
                            submitter: 'Integrated Genetics/Laboratory Corporation of America',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '06/01/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000327129',
                            submitter: 'CIMBA',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '02/10/2015',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000186926',
                            submitter: 'Ambry Genetics',
                            traitnames: 'Hereditary cancer-predisposing syndrome',
                            variant_id: '',
                            last_evaluated: '23/09/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000146071',
                            submitter: 'BIC (BRCA2)',
                            traitnames: 'Breast-ovarian cancer, familial 2',
                            variant_id: '',
                            last_evaluated: '29/05/2002',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'RCV000219019',
                            submitter: '',
                            traitnames: 'not provided',
                            variant_id: '51814',
                            last_evaluated: '21/01/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000683670',
                            submitter: 'Color Genomics, Inc.',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '12/12/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000591655',
                            submitter:
                                'Department of Pathology and Laboratory Medicine,Sinai Health System',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '17/02/2015',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000587530',
                            submitter:
                                "Research Molecular Genetics Laboratory,Women's College Hospital, University of Toronto",
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '31/01/2014',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'RCV000496563',
                            submitter: '',
                            traitnames: 'Hereditary breast and ovarian cancer syndrome',
                            variant_id: '51814',
                            last_evaluated: '06/01/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'RCV000044604',
                            submitter: '',
                            traitnames: 'Familial cancer of breast',
                            variant_id: '51814',
                            last_evaluated: '01/07/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000296839',
                            submitter: 'GeneKor MSA',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '01/07/2016',
                            clinical_significance_descr: 'Pathogenic'
                        }
                    ],
                    variant_id: 51814,
                    variant_description: 'reviewed by expert panel'
                }
            },
            prediction: {},
            references: [
                {
                    sources: ['HGMD', 'CLINVAR'],
                    pubmed_id: 8589730,
                    source_info: {
                        HGMD: 'Primary literature report. aka 279delAC.'
                    }
                },
                {
                    sources: ['HGMD', 'CLINVAR'],
                    pubmed_id: 18607349,
                    source_info: {
                        HGMD: 'Functional characterisation. No comments.'
                    }
                },
                {
                    sources: ['HGMD'],
                    pubmed_id: 28324225,
                    source_info: {
                        HGMD: 'Additional phenotype. Breast and/or ovarian cancer.'
                    }
                },
                {
                    sources: ['CLINVAR'],
                    pubmed_id: 18092194,
                    source_info: {}
                },
                {
                    sources: ['CLINVAR'],
                    pubmed_id: 9245992,
                    source_info: {}
                },
                {
                    sources: ['CLINVAR'],
                    pubmed_id: 10070953,
                    source_info: {}
                },
                {
                    sources: ['CLINVAR'],
                    pubmed_id: 22430266,
                    source_info: {}
                },
                {
                    sources: ['CLINVAR'],
                    pubmed_id: 20927582,
                    source_info: {}
                }
            ],
            frequencies: {},
            transcripts: [
                {
                    exon: '2/27',
                    HGVSc: 'c.51_52delAC',
                    HGVSp: 'p.Arg18LeufsTer12',
                    codons: 'ACa/a',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    protein: 'NP_000050.2',
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.51_52delAC',
                    amino_acids: 'T/X',
                    consequences: ['frameshift_variant'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 0,
                    coding_region_distance: 0
                },
                {
                    strand: -1,
                    symbol: 'ZAR1L',
                    hgnc_id: 37116,
                    transcript: 'NM_001136571.1',
                    consequences: ['upstream_gene_variant'],
                    in_last_exon: 'no',
                    is_canonical: true
                }
            ],
            worst_consequence: ['NM_000059.3'],
            filtered_transcripts: ['NM_000059.3'],
            annotation_id: 2123,
            schema_version: 1,
            filtered: [
                {
                    exon: '2/27',
                    HGVSc: 'c.51_52delAC',
                    HGVSp: 'p.Arg18LeufsTer12',
                    codons: 'ACa/a',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    protein: 'NP_000050.2',
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.51_52delAC',
                    amino_acids: 'T/X',
                    consequences: ['frameshift_variant'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 0,
                    coding_region_distance: 0
                }
            ]
        },
        tags: ['has_references'],
        urls: {
            exac: 'http://exac.broadinstitute.org/variant/13-32890645-GAC-G',
            '1000g':
                'http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=13:32890646-32890647',
            ensembl:
                'http://grch37.ensembl.org/Homo_sapiens/Location/View?r=13%3A32890646-32890647',
            gnomad: 'http://gnomad.broadinstitute.org/region/13-32890635-32890657',
            hgmd: 'https://portal.biobase-international.com/hgmd/pro/mut.php?accession=CD961847',
            clinvar: 'https://www.ncbi.nlm.nih.gov/clinvar/variation/51814'
        },
        formatted: {
            hgvsg: 'g.32890646_32890647del',
            alamut: 'Chr13(GRCh37):g.32890646_32890647del',
            genomicPosition: '13:32890646-32890647',
            display: 'BRCA2 c.51_52delAC',
            sampleType: 'H',
            inheritance: 'AD'
        },
        links: {
            workflow:
                '/workflows/variants/GRCh37/13-32890645-GAC-G?gp_name=HBOC&gp_version=v01&allele_id=2119'
        }
    },
    2120: {
        change_to: 'A',
        genome_reference: 'GRCh37',
        chromosome: '13',
        vcf_alt: 'A',
        open_end_position: 32890666,
        change_from: 'T',
        vcf_ref: 'T',
        start_position: 32890665,
        vcf_pos: 32890666,
        change_type: 'SNP',
        id: 2120,
        samples: [
            {
                sex: null,
                father_id: null,
                identifier: 'brca_sample_1',
                sample_type: 'HTS',
                proband: true,
                family_id: null,
                mother_id: null,
                sibling_id: null,
                affected: true,
                id: 7,
                date_deposited: '2019-06-17T11:00:40.627960+00:00',
                genotype: {
                    variant_quality: 5000,
                    id: 6090,
                    filter_status: 'PASS',
                    sequencing_depth: 187,
                    type: 'Heterozygous',
                    genotype_quality: 99,
                    allele_depth: {
                        A: 80,
                        'REF (T)': 107
                    },
                    multiallelic: false,
                    allele_ratio: 0.42780748663101603,
                    needs_verification: false,
                    needs_verification_checks: {
                        snp: true,
                        pass: true,
                        qual: true,
                        dp: true,
                        allele_ratio: true,
                        hts: true
                    },
                    formatted: 'T/A'
                }
            }
        ],
        annotation: {
            external: {
                HGMD: {
                    tag: 'DM',
                    acc_num: 'CS087186',
                    disease: 'Breast cancer'
                },
                CLINVAR: {
                    items: [
                        {
                            rcv: 'RCV000113080',
                            submitter: '',
                            traitnames: 'Breast-ovarian cancer, familial 2',
                            variant_id: '52162',
                            last_evaluated: '24/02/2003',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000146095',
                            submitter: 'BIC (BRCA2)',
                            traitnames: 'Breast-ovarian cancer, familial 2',
                            variant_id: '',
                            last_evaluated: '24/02/2003',
                            clinical_significance_descr: 'Pathogenic'
                        }
                    ],
                    variant_id: 52162,
                    variant_description: 'no assertion criteria provided'
                }
            },
            prediction: {},
            references: [
                {
                    sources: ['HGMD'],
                    pubmed_id: 18092194,
                    source_info: {
                        HGMD: 'Primary literature report. Descr. in Suppl. Table 1 (online).'
                    }
                },
                {
                    sources: ['HGMD'],
                    pubmed_id: 25525159,
                    source_info: {
                        HGMD:
                            'Additional report. predicted to induce a large splicing change - Table S4.'
                    }
                }
            ],
            frequencies: {},
            transcripts: [
                {
                    HGVSc: 'c.67+2T>A',
                    dbsnp: ['rs81002885'],
                    intron: '2/26',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.67+2T>A',
                    consequences: ['splice_donor_variant'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 2,
                    coding_region_distance: null
                },
                {
                    dbsnp: ['rs81002885'],
                    strand: -1,
                    symbol: 'ZAR1L',
                    hgnc_id: 37116,
                    transcript: 'NM_001136571.1',
                    consequences: ['upstream_gene_variant'],
                    in_last_exon: 'no',
                    is_canonical: true
                }
            ],
            worst_consequence: ['NM_000059.3'],
            filtered_transcripts: ['NM_000059.3'],
            annotation_id: 2124,
            schema_version: 1,
            filtered: [
                {
                    HGVSc: 'c.67+2T>A',
                    dbsnp: ['rs81002885'],
                    intron: '2/26',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.67+2T>A',
                    consequences: ['splice_donor_variant'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 2,
                    coding_region_distance: null
                }
            ]
        },
        tags: ['has_references'],
        urls: {
            exac: 'http://exac.broadinstitute.org/variant/13-32890666-T-A',
            '1000g':
                'http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=13:32890666-32890666',
            ensembl:
                'http://grch37.ensembl.org/Homo_sapiens/Location/View?r=13%3A32890666-32890666',
            gnomad: 'http://gnomad.broadinstitute.org/region/13-32890656-32890676',
            hgmd: 'https://portal.biobase-international.com/hgmd/pro/mut.php?accession=CS087186',
            clinvar: 'https://www.ncbi.nlm.nih.gov/clinvar/variation/52162'
        },
        formatted: {
            hgvsg: 'g.32890666T>A',
            alamut: 'Chr13(GRCh37):g.32890666T>A',
            genomicPosition: '13:32890666',
            display: 'BRCA2 c.67+2T>A',
            sampleType: 'H',
            inheritance: 'AD'
        },
        links: {
            workflow:
                '/workflows/variants/GRCh37/13-32890666-T-A?gp_name=HBOC&gp_version=v01&allele_id=2120'
        }
    },
    2121: {
        change_to: 'T',
        genome_reference: 'GRCh37',
        chromosome: '13',
        vcf_alt: 'T',
        open_end_position: 32893218,
        change_from: 'A',
        vcf_ref: 'A',
        start_position: 32893217,
        vcf_pos: 32893218,
        change_type: 'SNP',
        id: 2121,
        samples: [
            {
                sex: null,
                father_id: null,
                identifier: 'brca_sample_1',
                sample_type: 'HTS',
                proband: true,
                family_id: null,
                mother_id: null,
                sibling_id: null,
                affected: true,
                id: 7,
                date_deposited: '2019-06-17T11:00:40.627960+00:00',
                genotype: {
                    variant_quality: 5000,
                    id: 6091,
                    filter_status: 'PASS',
                    sequencing_depth: 187,
                    type: 'Heterozygous',
                    genotype_quality: 99,
                    allele_depth: {
                        T: 80,
                        'REF (A)': 107
                    },
                    multiallelic: false,
                    allele_ratio: 0.42780748663101603,
                    needs_verification: false,
                    needs_verification_checks: {
                        snp: true,
                        pass: true,
                        qual: true,
                        dp: true,
                        allele_ratio: true,
                        hts: true
                    },
                    formatted: 'A/T'
                }
            }
        ],
        annotation: {
            external: {
                HGMD: {
                    tag: 'DM',
                    codon: 24,
                    acc_num: 'CM111973',
                    disease: 'Breast and/or ovarian cancer'
                },
                CLINVAR: {
                    items: [
                        {
                            rcv: 'SCV000678953',
                            submitter:
                                'ClinVar Staff, National Center for Biotechnology Information (NCBI)',
                            traitnames: 'Familial cancer of breast',
                            variant_id: '',
                            last_evaluated: '',
                            clinical_significance_descr: 'not provided'
                        },
                        {
                            rcv: 'RCV000577171',
                            submitter: '',
                            traitnames: 'Familial cancer of breast',
                            variant_id: '52303',
                            last_evaluated: '',
                            clinical_significance_descr: 'not provided'
                        }
                    ],
                    variant_id: 52303,
                    variant_description: 'no assertion criteria provided'
                }
            },
            prediction: {},
            references: [
                {
                    sources: ['HGMD', 'CLINVAR'],
                    pubmed_id: 21356067,
                    source_info: {
                        HGMD: 'Primary literature report. No comments.'
                    }
                },
                {
                    sources: ['HGMD'],
                    pubmed_id: 25525159,
                    source_info: {
                        HGMD:
                            'Additional report. predicted to induce a large splicing change - Table S4.'
                    }
                }
            ],
            frequencies: {
                ExAC: {
                    hom: {
                        G: 0,
                        AFR: 0,
                        AMR: 0,
                        EAS: 0,
                        FIN: 0,
                        NFE: 0,
                        OTH: 0,
                        SAS: 0
                    },
                    num: {
                        G: 119160,
                        AFR: 9500,
                        AMR: 11530,
                        EAS: 8550,
                        FIN: 6600,
                        NFE: 65594,
                        OTH: 894,
                        SAS: 16492
                    },
                    freq: {
                        G: 0.000016784155756965425,
                        AFR: 0,
                        AMR: 0,
                        EAS: 0,
                        FIN: 0.00030303030303030303,
                        NFE: 0,
                        OTH: 0,
                        SAS: 0
                    },
                    count: {
                        G: 2,
                        AFR: 0,
                        AMR: 0,
                        EAS: 0,
                        FIN: 2,
                        Het: 2,
                        NFE: 0,
                        OTH: 0,
                        SAS: 0
                    }
                },
                GNOMAD_EXOMES: {
                    hom: {
                        G: 0,
                        AFR: 0,
                        AMR: 0,
                        ASJ: 0,
                        EAS: 0,
                        FIN: 0,
                        NFE: 0,
                        OTH: 0,
                        SAS: 0,
                        Male: 0,
                        Female: 0
                    },
                    num: {
                        G: 245534,
                        AFR: 15200,
                        AMR: 33558,
                        ASJ: 9828,
                        EAS: 17220,
                        FIN: 22286,
                        NFE: 111296,
                        OTH: 5474,
                        SAS: 30672,
                        Male: 134558,
                        Female: 110976
                    },
                    freq: {
                        G: 0.000020363778539835625,
                        AFR: 0,
                        AMR: 0,
                        ASJ: 0,
                        EAS: 0,
                        FIN: 0.0002243560979987436,
                        NFE: 0,
                        OTH: 0,
                        SAS: 0,
                        Male: 0.000007431739472941036,
                        Female: 0.00003604382929642445
                    },
                    count: {
                        G: 5,
                        AFR: 0,
                        AMR: 0,
                        ASJ: 0,
                        EAS: 0,
                        FIN: 5,
                        NFE: 0,
                        OTH: 0,
                        SAS: 0,
                        Male: 1,
                        Female: 4
                    },
                    filter: {
                        G: ['PASS']
                    }
                }
            },
            transcripts: [
                {
                    exon: '3/27',
                    HGVSc: 'c.72A>T',
                    HGVSp: 'p.Leu24Phe',
                    dbsnp: ['rs397507909'],
                    codons: 'ttA/ttT',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    protein: 'NP_000050.2',
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.72A>T',
                    amino_acids: 'L/F',
                    consequences: ['missense_variant'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 0,
                    coding_region_distance: 0
                }
            ],
            worst_consequence: ['NM_000059.3'],
            filtered_transcripts: ['NM_000059.3'],
            annotation_id: 2125,
            schema_version: 1,
            filtered: [
                {
                    exon: '3/27',
                    HGVSc: 'c.72A>T',
                    HGVSp: 'p.Leu24Phe',
                    dbsnp: ['rs397507909'],
                    codons: 'ttA/ttT',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    protein: 'NP_000050.2',
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.72A>T',
                    amino_acids: 'L/F',
                    consequences: ['missense_variant'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 0,
                    coding_region_distance: 0
                }
            ]
        },
        tags: ['has_references'],
        urls: {
            exac: 'http://exac.broadinstitute.org/variant/13-32893218-A-T',
            '1000g':
                'http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=13:32893218-32893218',
            ensembl:
                'http://grch37.ensembl.org/Homo_sapiens/Location/View?r=13%3A32893218-32893218',
            gnomad: 'http://gnomad.broadinstitute.org/variant/13-32893218-A-T',
            hgmd: 'https://portal.biobase-international.com/hgmd/pro/mut.php?accession=CM111973',
            clinvar: 'https://www.ncbi.nlm.nih.gov/clinvar/variation/52303'
        },
        formatted: {
            hgvsg: 'g.32893218A>T',
            alamut: 'Chr13(GRCh37):g.32893218A>T',
            genomicPosition: '13:32893218',
            display: 'BRCA2 c.72A>T',
            sampleType: 'H',
            inheritance: 'AD'
        },
        links: {
            workflow:
                '/workflows/variants/GRCh37/13-32893218-A-T?gp_name=HBOC&gp_version=v01&allele_id=2121'
        }
    },
    2122: {
        change_to: 'T',
        genome_reference: 'GRCh37',
        chromosome: '13',
        vcf_alt: 'T',
        open_end_position: 32893243,
        change_from: 'G',
        vcf_ref: 'G',
        start_position: 32893242,
        vcf_pos: 32893243,
        change_type: 'SNP',
        id: 2122,
        samples: [
            {
                sex: null,
                father_id: null,
                identifier: 'brca_sample_1',
                sample_type: 'HTS',
                proband: true,
                family_id: null,
                mother_id: null,
                sibling_id: null,
                affected: true,
                id: 7,
                date_deposited: '2019-06-17T11:00:40.627960+00:00',
                genotype: {
                    variant_quality: 5000,
                    id: 6092,
                    filter_status: 'PASS',
                    sequencing_depth: 187,
                    type: 'Heterozygous',
                    genotype_quality: 99,
                    allele_depth: {
                        T: 80,
                        'REF (G)': 107
                    },
                    multiallelic: false,
                    allele_ratio: 0.42780748663101603,
                    needs_verification: false,
                    needs_verification_checks: {
                        snp: true,
                        pass: true,
                        qual: true,
                        dp: true,
                        allele_ratio: true,
                        hts: true
                    },
                    formatted: 'G/T'
                }
            }
        ],
        annotation: {
            external: {
                HGMD: {
                    tag: 'DM',
                    codon: 33,
                    acc_num: 'CM067653',
                    disease: 'Breast and/or ovarian cancer'
                },
                CLINVAR: {
                    items: [
                        {
                            rcv: 'SCV000324794',
                            submitter: 'ENIGMA',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '18/10/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'RCV000256555',
                            submitter: '',
                            traitnames: 'Breast-ovarian cancer, familial 2',
                            variant_id: '52900',
                            last_evaluated: '18/10/2016',
                            clinical_significance_descr: 'Pathogenic'
                        },
                        {
                            rcv: 'SCV000328170',
                            submitter: 'CIMBA',
                            traitnames: '',
                            variant_id: '',
                            last_evaluated: '02/10/2015',
                            clinical_significance_descr: 'Pathogenic'
                        }
                    ],
                    variant_id: 52900,
                    variant_description: 'reviewed by expert panel'
                }
            },
            prediction: {},
            references: [
                {
                    sources: ['HGMD'],
                    pubmed_id: 16760289,
                    source_info: {
                        HGMD: 'Primary literature report. No comments.'
                    }
                },
                {
                    sources: ['HGMD'],
                    pubmed_id: 16847550,
                    source_info: {
                        HGMD: 'Additional report. No comments.'
                    }
                },
                {
                    sources: ['HGMD'],
                    pubmed_id: 25525159,
                    source_info: {
                        HGMD:
                            'Additional report. predicted to induce a large splicing change - Table S4.'
                    }
                }
            ],
            frequencies: {},
            transcripts: [
                {
                    exon: '3/27',
                    HGVSc: 'c.97G>T',
                    HGVSp: 'p.Glu33Ter',
                    dbsnp: ['rs397508065'],
                    codons: 'Gaa/Taa',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    protein: 'NP_000050.2',
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.97G>T',
                    amino_acids: 'E/*',
                    consequences: ['stop_gained'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 0,
                    coding_region_distance: 0
                }
            ],
            worst_consequence: ['NM_000059.3'],
            filtered_transcripts: ['NM_000059.3'],
            annotation_id: 2126,
            schema_version: 1,
            filtered: [
                {
                    exon: '3/27',
                    HGVSc: 'c.97G>T',
                    HGVSp: 'p.Glu33Ter',
                    dbsnp: ['rs397508065'],
                    codons: 'Gaa/Taa',
                    strand: 1,
                    symbol: 'BRCA2',
                    hgnc_id: 1101,
                    protein: 'NP_000050.2',
                    transcript: 'NM_000059.3',
                    HGVSc_short: 'c.97G>T',
                    amino_acids: 'E/*',
                    consequences: ['stop_gained'],
                    in_last_exon: 'no',
                    is_canonical: true,
                    exon_distance: 0,
                    coding_region_distance: 0
                }
            ]
        },
        tags: ['has_references'],
        urls: {
            exac: 'http://exac.broadinstitute.org/variant/13-32893243-G-T',
            '1000g':
                'http://browser.1000genomes.org/Homo_sapiens/Location/View?db=core;r=13:32893243-32893243',
            ensembl:
                'http://grch37.ensembl.org/Homo_sapiens/Location/View?r=13%3A32893243-32893243',
            gnomad: 'http://gnomad.broadinstitute.org/region/13-32893233-32893253',
            hgmd: 'https://portal.biobase-international.com/hgmd/pro/mut.php?accession=CM067653',
            clinvar: 'https://www.ncbi.nlm.nih.gov/clinvar/variation/52900'
        },
        formatted: {
            hgvsg: 'g.32893243G>T',
            alamut: 'Chr13(GRCh37):g.32893243G>T',
            genomicPosition: '13:32893243',
            display: 'BRCA2 c.97G>T',
            sampleType: 'H',
            inheritance: 'AD'
        },
        links: {
            workflow:
                '/workflows/variants/GRCh37/13-32893243-G-T?gp_name=HBOC&gp_version=v01&allele_id=2122'
        }
    }
}

const testSidebarOrderByNull = {
    classified: {
        key: null,
        reverse: false
    },
    unclassified: {
        key: null,
        reverse: false
    },
    technical: {
        key: null,
        reverse: false
    },
    notRelevant: {
        key: null,
        reverse: false
    }
}

export { testUiConfig, testAlleleState, testSidebarOrderByNull }
