import unittest
from ..grm import GRM
from ..grl import GRL


class GrlTest(unittest.TestCase):
    def testParseSimpleEqualityRule(self):
        jsonstring = [{"code": "BP2", "rule": {"transcript.splice.effect": "de_novo"}}]

        rules = self.parseJson(jsonstring)
        self.assertEqual(rules["BP2"][0].source, "transcript.splice.effect")
        self.assertEqual(rules["BP2"][0].code, "BP2")
        self.assertEqual(rules["BP2"][0].value, ["de_novo"])
        self.assertTrue(isinstance(rules["BP2"][0], GRM.InRule))

    def testParseBasicRuleList(self):
        jsonstring = [
            {
                "code": "BP1",
                "rule": {
                    "transcript.Consequence": {"$in": ["missense_variant", "synonymous_variant"]}
                },
            },
            {"code": "BP2", "rule": {"transcript.splice.effect": "de_novo"}},
            {"code": "BP1", "rule": {"t.s.e": "d_n"}},
            {
                "code": "rBP7-1",
                "rule": {
                    "transcript.Consequence": {
                        "$in": [
                            "start_retained_variant",
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
            {"code": "rBP7-4", "rule": {"foo.bar": {"$lt": "34323"}}},
            {"code": "rBP7-5", "rule": {"bar.foo": {"$gt": 0.5}}},
            {"code": "rBP7-6", "rule": {"ba.fo": {"$range": [0, 1.6]}}},
            {"code": "GP1", "rule": {"genepanel.hi_freq_cutoff": 0.01}},
        ]

        rules = self.parseJson(jsonstring)
        self.assertEqual(rules["BP1"][0].code, "BP1")
        self.assertEqual(rules["BP1"][1].code, "BP1")
        self.assertEqual(rules["BP1"][1].source, "t.s.e")
        self.assertEqual(rules["BP1"][1].value, ["d_n"])
        self.assertEqual(rules["BP2"][0].code, "BP2")

        self.assertEqual(rules["rBP7-1"][0].code, "rBP7-1")
        self.assertEqual(rules["rBP7-1"][0].source, "transcript.Consequence")
        self.assertEqual(
            rules["rBP7-1"][0].value,
            [
                "start_retained_variant",
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
            ],
        )
        self.assertEqual(rules["rBP7-2"][0].code, "rBP7-2")
        self.assertEqual(rules["rBP7-3"][0].code, "rBP7-3")
        self.assertEqual(rules["rBP7-3"][0].source, "transcript.splice.effect")
        self.assertEqual(rules["rBP7-3"][0].value, ["no_effect"])
        self.assertEqual(rules["rBP7-4"][0].value, "34323")
        self.assertTrue(isinstance(rules["rBP7-4"][0], GRM.LtRule))
        self.assertEqual(rules["rBP7-5"][0].value, 0.5)
        self.assertTrue(isinstance(rules["rBP7-5"][0], GRM.GtRule))
        self.assertTrue(isinstance(rules["rBP7-6"][0], GRM.RangeRule))
        self.assertEqual(rules["rBP7-6"][0].value[0], 0)
        self.assertEqual(rules["rBP7-6"][0].value[1], 1.6)

    def testParseCompositeRules(self):
        jsonstring = [
            {
                "code": "BP1",
                "rule": {
                    "transcript.Consequence": {"$in": ["missense_variant", "synonymous_variant"]}
                },
            },
            {"code": "BP2", "rule": {"genepanel.hi_freq_cutoff": 0.001}},
            {
                "code": "MYAND",
                "rule": {
                    "$and": [
                        {"genepanel.hi_freq_cutoff": 0.001},
                        {
                            "transcript.Consequence": {
                                "$in": ["missense_variant", "synonymous_variant"]
                            }
                        },
                    ]
                },
            },
            {
                "code": "MYOR",
                "rule": {
                    "$or": [
                        {"genepanel.hi_freq_cutoff": 0.002},
                        {"transcript.Conseq": {"$in": ["missense_v", "synonymous_v"]}},
                    ]
                },
            },
            {
                "code": "MYCOMPLEX",
                "rule": {
                    "$or": [
                        {"genepanel.hi_freq_cutoff": 0.001},
                        {
                            "$and": [
                                {"a.b": 0.01},
                                {"c.d": {"$in": ["some", "values"]}},
                                {
                                    "$or": [
                                        {"e.f.g": "0.001"},
                                        {"h.jjj": {"$in": ["more", "values"]}},
                                    ]
                                },
                            ]
                        },
                        {"genepanel.foo": "baz"},
                    ]
                },
            },
        ]

        rules = self.parseJson(jsonstring)
        self.assertTrue(isinstance(rules["MYAND"][0], GRM.AndRule))
        self.assertEqual(rules["MYAND"][0].subrules[0].source, "genepanel.hi_freq_cutoff")
        self.assertEqual(rules["MYAND"][0].subrules[0].value, [0.001])
        self.assertTrue(isinstance(rules["MYAND"][0].subrules[0], GRM.InRule))
        self.assertEqual(rules["MYAND"][0].subrules[1].source, "transcript.Consequence")
        self.assertEqual(
            rules["MYAND"][0].subrules[1].value, ["missense_variant", "synonymous_variant"]
        )
        self.assertTrue(isinstance(rules["MYAND"][0].subrules[1], GRM.InRule))

        self.assertTrue(isinstance(rules["MYOR"][0], GRM.OrRule))
        self.assertEqual(rules["MYOR"][0].subrules[0].source, "genepanel.hi_freq_cutoff")
        self.assertEqual(rules["MYOR"][0].subrules[0].value, [0.002])
        self.assertTrue(isinstance(rules["MYOR"][0].subrules[0], GRM.InRule))
        self.assertEqual(rules["MYOR"][0].subrules[1].source, "transcript.Conseq")
        self.assertEqual(rules["MYOR"][0].subrules[1].value, ["missense_v", "synonymous_v"])
        self.assertTrue(isinstance(rules["MYOR"][0].subrules[1], GRM.InRule))

        self.assertTrue(isinstance(rules["MYCOMPLEX"][0], GRM.OrRule))
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[0].source, "genepanel.hi_freq_cutoff")
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[0].value, [0.001])
        self.assertTrue(isinstance(rules["MYCOMPLEX"][0].subrules[1], GRM.AndRule))
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[1].subrules[0].source, "a.b")
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[1].subrules[0].value, [0.01])
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[1].subrules[1].source, "c.d")
        self.assertTrue(isinstance(rules["MYCOMPLEX"][0].subrules[1].subrules[1], GRM.InRule))
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[1].subrules[1].value, ["some", "values"])
        self.assertTrue(isinstance(rules["MYCOMPLEX"][0].subrules[1].subrules[2], GRM.OrRule))
        self.assertTrue(
            isinstance(rules["MYCOMPLEX"][0].subrules[1].subrules[2].subrules[0], GRM.InRule)
        )
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[1].subrules[2].subrules[0].source, "e.f.g")
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[1].subrules[2].subrules[0].value, ["0.001"])
        self.assertTrue(
            isinstance(rules["MYCOMPLEX"][0].subrules[1].subrules[2].subrules[1], GRM.InRule)
        )
        self.assertEqual(rules["MYCOMPLEX"][0].subrules[1].subrules[2].subrules[1].source, "h.jjj")
        self.assertEqual(
            rules["MYCOMPLEX"][0].subrules[1].subrules[2].subrules[1].value, ["more", "values"]
        )

    def parseJson(self, jsonobj):
        grl = GRL()
        rules = grl.parseRules(jsonobj)
        return rules

    def testRuleAgGRMgationAll(self):
        jsonstring = [
            {
                "code": "rBP7-1",
                "rule": {
                    "transcript.Consequence": {
                        "$in": [
                            "start_retained_variant",
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
            {"code": "rBP7-4", "rule": {"transcript.splice.power": "some_effect"}},
            {"code": "BP7", "rule": {"$$aggregate": {"$all": ["rBP7-1", "rBP7-2", "rBP7-3"]}}},
            {"code": "PP7", "rule": {"$$aggregate": {"$all": ["BP7", "rBP7-4"]}}},
            {"code": "PP8", "rule": {"$$aggregate": {"$not": {"$all": ["BP7", "rBP7-4"]}}}},
        ]
        rules = self.parseJson(jsonstring)
        self.assertTrue(isinstance(rules["BP7"][0], GRM.AllRule))
        self.assertEqual(rules["BP7"][0].value, ["rBP7-1", "rBP7-2", "rBP7-3"])
        self.assertEqual(rules["BP7"][0].code, "BP7")
        self.assertEqual(rules["PP8"][0].subrule.value, ["BP7", "rBP7-4"])

    def testRuleAggregationComposite(self):
        jsonstring = [
            {"code": "rBP7-1", "rule": {"genomic.Conservation": "non_conserved"}},
            {"code": "rBP7-2", "rule": {"transcript.splice.effect": "no_effect"}},
            {"code": "rBP7-3", "rule": {"transcript.splice.power": "some_effect"}},
            {"code": "rBP7-4", "rule": {"transcript.splice.power": "some_effect"}},
            {"code": "rBP7-5", "rule": {"transcript.splice.power": "some_effect"}},
            {"code": "BP7", "rule": {"$$aggregate": {"$all": ["rBP7-1", "rBP7-2", "rBP7-3"]}}},
            {"code": "BP8", "rule": {"$$aggregate": {"$atleast": [1, "rBP7-4", "rBP7-5"]}}},
            {
                "code": "BP9",
                "rule": {"$$aggregate": {"$or": [{"$all": ["BP7"]}, {"$not": {"$all": ["BP8"]}}]}},
            },
        ]
        rules = self.parseJson(jsonstring)
        self.assertTrue(rules["BP9"][0].aggregate)
        self.assertTrue(isinstance(rules["BP9"][0], GRM.OrRule))
        self.assertEqual(rules["BP9"][0].subrules[0].value, ["BP7"])
        self.assertEqual(rules["BP9"][0].subrules[1].subrule.value, ["BP8"])

    def testRuleAgGRMgationAtLeast(self):
        jsonstring = [
            {
                "code": "rBP7-1",
                "rule": {
                    "transcript.Consequence": {
                        "$in": [
                            "start_retained_variant",
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
            {"code": "rBP7-2", "rule": {"genomic.Onservation": "conserved"}},
            {
                "code": "PP7",
                "rule": {"$$aggregate": {"$atleast": [2, "rBP7-1", "rBP7-2", "rBP7-3"]}},
            },
        ]
        rules = self.parseJson(jsonstring)
        self.assertTrue(isinstance(rules["PP7"][0], GRM.AtLeastRule))
        self.assertEqual(rules["PP7"][0].atleast, 2)
        self.assertEqual(rules["PP7"][0].value, ["rBP7-1", "rBP7-2", "rBP7-3"])
        self.assertEqual(rules["PP7"][0].code, "PP7")
