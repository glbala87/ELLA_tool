# coding=utf-8
from api.schemas import ClassificationSchema
from rule_engine.gre import GRE
from rule_engine.grc import ACMGClassifier2015
from mapping_rules import rules
import json

data = {
    "frequency": {
        "1000g": {
            "AA": 0.102587,
            "AFR": 0.05,
            "AMR": 0.19,
            "ASN": 0.37,
            "EA": 0.263256,
            "EUR": 0.23,
            "G": 0.2185
        },
        "ExAC": {
            "AFR": 0.10079704510108865,
            "AMR": 0.18944802368100297,
            "Adj": 0.24646677011897014,
            "EAS": 0.38011152416356875,
            "FIN": 0.19137466307277629,
            "G": 0.24313202452790292,
            "NFE": 0.2580812077676995,
            "OTH": 0.25925925925925924,
            "SAS": 0.2833209693372898
        }
    },
    "genomic": {
        "Conservation": "conserved"
    },
    "refassessment": {
        "ref_functional": "prot++",
        "ref_segregation": "segr++",
    },
    "transcript": {
        "BIC": [
            "Clinically important: yes"
        ],
        "InSight": [
            "Path: +/?"
        ],
        "VEP_Consequence": [
            "synonymous_variant"
        ],
        "HGVSc": "NM_000059.3:c.-26G>A",
        "Transcript": "NM_000059",
        "Transcript_version": "3",
        "Transcript_version_CLINVAR": "3",
        "Transcript_version_HGMD": "3"
    },
    
    "genepanel": {
        "inheritance": "autosomal_dominant",
        "last_exon": "last_exon_important",
        "hi_freq_cutoff": 0.01,
        "lo_freq_cutoff": 0.001,
        "disease_mode": "lof_missense"
    }
}

# Current example data:
data16nov2015 = {
                "external": {
                    "BIC": {
                        "Clinically_Important": "unknown"
                    }, 
                    "CLINVAR": {
                        "CLNDBN": "Familial_cancer_of_breast|Breast-ovarian_cancer\\x2c_familial_2", 
                        "CLNREVSTAT": "not|mult"
                    },
                    "HGMD": {
                        "acc_num": "CI126332", 
                        "codon": 1446, 
                        "disease": "Breast and/or ovarian cancer", 
                        "tag": "DM"
                    }
                }, 
                "frequencies": {
                    "1000g": {
                        "AA": 0.022323, 
                        "AFR": 0.03, 
                        "EA": 0.0, 
                        "G": 0.006
                    }, 
                    "ExAC": {
                        "AFR": 0.026535769828926904, 
                        "AMR": 0.0011259310583751948, 
                        "Adj": 0.0024023169384270265, 
                        "EAS": 0.0, 
                        "FIN": 0.0, 
                        "G": 0.0023518114644705576, 
                        "Het_AFR": 263, 
                        "Het_AMR": 13, 
                        "Het_EAS": 0, 
                        "Het_FIN": 0, 
                        "Het_NFE": 1, 
                        "Het_OTH": 0, 
                        "Het_SAS": 0, 
                        "Hom_AFR": 5, 
                        "Hom_AMR": 0, 
                        "Hom_EAS": 0, 
                        "Hom_FIN": 0, 
                        "Hom_NFE": 0, 
                        "Hom_OTH": 0, 
                        "Hom_SAS": 0, 
                        "NFE": 1.5055252777694137e-05, 
                        "OTH": 0.0, 
                        "SAS": 0.0
                    }
                }, 
                "genetic": None, 
                "references": [], 
                "transcripts": [
                    {
                        "Amino_acids": "P", 
                        "Consequence": [
                            "synonymous_variant"
                        ], 
                        "Existing_variation": [
                            "rs36060526"
                        ], 
                        "HGVSc": "NM_000059.3:c.3264T>C", 
                        "HGVSp": "NM_000059.3:c.3264T>C(p.=)", 
                        "STRAND": 1, 
                        "symbol": "BRCA2", 
                        "Transcript": "NM_000059", 
                        "Transcript_version": "3", 
                        "splice_Effect": "no_effect", 
                        "splice_Transcript_version": "3"
                    }            
            ]
        }

passed, nonpassed = GRE().query(rules, data)
print "PASSED: {}".format([(p.code, p.source) for p in passed])
print "NOT PASSED: {}".format([(p.code, p.source) for p in nonpassed])
classification = ACMGClassifier2015().classify(passed)
print "CLASSIFICATION: " + classification.classification
print "CLASSIFICATION INFO: " + classification.message
print "CLASSIFICATION CONTRIBUTORS: " + "[%s]" % ", ".join(map(str, [r.source+":"+r.code for r in classification.contributors]))
ret = dict()
ret["alleles"] = {0:classification}
ret["mapping_rules"] = None
print "CLASSIFICATION SERIALIZED: " + json.dumps(ClassificationSchema().dump(ret), indent=2, sort_keys=True)
