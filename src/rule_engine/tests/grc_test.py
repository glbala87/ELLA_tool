from .. grc import ACMGClassifier2015,ClassificationResult
from .. grm import GRM
import unittest
import re

class ACMGClassifier2015Test(unittest.TestCase):
    
    def test_count_occurences(self):
        classifier = ACMGClassifier2015()
        self.assertListEqual(classifier.occurences(re.compile("PVS1"), [GRM.Rule("", "foo", "PVS1")]), [GRM.Rule("", "foo", "PVS1")])
        self.assertListEqual(classifier.occurences(re.compile("PVS1"), [GRM.Rule("", "foo", "PVS2"), GRM.Rule("", "bar", "BP1")]), [])
        self.assertListEqual(classifier.occurences(re.compile("PS1"), []), [])
        self.assertListEqual(classifier.occurences(re.compile("PVS.*"), [GRM.Rule("", "foo", "PVS1")]), [GRM.Rule("", "foo", "PVS1")])
        self.assertListEqual(classifier.occurences(re.compile("PVS.*"), [GRM.Rule("", "foo", "PVS1"),
                                                                  GRM.Rule("","bar", "PVS3")]),
                                                                 [GRM.Rule("","foo", "PVS1"),
                                                                  GRM.Rule("","bar", "PVS3")])
        self.assertListEqual(classifier.occurences(re.compile("PVS.*"), [GRM.Rule("", "foo", "PVS1"),
                                                                  GRM.Rule("", "bar", "PVS3"),
                                                                  GRM.Rule("", "baz", "PP1")]),
                                                                 [GRM.Rule("", "foo", "PVS1"),
                                                                  GRM.Rule("", "bar", "PVS3")])
        self.assertListEqual(classifier.occurences(re.compile("PM.*"), [GRM.Rule("", "foo", "BS2"),
                                                                 GRM.Rule("", "bar", "BS4"),
                                                                 GRM.Rule("", "baz", "PVS1"),
                                                                 GRM.Rule("", "baz", "PVS3"),
                                                                 GRM.Rule("", "baz", "PM3"),
                                                                 GRM.Rule("", "baz", "PP2")]),
                                                                [GRM.Rule("", "baz", "PM3")])

        self.assertListEqual(classifier.occurences(re.compile("PM.*"), [GRM.Rule("", "foo", "BS2"),
                                                                 GRM.Rule("", "bar", "PM3"),
                                                                 GRM.Rule("", "baz", "BS4"),
                                                                 GRM.Rule("", "baz", "PVS1"),
                                                                 GRM.Rule("", "baz", "PVS3"),
                                                                 GRM.Rule("", "baz", "PM3"),
                                                                 GRM.Rule("", "baz", "PP2"),                                                                    
                                                                 GRM.Rule("", "bav", "PM1")]),
                                                                [GRM.Rule("", "bar", "PM3"),
                                                                 GRM.Rule("", "baz", "PM3"),
                                                                 GRM.Rule("", "bav", "PM1")])

    def test_count_occurences_special_cases(self):
        classifier = ACMGClassifier2015()

        self.assertListEqual(classifier.occurences(re.compile("PP.*"), [GRM.Rule("", "foo", "BS2"),
                                                                 GRM.Rule("", "bar", "PP3"),
                                                                 GRM.Rule("", "baz", "BS4"),
                                                                 GRM.Rule("", "baz", "PVS1"),
                                                                 GRM.Rule("", "baz", "PVS3"),
                                                                 GRM.Rule("", "baz", "PM3"),
                                                                 GRM.Rule("", "baz", "PP3"),                                                                    
                                                                 GRM.Rule("", "bav", "PP1"),
                                                                 GRM.Rule("", "baw", "PP2")]),                    
                                                                [GRM.Rule("", "bar", "PP3"), # The first of the PP3s returned. 
                                                                 GRM.Rule("", "bav", "PP1"),
                                                                 GRM.Rule("", "baw", "PP2")])

        self.assertListEqual(classifier.occurences(re.compile("PP.*"), [GRM.Rule("", "foo", "BS2"),
                                                                 GRM.Rule("", "bar", "PP3"),
                                                                 GRM.Rule("", "baz", "BS4"),
                                                                 GRM.Rule("", "baz", "PVS1"),
                                                                 GRM.Rule("", "baz", "PVS3"),
                                                                 GRM.Rule("", "baz", "PM3"),
                                                                 GRM.Rule("", "baz", "PP3"),                                                                    
                                                                 GRM.Rule("", "bav", "PP1"),
                                                                 GRM.Rule("", "ban", "PP1")]),                    
                                                                [GRM.Rule("", "bar", "PP3"), # The first of the PP3s returned. 
                                                                 GRM.Rule("", "bav", "PP1"),
                                                                 GRM.Rule("", "ban", "PP1")])        

        self.assertListEqual(classifier.occurences(re.compile("BP.*"), [GRM.Rule("", "foo", "BP4"),
                                                                 GRM.Rule("", "bar", "PP3"),
                                                                 GRM.Rule("", "baz", "BP4"),
                                                                 GRM.Rule("", "baz", "PVS3"),
                                                                 GRM.Rule("", "baz", "PVS3"),
                                                                 GRM.Rule("", "baz", "PM3"),
                                                                 GRM.Rule("", "baz", "BP3"),                                                                    
                                                                 GRM.Rule("", "bav", "PP1"),
                                                                 GRM.Rule("", "baz", "PP1"),                                                                    
                                                                 GRM.Rule("", "bav", "BP4"),
                                                                 GRM.Rule("", "ban", "BP4")]),                    
                                                                [GRM.Rule("", "foo", "BP4"),
                                                                 GRM.Rule("", "baz", "BP3")])                
    
    def test_classify_pathogenic(self):
        classifier = ACMGClassifier2015()
        path_res = classifier.pathogenic([GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s2", "BS4"),
                GRM.Rule("", "s3", "PVS1"),
                GRM.AtLeastRule(["rBP7-1", "rBP7-2","rBP7-3","rBP7-4","rBP7-5", "rBP7-1"], "BP7", 3),
                GRM.Rule("", "s4", "PS3"),
                GRM.Rule("", "s7", "PP1")])
        self.assertListEqual(path_res,
                               [GRM.Rule("", "s3", "PVS1"), # 1PVS* AND >=1PS*
                                GRM.Rule("", "s4", "PS3")])

        path_res = classifier.pathogenic([GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s3", "PVS1"),
                GRM.Rule("", "s2", "BS4"),
                GRM.Rule("", "s7", "PVSX1")])
        self.assertListEqual(path_res,
                               [GRM.Rule("", "s3", "PVS1"), # >=2PVS*
                                GRM.Rule("", "s7", "PVSX1")])

        path_res = classifier.pathogenic([
                GRM.Rule("", "s1", "BS2"), 
                GRM.Rule("", "s2", "BS4"), 
                GRM.Rule("", "s3", "PVS1"), 
                GRM.Rule("", "s4", "PS3"), 
                GRM.Rule("", "s5", "PS3"), 
                GRM.Rule("", "s6", "PS3"), 
                GRM.Rule("", "s7", "PP1")])
        self.assertListEqual(path_res,
            [GRM.Rule("", "s3", "PVS1"), # First 1PVS* AND >=1PS*
            GRM.Rule("", "s4", "PS3"),
            GRM.Rule("", "s5", "PS3"),
            GRM.Rule("", "s6", "PS3"),
            GRM.Rule("", "s4", "PS3"), # Then >=2 PS*, because of not shortcut/conversion to set:
            GRM.Rule("", "s5", "PS3"),
            GRM.Rule("", "s6", "PS3")
            ])
        
        path_res = classifier.pathogenic([
                GRM.Rule("", "s1", "BS2"), 
                GRM.Rule("", "s2", "PS4"), 
                GRM.Rule("", "s3", "PM2"), 
                GRM.Rule("", "s4", "PM1"), 
                GRM.Rule("", "s5", "BA3"), 
                GRM.Rule("", "s6", "PP3"), 
                GRM.Rule("", "s7", "PP1")])
        self.assertListEqual(path_res,
            [GRM.Rule("", "s2", "PS4"), # 1PS* AND 2PM* AND >=2PP*
            GRM.Rule("", "s3", "PM2"),
            GRM.Rule("", "s4", "PM1"),
            GRM.Rule("", "s6", "PP3"),
            GRM.Rule("", "s7", "PP1")
            ])
        
        path_res = classifier.pathogenic([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s2", "PS4"),
                GRM.Rule("", "s6", "PP4"),
                GRM.Rule("", "s6", "PP6"),
                GRM.Rule("", "s6", "PP1"),
                GRM.Rule("", "s5", "BA3"),
                GRM.Rule("", "s6", "PP3"),
                GRM.Rule("", "s8", "PP3"),
                GRM.Rule("", "s7", "PM1")])
        self.assertListEqual(path_res,
            [GRM.Rule("", "s2", "PS4"), # 1PS* AND 1PM* AND >=4PP*
            GRM.Rule("", "s7", "PM1"),
            GRM.Rule("", "s6", "PP4"),
            GRM.Rule("", "s6", "PP6"),
            GRM.Rule("", "s6", "PP1"),
            GRM.Rule("", "s6", "PP3")
            ])
        
        self.assertFalse(classifier.pathogenic([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s2", "PS4"),
                GRM.Rule("", "s6", "PP4"),
                GRM.Rule("", "s6", "PP6"),
                GRM.Rule("", "s5", "BA3"),
                GRM.Rule("", "s6", "PP3"),
                GRM.Rule("", "s8", "PP3"),
                GRM.Rule("", "s7", "PM1")]))
        
        self.assertFalse(classifier.pathogenic([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s6", "PP4"),
                GRM.Rule("", "s6", "PP1"),
                GRM.Rule("", "s6", "PP6"),
                GRM.Rule("", "s5", "BA3"),
                GRM.Rule("", "s6", "PP3"),
                GRM.Rule("", "s8", "PP3"),
                GRM.Rule("", "s7", "PM1")]))
        
    def test_classify_likely_pathogenic(self):
        classifier = ACMGClassifier2015()
        lp_res = classifier.likely_pathogenic([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s2", "PS4"),
                GRM.Rule("", "s3", "PP4"),
                GRM.Rule("", "s4", "PP6"),
                GRM.Rule("", "s6", "BA3"),
                GRM.Rule("", "s7", "PP3"),
                GRM.Rule("", "s8", "PP3"),
                GRM.Rule("", "s9", "PM1")])
        self.assertListEqual(lp_res,
            [GRM.Rule("", "s2", "PS4"), # 1PS* AND 1PM*
            GRM.Rule("", "s9", "PM1"),
            GRM.Rule("", "s2", "PS4"), # 1PS* AND >=2PP*
            GRM.Rule("", "s3", "PP4"),
            GRM.Rule("", "s4", "PP6"),
            GRM.Rule("", "s7", "PP3")
            ])
        
        lp_res = classifier.likely_pathogenic([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s2", "PS4"),
                GRM.Rule("", "s3", "PP4"),
                GRM.Rule("", "s4", "PP6"),
                GRM.Rule("", "s5", "PP1"),
                GRM.Rule("", "s6", "BA3"),
                GRM.Rule("", "s7", "PP3"),
                GRM.Rule("", "s8", "PP3"),
                GRM.Rule("", "s9", "PM1")])
        self.assertListEqual(lp_res,
            [GRM.Rule("", "s2", "PS4"), # First 1PS* AND 1PM*
            GRM.Rule("", "s9", "PM1"),
            GRM.Rule("", "s2", "PS4"), # Then 1PS* AND >=2PP*
            GRM.Rule("", "s3", "PP4"),
            GRM.Rule("", "s4", "PP6"),
            GRM.Rule("", "s5", "PP1"),
            GRM.Rule("", "s7", "PP3"),
            GRM.Rule("", "s9", "PM1"), # Then 1PM* AND >=4PP*
            GRM.Rule("", "s3", "PP4"),
            GRM.Rule("", "s4", "PP6"),
            GRM.Rule("", "s5", "PP1"),
            GRM.Rule("", "s7", "PP3")
            ])
        
        lp_res = classifier.likely_pathogenic([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s3", "PP4"),
                GRM.Rule("", "s4", "PP6"),
                GRM.Rule("", "s5", "PP1"),
                GRM.Rule("", "s6", "BA3"),
                GRM.Rule("", "s7", "PP3"),
                GRM.Rule("", "s8", "PP3"),
                GRM.Rule("", "s9", "PM1")])
        self.assertListEqual(lp_res,
            [GRM.Rule("", "s9", "PM1"), # 1PM* AND >=4PP*
            GRM.Rule("", "s3", "PP4"),
            GRM.Rule("", "s4", "PP6"),
            GRM.Rule("", "s5", "PP1"),
            GRM.Rule("", "s7", "PP3")
            ])
        
        lp_res = classifier.likely_pathogenic([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s3", "BP4"),
                GRM.Rule("", "s4", "BP6"),
                GRM.Rule("", "s5", "BP1"),
                GRM.Rule("", "s6", "PVS3"),
                GRM.Rule("", "s7", "BP3"),
                GRM.Rule("", "s8", "PM3"),
                GRM.Rule("", "s9", "BM1")])
        
        self.assertListEqual(lp_res,[
                GRM.Rule("", "s6", "PVS3"), # 1PVFS* AND 1PM*
                GRM.Rule("", "s8", "PM3")])
        
        self.assertFalse(classifier.likely_pathogenic([
             GRM.Rule("", "s1", "PVSX1"),
             GRM.Rule("", "s7", "PP6"),
             GRM.Rule("", "s8", "BS2")]))

    def test_classify_benign(self):
        classifier = ACMGClassifier2015()
        lp_res = classifier.benign([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s2", "PS4"),
                GRM.Rule("", "s3", "BAX1"),
                GRM.Rule("", "s4", "PP6"),
                GRM.Rule("", "s6", "BA3"),
                GRM.Rule("", "s7", "BS1"),
                GRM.Rule("", "s8", "BS2"),
                GRM.Rule("", "s9", "PM1")])
        self.assertListEqual(lp_res,
            [GRM.Rule("", "s3", "BAX1"), # >=1BA* OR >=2BS*
             GRM.Rule("", "s6", "BA3"),
             GRM.Rule("", "s1", "BS2"),
             GRM.Rule("", "s7", "BS1"),
             GRM.Rule("", "s8", "BS2")])
        
        self.assertFalse(classifier.benign([
             GRM.Rule("", "s1", "PP7"),
             GRM.Rule("", "s7", "PP6"),
             GRM.Rule("", "s8", "BS2")]))
        
    def test_classify_likely_benign(self):
        classifier = ACMGClassifier2015()
        lp_res = classifier.likely_benign([
                GRM.Rule("", "s1", "PP2"),
                GRM.Rule("", "s2", "PS4"),
                GRM.Rule("", "s3", "BS2"),
                GRM.Rule("", "s4", "PP6"),
                GRM.Rule("", "s6", "BA3"),
                GRM.Rule("", "s9", "BP3")])
        self.assertListEqual(lp_res,
            [GRM.Rule("", "s3", "BS2"), # 1BS* AND 1BP*
             GRM.Rule("", "s9", "BP3")])

        lp_res = classifier.likely_benign([
                GRM.Rule("", "s1", "BP2"),
                GRM.Rule("", "s2", "PS4"),
                GRM.Rule("", "s4", "PP6"),
                GRM.Rule("", "s6", "BA3"),
                GRM.Rule("", "s9", "BP3")])
        self.assertListEqual(lp_res,
            [GRM.Rule("", "s1", "BP2"), # >=2BP*
             GRM.Rule("", "s9", "BP3")])

        self.assertFalse(classifier.likely_benign([
             GRM.Rule("", "s1", "PP7"),
             GRM.Rule("", "s7", "PP6"),
             GRM.Rule("", "s8", "BS2")]))

    def test_classify_composite_rules(self):
        classifier = ACMGClassifier2015()
        r1 = GRM.Rule("", "s6", "r_BA3_1")
        r2 = GRM.Rule("", "s7", "r_BA3_2")
        lp_res = classifier.benign([
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s2", "PS4"),
                GRM.Rule("", "s4", "PP6"),
                r1,
                r2,
                GRM.AllRule([r1.code, r2.code], None, "BA3"),
                GRM.Rule("", "s9", "PM1")])
        self.assertListEqual(lp_res,
            [GRM.AllRule([r1.code, r2.code], None, "BA3")])

    def test_contradict(self):
        classifier = ACMGClassifier2015()
        pathogenic = [GRM.Rule("", "s3", "PVS1"),
                      GRM.Rule("", "s4", "PS3")]
        likely_pathogenic = [GRM.Rule("", "s2", "PS4"),
            GRM.Rule("", "s9", "PM1"),
            GRM.Rule("", "s2", "PS4"),
            GRM.Rule("", "s3", "PP4"),
            GRM.Rule("", "s4", "PP6"),
            GRM.Rule("", "s7", "PP3")]
        benign = [GRM.Rule("", "s6", "BA3"),
             GRM.Rule("", "s1", "BS2"),
             GRM.Rule("", "s7", "BS1"),
             GRM.Rule("", "s8", "BS2")]
        likely_benign = [GRM.Rule("", "s3", "BS2"),
                        GRM.Rule("", "s9", "BP3")]
        cont = classifier.contradict(pathogenic, [], benign, [])
        self.assertEquals(cont, (pathogenic + benign, "Contradiction"))
        
        cont = classifier.contradict([], likely_pathogenic, [], likely_benign)
        self.assertEquals(cont, (likely_pathogenic + likely_benign, "Contradiction"))

        cont = classifier.contradict([], likely_pathogenic, benign, [])
        self.assertEquals(cont, (likely_pathogenic + benign, "Contradiction"))
        
        self.assertEquals(classifier.contradict([], [], benign, likely_benign), (None, None))
        self.assertEquals(classifier.contradict([], [], [], likely_benign), (None, None))

    def test_classify(self):
        classifier = ACMGClassifier2015()

        passed = [GRM.Rule("", "s1", "PVS1"),
                  GRM.Rule("", "s2", "PS2"),
                  GRM.Rule("", "s3", "BA1")]
        self.assertEquals(classifier.classify(passed), ClassificationResult(3, "Uncertain significance",
                 [GRM.Rule("", "s1", "PVS1"),
                  GRM.Rule("", "s2", "PS2"),
                  GRM.Rule("", "s3", "BA1")
                  ], "Contradiction"))

        passed = [GRM.Rule("", "s1", "BS2"), 
                  GRM.Rule("", "s3", "PVS1"), 
                  GRM.Rule("", "s4", "PS3"), 
                  GRM.Rule("", "s5", "PS3"), 
                  GRM.Rule("", "s6", "PS3"), 
                  GRM.Rule("", "s7", "PP1")]
        self.assertEquals(classifier.classify(passed), ClassificationResult(5, "Pathogenic",
            [GRM.Rule("", "s3", "PVS1"),
            GRM.Rule("", "s4", "PS3"),
            GRM.Rule("", "s5", "PS3"),
            GRM.Rule("", "s6", "PS3"),
            GRM.Rule("", "s4", "PS3"),
            GRM.Rule("", "s5", "PS3"),
            GRM.Rule("", "s6", "PS3")
            ], "Pathogenic"))
        
        passed = [GRM.Rule("", "s1", "BS2"), 
                  GRM.Rule("", "s3", "PVS1"), 
                  GRM.Rule("", "s5", "PM3")]
        self.assertEquals(classifier.classify(passed), ClassificationResult(4, "Likely pathogenic",
            [GRM.Rule("", "s3", "PVS1"),
            GRM.Rule("", "s5", "PM3")
            ], "Likely pathogenic"))
        
        passed = [
                GRM.Rule("", "s1", "BS2"),
                GRM.Rule("", "s3", "PP4"),
                GRM.Rule("", "s4", "PP6"),
                GRM.Rule("", "s6", "BA3"),
                GRM.Rule("", "s7", "BS1"),
                GRM.Rule("", "s8", "BS2"),
                GRM.Rule("", "s9", "PM1")]
        self.assertEquals(classifier.classify(passed), ClassificationResult(1, "Benign",
            [GRM.Rule("", "s6", "BA3"),
             GRM.Rule("", "s1", "BS2"),
             GRM.Rule("", "s7", "BS1"),
             GRM.Rule("", "s8", "BS2")
             ], "Benign"))
        
        passed = [
                GRM.Rule("", "s3", "BP4"),
                GRM.Rule("", "s4", "BP6"),
                GRM.Rule("", "s9", "PM1")]
        self.assertEquals(classifier.classify(passed), ClassificationResult(2, "Likely benign",
            [GRM.Rule("", "s3", "BP4"),
             GRM.Rule("", "s4", "BP6")
             ], "Likely benign"))

        passed = [
                GRM.Rule("", "s4", "BP6"),
                GRM.Rule("", "s9", "PM1")]
        self.assertEquals(classifier.classify(passed), ClassificationResult(3, "Uncertain significance",
            [], "None"))
