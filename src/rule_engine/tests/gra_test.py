import unittest
from ..gra import GRA
from ..grl import GRL
from ..grm import GRM


class GraTest(unittest.TestCase):

    jsonrules = [
        {
            "code": "BP1",
            "rule": {"transcript.Consequence": {"$in": ["missense_variant", "synonymous_variant"]}},
        },
        {"code": "BP1", "rule": {"transcript.Conseq": {"$in": ["missense_var", "synonymous_var"]}}},
        {"code": "BP2", "rule": {"transcript.splice.effect": "de_novo"}},
        {
            "code": "rBP7-1",
            "rule": {
                "transcript.Consequence": {
                    "$in": [
                        "stop_retained_variant",
                        "5_prime_UTR_variant",
                        "3_prime_UTR_variant",
                        "non_coding_exon_variant",
                        "nc_transcript_variant",
                        "intron_variant",
                        "upstream_gene_variant",
                        "downstream_gene_variant",
                        "intergenic_variant",
                        "synonymous_variant",
                    ]
                }
            },
        },
        {"code": "rBP7-2", "rule": {"genomic.Conservation": "non_conserved"}},
        {"code": "rBP7-3", "rule": {"transcript.splice.effect": "no_effect"}},
        {"code": "rBP7-4", "rule": {"transcript.Existing_variation": {"$in": ["rs1799943"]}}},
        {"code": "BP7", "rule": {"$$aggregate": {"$all": ["rBP7-1", "rBP7-2", "rBP7-3"]}}},
        {"code": "BP8", "rule": {"$$aggregate": {"$all": ["rBP7-1", "BP*"]}}},
        {"code": "PP7", "rule": {"$$aggregate": {"$atleast": [2, "rPP3-1", "rPP3-2", "rPP3-3"]}}},
        {"code": "PP8", "rule": {"frequencies.ExAC.Adj": 0.24646677011897014}},
        {"code": "PP9", "rule": {"$$aggregate": {"$atleast": [1, "rPP3*", "rPP1*"]}}},
        {"code": "GP1", "rule": {"genepanel.hi_freq_cutoff": 0.01}},
        {"code": "PP10", "rule": {"$$aggregate": {"$atleast": [1, "GP*", "BP*"]}}},
        {"code": "PP11", "rule": {"$$aggregate": {"$or": [{"$all": ["PP9"]}, {"$all": ["PP10"]}]}}},
        {
            "code": "PP11.1",
            "rule": {"$$aggregate": {"$or": [{"$all": ["PP9"]}, {"$not": {"$all": ["PP10"]}}]}},
        },
        {
            "code": "PP11.2",
            "rule": {"$$aggregate": {"$or": [{"$all": ["PP9"]}, {"$in": ["PP10", "FOO"]}]}},
        },
        {"code": "PP11.2.1", "rule": {"$$aggregate": {"$or": ["PP9", "PP10"]}}},
        {
            "code": "PP11.3",
            "rule": {"$$aggregate": {"$or": [{"$all": ["PP9"]}, {"$in": ["NOT", "HERE"]}]}},
        },
        {
            "code": "PP12",
            "rule": {"$$aggregate": {"$and": [{"$all": ["PP10"]}, {"$all": ["PP9"]}]}},
        },
        {"code": "PP13", "rule": {"refassessment.*.ref_segregation": "segr+++"}},
        {"code": "PP14", "rule": {"refassessment.*.ref_ihc": "mmr_loss++"}},
    ]

    jsondata = {
        "frequencies": {
            "1000g": {
                "AA": 0.102587,
                "AFR": 0.05,
                "AMR": 0.19,
                "ASN": 0.37,
                "EA": 0.263256,
                "EUR": 0.23,
                "G": 0.2185,
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
                "SAS": 0.2833209693372898,
            },
        },
        "genetic": {"Conservation": "non_conserved"},
        "refassessment": {"0": {"ref_segregation": "segr+++"}, "1": {"ref_ihc": "mmr_loss+"}},
        "genomic": {"Conservation": "conserved"},
        "transcript": {
            "Consequence": ["synonymous_variant"],
            "Conseq": ["missense_var"],
            "Existing_variation": ["rs1799943"],
            "HGVSc": "NM_000059.3:c.-26G>A",
            "Transcript": "NM_000059",
            "Transcript_version": "3",
            "Transcript_version_CLINVAR": "3",
            "Transcript_version_HGMD": "3",
        },
        "genepanel": {
            "inheritance": ["AD", "XD"],
            "last_exon_important": "true",
            "hi_freq_cutoff": 0.01,
            "lo_freq_cutoff": 0.001,
            "disease_mode": "lof_only",
        },
    }

    def testExpandMultiRules(self):
        dataflattened = {
            ".".join(list(k)): v for k, v in GRA().parseNodeToSourceKeyedDict(self.jsondata).items()
        }
        rulelist = [
            rul
            for resultlist in list(GRL().parseRules(self.jsonrules).values())
            for rul in resultlist
        ]
        GRA().expand_multi_rules(rulelist, dataflattened)
        self.assertEqual(rulelist[-2].source, "refassessment.0.ref_segregation")
        self.assertEqual(rulelist[-2].code, "PP13")
        self.assertEqual(rulelist[-2].value, ["segr+++"])
        self.assertTrue(isinstance(rulelist[-2], GRM.InRule))
        self.assertEqual(rulelist[-1].source, "refassessment.1.ref_ihc")
        self.assertEqual(rulelist[-1].code, "PP14")
        self.assertEqual(rulelist[-1].value, ["mmr_loss++"])
        self.assertTrue(isinstance(rulelist[-1], GRM.InRule))

    def testParseToSourceKeyed(self):
        data = GRA().parseNodeToSourceKeyedDict(self.jsondata)
        self.assertEqual(data[("frequencies", "1000g", "AA")], 0.102587)
        self.assertEqual(data[("frequencies", "1000g", "EUR")], 0.23)
        self.assertEqual(data[("transcript", "Consequence")], ["synonymous_variant"])
        self.assertEqual(data[("transcript", "Existing_variation")], ["rs1799943"])
        self.assertEqual(data[("transcript", "Transcript_version_CLINVAR")], "3")

    def testApplyRules(self):
        (passed, notpassed) = GRA().applyRules(
            GRL().parseRules(self.jsonrules), GRA().parseNodeToSourceKeyedDict(self.jsondata)
        )
        self.assertEqual(
            [rule.code for rule in passed],
            [
                "BP1",
                "BP1",
                "rBP7-1",
                "rBP7-4",
                "BP8",
                "PP8",
                "GP1",
                "PP10",
                "PP11",
                "PP11.2",
                "PP11.2.1",
                "PP13",
            ],
        )
        self.assertEqual(passed[0].source, "transcript.Consequence")
        self.assertEqual(
            [rule.code for rule in notpassed],
            ["BP2", "rBP7-2", "rBP7-3", "BP7", "PP7", "PP9", "PP11.1", "PP11.3", "PP12", "PP14"],
        )
