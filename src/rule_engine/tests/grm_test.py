import unittest
from ..grm import GRM


class GrmTest(unittest.TestCase):
    def testInRuleSingleInputAnnotation(self):
        rule = GRM.InRule(["transcript_ablation", "splice_donor_variant"], "VEP consequence")
        self.assertEquals(rule.query(["transcript_ablation"]), [rule])
        self.assertFalse(rule.query(["not_there"]))
        rule = GRM.InRule(["transcript_ablation"], "VEP consequence")
        self.assertEquals(rule.query(["transcript_ablation"]), [rule])
        self.assertFalse(rule.query(["not_there"]))
        rule = GRM.InRule([], "VEP consequence")
        self.assertFalse(rule.query(["transcript_ablation"]))

    def testInRuleMultipleInputAnnotation(self):
        rule = GRM.InRule(["transcript_ablation", "splice_donor_variant"], "VEP consequence")
        self.assertEquals(rule.query(["transcript_ablation", "something_else_too"]), [rule])
        self.assertFalse(rule.query(["not_there", "not_there_neither"]))
        rule = GRM.InRule(["transcript_ablation"], "VEP consequence")
        self.assertEquals(rule.query(["transcript_ablation", "splice_donor_variant"]), [rule])
        self.assertFalse(rule.query(["not_there", "not_there_neither"]))
        rule = GRM.InRule([], "VEP consequence")
        self.assertFalse(rule.query(["transcript_ablation", "something_else"]))

    """
    The InRule when used as a simple {"transcript.splice.effect": "de_novo"}
    """

    def testInRuleSingleValue(self):
        rule = GRM.InRule(["de_novo"], "transcript.splice.effect")
        self.assertEquals(rule.query(["de_novo"]), [rule])
        self.assertEquals(rule.query("de_novo"), [rule])

        self.assertFalse(rule.query(["not_de_novo"]))
        rule = GRM.InRule([99], "transcript.splice.eff")
        self.assertEquals(rule.query([99]), [rule])
        self.assertEquals(rule.query(99), [rule])

    def testAndRule(self):
        rule1 = GRM.InRule(["transcript_ablation"], "VEP consequence")
        rule2 = GRM.InRule(["splice_donor_variant"], "VEP consequence")
        rule3 = GRM.InRule(["stop_gained"], "VEP consequence")
        andrule = GRM.AndRule([rule1, rule2, rule3])
        result = andrule.query(["stop_gained", "transcript_ablation", "splice_donor_variant"])
        self.assertEquals(result, [rule1, rule2, rule3])
        self.assertFalse(andrule.query(["stop_gained", "splice_donor_variant"]))
        self.assertFalse(andrule.query([]))

    def testOrRule(self):
        rule1 = GRM.InRule(["transcript_ablation"], "VEP consequence")
        rule2 = GRM.InRule(["splice_donor_variant"], "VEP consequence")
        rule3 = GRM.InRule(["stop_gained"], "VEP consequence")
        orrule = GRM.OrRule([rule1, rule2, rule3])
        result = orrule.query(["stop_gained", "splice_donor_variant"])
        self.assertEquals(result, [rule2, rule3])
        self.assertFalse(orrule.query(["different", "annotations", "altogether"]))
        self.assertFalse(orrule.query([]))

    def testGtRule(self):
        rule = GRM.GtRule(0.4, "ESP6500")
        self.assertEquals(rule.query(0.5), [rule])
        self.assertEquals(rule.query(0.6)[0].source, "ESP6500")
        self.assertEquals(rule.query("0.6")[0].source, "ESP6500")
        self.assertEquals(rule.query("68")[0].source, "ESP6500")
        self.assertFalse(rule.query(-876))
        self.assertFalse(rule.query(0.4))

    def testLtRule(self):
        rule = GRM.LtRule(0.4, "ESP6501")
        self.assertEquals(rule.query(0.3), [rule])
        self.assertEquals(rule.query(0.3999999)[0].source, "ESP6501")
        self.assertEquals(rule.query("-678")[0].source, "ESP6501")
        self.assertFalse(rule.query(876))
        self.assertFalse(rule.query(0.4))

    def testRangeRule(self):
        rule = GRM.RangeRule([-67.3, 4], "ESP6502")
        self.assertEquals(rule.query(-3), [rule])
        self.assertEquals(rule.query(-67.2999999)[0].source, "ESP6502")
        self.assertFalse(rule.query(-875))
        self.assertFalse(rule.query(4.00002))

    """
    Test of
    transcript_ablation AND splice_donor_variant AND stop_gained
    OR ([Phase]in_cis_pathogenic AND [Phase]in_trans_pathogenic)
    """

    def testComplexCompositeRule(self):
        rule1_1 = GRM.InRule(["transcript_ablation"], "VEP consequence")
        rule1_2 = GRM.InRule(["splice_donor_variant"], "VEP consequence")
        rule1_3 = GRM.InRule(["stop_gained"], "VEP consequence")
        andrule1 = GRM.AndRule([rule1_1, rule1_2, rule1_3])

        rule2_1 = GRM.InRule(["in_cis_pathogenic"], "Phase")
        rule2_2 = GRM.InRule(["in_trans_pathogenic"], "Phase")
        andrule2 = GRM.AndRule([rule2_1, rule2_2])

        orrule = GRM.OrRule([andrule1, andrule2])

        self.assertEquals(
            orrule.query(["transcript_ablation", "splice_donor_variant", "stop_gained"]),
            [rule1_1, rule1_2, rule1_3],
        )
        self.assertEquals(
            orrule.query(["transcript_ablation", "splice_donor_variant", "stop_gained"])[0].source,
            "VEP consequence",
        )
        self.assertEquals(
            orrule.query(["in_cis_pathogenic", "in_trans_pathogenic"]), [rule2_1, rule2_2]
        )
        self.assertEquals(
            orrule.query(["in_cis_pathogenic", "in_trans_pathogenic"])[0].source, "Phase"
        )
        self.assertFalse(
            orrule.query(["transcript_ablation", "splice_donor_variant", "in_cis_pathogenic"])
        )

    def testAllRule(self):
        rule = GRM.AllRule(["rBP7-1", "rBP7-2", "rBP7-3", "rBP7-4", "rBP7-5"], "BP7")
        self.assertFalse(rule.query([]))
        self.assertFalse(rule.query(["rBP7-1"]))
        self.assertFalse(rule.query(["rBP7-1", "rBP7-2"]))
        self.assertFalse(rule.query(["rBP7-1", "rBP7-3"]))
        self.assertEquals(rule.query(["rBP7-1", "rBP7-2", "rBP7-3", "rBP7-4", "rBP7-5"]), [rule])
        self.assertEquals(
            rule.query(["rBP7-1", "rBP7-2", "rBP7-4", "rBP7-3", "rBP7-5", "rBP7-4"]), [rule]
        )
        self.assertEquals(
            rule.query(["rBP7-1", "rBP7-2", "rBP7-3", "rBP7-4", "rBP7-5", "and"]), [rule]
        )
        self.assertEquals(
            rule.query(["rBP7-1", "rBP7-2", "rBP7-3", "rBP7-4", "rBP7-5", "and", "more"]), [rule]
        )

    def testAllRuleWildcard(self):
        rule = GRM.AllRule(["BP6", "PP*"], "BP7")
        self.assertFalse(rule.query([]))
        self.assertFalse(rule.query(["rBP7-1"]))
        self.assertFalse(rule.query(["rBP7-1", "rBP7-2"]))
        self.assertFalse(rule.query(["rBP7-1", "BP6"]))
        self.assertEquals(rule.query(["PP3", "BP6"]), [rule])
        self.assertEquals(
            rule.query(["rBP7-1", "rBP7-2", "rBP7-4", "PP5", "rBP7-5", "BP6", "rBP7-4"]), [rule]
        )

    def testAtleastRule(self):
        rule = GRM.AtLeastRule(
            ["rBP7-1", "rBP7-2", "rBP7-3", "rBP7-4", "rBP7-5", "rBP7-1"], "BP7", 3
        )
        self.assertFalse(rule.query([]))
        self.assertFalse(rule.query(["rBP7-1"]))
        self.assertFalse(rule.query(["rBP7-1", "rBP7-2"]))
        self.assertFalse(rule.query(["rBP7-1", "rBP7-3", "rBP7-1"]))
        self.assertEquals(rule.query(["rBP7-1", "rBP7-2", "rBP7-4"]), [rule])
        self.assertEquals(rule.query(["rBP7-1", "rBP7-2", "rBP7-3", "rBP7-4"]), [rule])
        self.assertEquals(
            rule.query(["rBP7-1", "rBP7-2", "rBP7-4", "rBP7-3", "rBP7-5", "rBP7-4"]), [rule]
        )
        self.assertEquals(
            rule.query(["rBP7-1", "rBP7-2", "rBP7-3", "rBP7-4", "rBP7-5", "and"]), [rule]
        )
        self.assertEquals(
            rule.query(["rBP7-1", "rBP7-2", "rBP7-3", "rBP7-4", "rBP7-5", "and", "more"]), [rule]
        )

    def testAtleastRuleWildcard(self):
        rule = GRM.AtLeastRule(["BP7", "BP8", "BP9", "BP1*"], "BP0", 3)
        self.assertFalse(rule.query([]))
        self.assertFalse(rule.query(["BP7"]))
        self.assertFalse(rule.query(["BP7", "BP7"]))
        self.assertFalse(rule.query(["BP1567", "BP1987"]))
        self.assertFalse(rule.query(["BP1567", "BP1987", "BP23"]))
        self.assertFalse(rule.query(["BP7", "BP8", "BP7"]))
        self.assertEquals(rule.query(["BP7", "BP8", "BP9"]), [rule])
        self.assertEquals(rule.query(["BP7", "BP1234234", "BP9"]), [rule])
        self.assertEquals(rule.query(["BP7", "BP1234234", "BP9", "BP7"]), [rule])

    def testNotRule(self):
        rule1 = GRM.InRule(["transcript_ablation"], "VEP consequence")
        rule2 = GRM.InRule(["splice_donor_variant"], "VEP consequence")
        rule3 = GRM.InRule(["stop_gained"], "VEP consequence")
        andrule = GRM.AndRule([rule1, rule2, rule3])
        notrule = GRM.NotRule(andrule)
        self.assertFalse(
            notrule.query(["stop_gained", "transcript_ablation", "splice_donor_variant"])
        )
        self.assertFalse(
            notrule.query(["stop_gained", "transcript_ablation", "splice_donor_variant", "foo"])
        )
        self.assertEquals(notrule.query(["stop_gained", "splice_donor_variant"]), [andrule])
        self.assertEquals(notrule.query([]), [andrule])
