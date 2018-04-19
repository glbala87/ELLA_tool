# -*- coding: utf-8 -*-

import os
from .acmgconfig import acmgconfig
from .customannotationconfig import customannotationconfig

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


config = {
    "app": {
        "enable_igv": str2bool(os.environ.get("ENABLE_IGV", "false")),  # Disable by default for now
        "links_to_clipboard": str2bool(os.environ.get("OFFLINE_MODE", "true")),
        "non_production_warning": os.environ.get('NON_PRODUCTION_WARNING'),
        "user_confirmation_on_state_change": str2bool(os.environ.get("USER_CONFIRMATION_ON_STATE_CHANGE", "true")),
        "user_confirmation_to_discard_changes": str2bool(os.environ.get('USER_CONFIRMATION_TO_DISCARD_CHANGES', 'true')),
        "annotation_service": os.environ.get("ANNOTATION_SERVICE_URL", "http://localhost:6000"),
        "attachment_storage": os.environ.get("ATTACHMENT_STORAGE", None),
        "max_upload_size": 50*1024*1024, # 50 MB
    },
    "user": {
        "auth": {
            "password_expiry_days": 90,
            "password_minimum_length": 8,
            "password_match_groups": [".*[A-Z].*", ".*[a-z].*", ".*[0-9].*", ".*[^A-Za-z0-9].*"],
            "password_match_groups_descr": ["Uppercase letters [A-Z]", "Lowercase letters [a-z]", "Digits [0-9]", "Special characters"],
            "password_num_match_groups": 3
        },
        "user_config": {  # Default user config
            "overview": {
                "views": ["variants", "analyses-by-findings"]
            },
            "workflows": {
                "allele": {
                    "finalize_required_workflow_status": ['Interpretation', 'Review']  # Required current workflow status for allowing finalized
                },
                "analysis": {
                    "finalize_required_workflow_status": ['Not ready', 'Interpretation', 'Review', 'Medical review']
                }
            }
        }
    },
    "analysis": {
        "priority": {
            "display": {
                "1": "Normal",
                "2": "High",
                "3": "Urgent"
            }
        }
    },
    "annotation": {
        "clinvar": {
            "clinical_significance_status": {
                "criteria provided, conflicting interpretations": 1,
                "criteria provided, multiple submitters, no conflicts": 2,
                "criteria provided, single submitter": 1,
                "no assertion criteria provided": 0,
                "no assertion provided": 0,
                "practice guideline": 4,
                "reviewed by expert panel": 3,
            }
        }
    },
    "frequencies": {
        "view": {
            "groups": {
                "GNOMAD_GENOMES": [
                    "G",
                    "AFR",
                    "AMR",
                    "ASJ",
                    "EAS",
                    "FIN",
                    "NFE",
                    "OTH",
                    "SAS",
                ],
                "GNOMAD_EXOMES": [
                    "G",
                    "AFR",
                    "AMR",
                    "ASJ",
                    "EAS",
                    "FIN",
                    "NFE",
                    "OTH",
                    "SAS",
                ],
                "ExAC": [
                    "G",
                    "AFR",
                    "AMR",
                    "EAS",
                    "FIN",
                    "NFE",
                    "OTH",
                    "SAS",
                ],
                "1000g": [
                    "G",
                    "AMR",
                    "ASN",
                    "EUR",
                    "EAS",
                    "SAS"
                ],
                "esp6500": [
                    "AA",
                    "EA",
                ],
                "inDB": [
                    "OUSWES"
                ]
            },
            "precision": 6,  # Float precision (for strings)
            "scientific_threshold": 4,  # Convert to scientific notation for frequencies below 10**-x
            "indications_threshold": 10,
            "GNOMAD_GENOMES": {  # translations: the key is used to link/lookup other sources of information:
                "G": "TOT",
                "AFR": "AFR",
                "AMR": "LAT",
                "ASJ": "ASJ",
                "EAS": "EA",
                "FIN": "E(F)",
                "NFE": "E(NF)",
                "OTH": "OTH",
                "SAS": "SA",
            },
            "GNOMAD_EXOMES": {
                "G": "TOT",
                "AFR": "AFR",
                "AMR": "LAT",
                "ASJ": "ASJ",
                "EAS": "EA",
                "FIN": "E(F)",
                "NFE": "E(NF)",
                "OTH": "OTH",
                "SAS": "SA",
            },
            "ExAC": {
                "G": "TOT",
                "AFR": "AFR",
                "AMR": "LAT",
                "EAS": "EA",
                "FIN": "E(F)",
                "NFE": "E(NF)",
                "OTH": "OTH",
                "SAS": "SA",
            }
        }
    },
    "variant_criteria": {  # Config related to criterias for filtering/displaying variants
        # Region thresholds to use when filtering out intronic variants. Distance from exon start/end.
        "intronic_region": [-20, 6],  # Filters variants with -20 or +6 as intronic, e.g. c.123-21A>G and c.123+7T>C
        "freq_num_thresholds": {  # Specifies (optional) requirements for >= 'num' count for each freq
            "GNOMAD_GENOMES": {
                "G": 5000,
                "AFR": 5000,
                "AMR": 5000,
                "EAS": 5000,
                "FIN": 5000,
                "NFE": 5000,
                "OTH": 5000,
                "SAS": 5000
            },
            "GNOMAD_EXOMES": {
                "G": 5000,
                "AFR": 5000,
                "AMR": 5000,
                "EAS": 5000,
                "FIN": 5000,
                "NFE": 5000,
                "OTH": 5000,
                "SAS": 5000
            }

        },
        "genepanel_config": {  # Default config for genepanels
            "freq_cutoff_groups": {  # 'external'/'internal' references the groups under 'frequencies->groups' key below
                "AD": {
                    "external": {"hi_freq_cutoff": 0.005, "lo_freq_cutoff": 0.001},
                    "internal": {"hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0}
                },
                "default": {
                    "external": {"hi_freq_cutoff": 0.01, "lo_freq_cutoff": 1.0},
                    "internal": {"hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0}
                }
            },
            "disease_mode": "ANY",
            "last_exon_important": "LEI",
        },
        "frequencies": {  # Frequency groups to be used as part of cutoff calculation (and by extension class 1 filtering)
            "groups": {
                "external": {
                    "GNOMAD_GENOMES": [
                        "G",
                        "AFR",
                        "AMR",
                        "EAS",
                        "FIN",
                        "NFE",
                        "OTH",
                        "SAS"
                    ],
                    "GNOMAD_EXOMES": [
                        "G",
                        "AFR",
                        "AMR",
                        "EAS",
                        "FIN",
                        "NFE",
                        "OTH",
                        "SAS"
                    ]
                },
                "internal": {
                    "inDB": [
                        'AF',  # TODO: Deprecated. Remove once in production
                        'OUSWES'
                    ]
                }
            }
        }
    },
    "classification": {
        "gene_groups": {
            "MMR": ["MLH1", "MSH2", "MSH6", "PMS2"]  # Mismatch repair group
        },
        "options": [  # Also defines sorting order
            # Adding a class needs ENUM update in DB, along with migration
            {
                "name": "Unclassified",
                "value": "U",
            },
            {
                "name": "Class 1",
                "value": "1"
            },
            {
                "name": "Class 2",
                "value": "2",
                "outdated_after_days": 180, # Marked as outdated after N number of days
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 3",
                "value": "3",
                "outdated_after_days": 180,
                "include_report": True,  # Include in report by default
                "include_analysis_with_findings": True,
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 4",
                "value": "4",
                "outdated_after_days": 180,
                "include_report": True,
                "include_analysis_with_findings": True,
                "exclude_filtering_existing_assessment": True
            },
            {
                "name": "Class 5",
                "value": "5",
                "outdated_after_days": 365,
                "include_report": True,
                "include_analysis_with_findings": True,
                "exclude_filtering_existing_assessment": True
            }
        ]
    },

    "report": {
        "classification_text": {
            "5": "Sykdomsgivende variant",
            "4": "Sannsynlig sykdomsgivende variant",
            "3": "Variant med usikker betydning",
            "2": "Sannsynlig ikke sykdomsgivende variant",
            "1": "Ikke sykdomsgivende variant",
        }
    },
    "transcripts": {
        # In order of severity, high to low. Used for searching for worst consequence.
        "consequences": [
            "transcript_ablation",
            "splice_donor_variant",
            "splice_acceptor_variant",
            "stop_gained",
            "frameshift_variant",
            "start_lost",
            "initiator_codon_variant",
            "stop_lost",
            "inframe_insertion",
            "inframe_deletion",
            "missense_variant",
            "protein_altering_variant",
            "transcript_amplification",
            "splice_region_variant",
            "incomplete_terminal_codon_variant",
            "synonymous_variant",
            "stop_retained_variant",
            "coding_sequence_variant",
            "mature_miRNA_variant",
            "5_prime_UTR_variant",
            "3_prime_UTR_variant",
            "non_coding_transcript_exon_variant",
            "non_coding_transcript_variant",
            "intron_variant",
            "NMD_transcript_variant",
            "upstream_gene_variant",
            "downstream_gene_variant",
            "TFBS_ablation",
            "TFBS_amplification",
            "TF_binding_site_variant",
            "regulatory_region_variant",
            "regulatory_region_ablation",
            "regulatory_region_amplification",
            "feature_elongation",
            "feature_truncation",
            "intergenic_variant"
        ],
        # None includes all transcripts available in annotation
        # Will also include transcripts defined in genepanel
        "inclusion_regex": "NM_.*",
    },
    "igv": {
        "reference": {
            "fastaURL": "api/v1/igv/human_g1k_v37_decoy.fasta" if os.environ.get('OFFLINE_MODE') else "//igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta",
            "cytobandURL": "api/v1/igv/cytoBand.txt" if os.environ.get('OFFLINE_MODE') else "//igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt"
        },
        "tracks": {
            "gencode": "api/v1/igv/gencode.v18.collapsed.bed" if os.environ.get('OFFLINE_MODE') else "//igv.broadinstitute.org/annotations/hg19/genes/gencode.v18.collapsed.bed",
        },
        # Files permitted accessible on /igv/<file> resource, relative to $IGV_DATA env
        "valid_resource_files": [
            'gencode.v18.collapsed.bed',
            'gencode.v18.collapsed.bed.idx',
            'cytoBand.txt',
            'human_g1k_v37_decoy.fasta',
            'human_g1k_v37_decoy.fasta.fai'
        ]
    },
    'deposit': {
        'postprocess': [
            {
                'name': '^Diag-EKG.*',
                'type': 'analysis',
                'methods': ['analysis_not_ready_findings']
            }
        ]
    }
}

config.update({
    'acmg': acmgconfig,
    'custom_annotation': customannotationconfig
})
