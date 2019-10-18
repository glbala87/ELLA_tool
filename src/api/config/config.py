# -*- coding: utf-8 -*-

import os
import copy
from .acmgconfig import acmgconfig
from .customannotationconfig import customannotationconfig


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


config = {
    "app": {
        # Disable by default for now
        "links_to_clipboard": str2bool(os.environ.get("OFFLINE_MODE", "true")),
        "non_production_warning": os.environ.get("NON_PRODUCTION_WARNING"),
        "annotation_service": os.environ.get("ANNOTATION_SERVICE_URL", "http://localhost:6000"),
        "attachment_storage": os.environ.get("ATTACHMENT_STORAGE", None),
        "max_upload_size": 50 * 1024 * 1024,  # 50 MB
    },
    "user": {
        "auth": {
            "password_expiry_days": 90,
            "password_minimum_length": 8,
            "password_match_groups": [".*[A-Z].*", ".*[a-z].*", ".*[0-9].*", ".*[^A-Za-z0-9].*"],
            "password_match_groups_descr": [
                "Uppercase letters [A-Z]",
                "Lowercase letters [a-z]",
                "Digits [0-9]",
                "Special characters",
            ],
            "password_num_match_groups": 3,
        },
        "user_config": {
            # Default user config
            # Is _shallow_ merged with usergroup's and user's config at runtime
            "overview": {"views": ["variants", "analyses-by-findings"]},
            "workflows": {
                "allele": {
                    "finalize_requirements": {
                        # Workflow statuses allowing finalization
                        "workflow_status": ["Interpretation", "Review"]
                    }
                },
                "analysis": {
                    "finalize_requirements": {
                        "workflow_status": [
                            "Not ready",
                            "Interpretation",
                            "Review",
                            "Medical review",
                        ],
                        "allow_notrelevant": False,
                        "allow_technical": True,
                        "allow_unclassified": False,  # allow_unclassified implies allow_technical and allow_notrelevant
                    }
                },
            },
            "acmg": {
                "frequency": {
                    "thresholds": {  # 'external'/'internal' references the groups under 'frequency->groups'
                        "AD": {
                            "external": {"hi_freq_cutoff": 0.005, "lo_freq_cutoff": 0.001},
                            "internal": {"hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0},
                        },
                        "default": {
                            "external": {"hi_freq_cutoff": 0.01, "lo_freq_cutoff": 1.0},
                            "internal": {"hi_freq_cutoff": 0.05, "lo_freq_cutoff": 1.0},
                        },
                    },
                    "num_thresholds": {
                        "GNOMAD_GENOMES": {
                            "G": 5000,
                            "AFR": 5000,
                            "AMR": 5000,
                            "EAS": 5000,
                            "FIN": 5000,
                            "NFE": 5000,
                            "OTH": 5000,
                            "SAS": 5000,
                        },
                        "GNOMAD_EXOMES": {
                            "G": 5000,
                            "AFR": 5000,
                            "AMR": 5000,
                            "EAS": 5000,
                            "FIN": 5000,
                            "NFE": 5000,
                            "OTH": 5000,
                            "SAS": 5000,
                        },
                    },
                },
                "disease_mode": "ANY",
                "last_exon_important": "LEI",
            },
            "interpretation": {"autoIgnoreReferencePubmedIds": []},
        },
    },
    "analysis": {
        "priority": {"display": {"1": "Normal", "2": "High", "3": "Urgent"}},
        "sidebar": {
            "full": {
                "columns": [],
                "classification_options": {
                    "unclassified": [],
                    "classified": [],
                    "not_relevant": [],
                    "technical": [],
                },
                "comment_type": {
                    "unclassified": None,
                    "classified": None,
                    "not_relevant": None,
                    "technical": None,
                },
                "shade_multiple_in_gene": True,
            },
            "quick": {
                "columns": ["qual", "dp", "ratio", "hi-freq", "hi-count", "external"],
                "classification_options": {
                    "unclassified": ["technical", "notrelevant", "classu", "class2"],
                    "classified": [],
                    "not_relevant": [],
                    "technical": [],
                },
                "comment_type": {
                    "unclassified": None,
                    "classified": "evaluation",
                    "not_relevant": "analysis",
                    "technical": "analysis",
                },
                "narrow_comment": False,
                "shade_multiple_in_gene": True,
            },
            "visual": {
                "columns": ["qual", "ratio"],
                "classification_options": {
                    "unclassified": ["technical"],
                    "classified": ["technical"],
                    "not_relevant": [],
                    "technical": [],
                },
                "comment_type": {
                    "unclassified": None,
                    "classified": None,
                    "not_relevant": "analysis",
                    "technical": "analysis",
                },
                "narrow_comment": True,
                "shade_multiple_in_gene": True,
            },
            "report": {
                "columns": [],
                "classification_options": {
                    "unclassified": [],
                    "classified": [],
                    "not_relevant": [],
                    "technical": [],
                },
                "comment_type": {
                    "unclassified": None,
                    "classified": None,
                    "not_relevant": None,
                    "technical": None,
                },
                "shade_multiple_in_gene": True,
            },
            "list": {
                "columns": ["qual", "dp", "ratio", "hi-freq", "hi-count", "external"],
                "classification_options": {
                    "unclassified": [],
                    "classified": [],
                    "not_relevant": [],
                    "technical": [],
                },
                "comment_options": {
                    "unclassified": None,
                    "classified": None,
                    "not_relevant": None,
                    "technical": None,
                },
                "shade_multiple_in_gene": False,
            },
        },
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
        "groups": {
            "external": {
                "GNOMAD_GENOMES": ["G", "AFR", "AMR", "EAS", "FIN", "NFE", "OTH", "SAS"],
                "GNOMAD_EXOMES": ["G", "AFR", "AMR", "EAS", "FIN", "NFE", "OTH", "SAS"],
            },
            "internal": {"inDB": ["OUSWES"]},
        },
        "view": {
            "groups": {
                "GNOMAD_GENOMES": ["G", "AFR", "AMR", "ASJ", "EAS", "FIN", "NFE", "OTH", "SAS"],
                "GNOMAD_EXOMES": ["G", "AFR", "AMR", "ASJ", "EAS", "FIN", "NFE", "OTH", "SAS"],
                "ExAC": ["G", "AFR", "AMR", "EAS", "FIN", "NFE", "OTH", "SAS"],
                "1000g": ["G", "AMR", "ASN", "EUR", "EAS", "SAS"],
                "esp6500": ["AA", "EA"],
                "inDB": ["OUSWES"],
            },
            "precision": 6,  # Float precision (for strings)
            # Convert to scientific notation for frequencies below 10**-x
            "scientific_threshold": 4,
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
            },
        },
    },
    "filter": {
        # These defaults will be used as base when applying any FilterConfig's filter configurations
        # The configs are shallow merged on top of the following defaults
        "default_filter_config": {
            "region": {"splice_region": [-20, 6], "utr_region": [0, 0]},
            "frequency": {
                "num_thresholds": {
                    "GNOMAD_GENOMES": {
                        "G": 5000,
                        "AFR": 5000,
                        "AMR": 5000,
                        "EAS": 5000,
                        "FIN": 5000,
                        "NFE": 5000,
                        "OTH": 5000,
                        "SAS": 5000,
                    },
                    "GNOMAD_EXOMES": {
                        "G": 5000,
                        "AFR": 5000,
                        "AMR": 5000,
                        "EAS": 5000,
                        "FIN": 5000,
                        "NFE": 5000,
                        "OTH": 5000,
                        "SAS": 5000,
                    },
                },
                "thresholds": {
                    "AD": {"external": 0.005, "internal": 0.05},
                    "default": {"external": 0.01, "internal": 0.05},
                },
            },
            "inheritancemodel": {},
            "quality": {},
            "segregation": {},
            "external": {},
            "classification": {},
            "ppy": {},
            "consequence": {},
        }
    },
    "classification": {
        "gene_groups": {"MMR": ["MLH1", "MSH2", "MSH6", "PMS2"]},  # Mismatch repair group
        "options": [  # Also defines sorting order
            # Adding a class needs ENUM update in DB, along with migration
            {"name": "Class U", "value": "U"},
            {"name": "Class 1", "value": "1"},
            {
                "name": "Class 2",
                "value": "2",
                "outdated_after_days": 365,
            },  # Marked as outdated after N number of days
            {
                "name": "Class 3",
                "value": "3",
                "outdated_after_days": 180,
                "include_report": True,  # Include in report by default
                "include_analysis_with_findings": True,
            },
            {
                "name": "Class 4",
                "value": "4",
                "outdated_after_days": 180,
                "include_report": True,
                "include_analysis_with_findings": True,
            },
            {
                "name": "Class 5",
                "value": "5",
                "outdated_after_days": 365,
                "include_report": True,
                "include_analysis_with_findings": True,
            },
            {"name": "Drug response", "value": "DR"},
        ],
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
            "intergenic_variant",
        ],
        # None includes all transcripts available in annotation
        # Will also include transcripts defined in genepanel
        "inclusion_regex": "NM_.*",
    },
    "igv": {
        "reference": {
            "fastaURL": "api/v1/igv/human_g1k_v37_decoy.fasta"
            if str2bool(os.environ.get("OFFLINE_MODE", ""))
            else "//igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta",
            "cytobandURL": "api/v1/igv/cytoBand.txt"
            if str2bool(os.environ.get("OFFLINE_MODE", ""))
            else "//igv.broadinstitute.org/genomes/seq/b37/b37_cytoband.txt",
        },
        # Files permitted accessible on /igv/<file> resource, relative to $IGV_DATA env
        "valid_resource_files": [
            "cytoBand.txt",
            "human_g1k_v37_decoy.fasta",
            "human_g1k_v37_decoy.fasta.fai",
        ],
    },
    "import": {
        "automatic_deposit_with_sample_id": False,
        "preimport_script": os.path.join(
            os.path.split(os.path.abspath(__file__))[0], "../../../scripts/preimport.py"
        ),
    },
}

config["acmg"] = acmgconfig
config["custom_annotation"] = customannotationconfig


def get_user_config(app_config, usergroup_config, user_config):
    # Use json instead of copy.deepcopy for performance
    merged_config = copy.deepcopy(app_config["user"]["user_config"])
    merged_config.update(copy.deepcopy(usergroup_config))
    merged_config.update(copy.deepcopy(user_config))
    return merged_config


def get_filter_config(app_config, filter_config):
    """
    filter_config is shallow merged with the default
    provided in application config.
    """

    merged_filters = list()
    assert "filters" in filter_config
    for filter_step in filter_config["filters"]:

        base_config = dict(app_config["filter"]["default_filter_config"][filter_step["name"]])
        base_config.update(filter_step.get("config", {}))

        filter_exceptions = []
        for filter_exception in filter_step.get("exceptions", []):
            filter_exceptions.append(
                {"name": filter_exception["name"], "config": filter_exception.get("config", {})}
            )

        merged_filters.append(
            {"name": filter_step["name"], "config": base_config, "exceptions": filter_exceptions}
        )
    merged_filters = copy.deepcopy(merged_filters)
    return merged_filters
