from .. grc import ACMGClassifier2015,ClassificationResult
from .. grm import GRM
import unittest
import re

class ACMGClassifier2015Test(unittest.TestCase):

    def test_count_occurences(self):
        classifier = ACMGClassifier2015()
        self.assertListEqual(classifier.occurences(re.compile("PVS1"), ["PVS1"]), ["PVS1"])
        self.assertListEqual(classifier.occurences(re.compile("PVS1"), ["PVS2", "BP1"]), [])
        self.assertListEqual(classifier.occurences(re.compile("PS1"), []), [])
        self.assertListEqual(classifier.occurences(re.compile("PVS.*"), ["PVS1"]), ["PVS1"])
        self.assertListEqual(classifier.occurences(re.compile("PVS.*"), ["PVS1",
                                                                  "PVS3"]),
                                                                 ["PVS1",
                                                                  "PVS3"])
        self.assertListEqual(classifier.occurences(re.compile("PVS.*"), ["PVS1",
                                                                  "PVS3",
                                                                  "PP1"]),
                                                                 ["PVS1",
                                                                  "PVS3"])
        self.assertListEqual(classifier.occurences(re.compile("PM.*"), ["BS2",
                                                                 "BS4",
                                                                 "PVS1",
                                                                 "PVS3",
                                                                 "PM3",
                                                                 "PP2"]),
                                                                ["PM3"])

        self.assertListEqual(classifier.occurences(re.compile("PM.*"), ["BS2",
                                                                 "PM3",
                                                                 "BS4",
                                                                 "PVS1",
                                                                 "PVS3",
                                                                 "PM3",
                                                                 "PP2",
                                                                 "PM1"]),
                                                                ["PM3",
                                                                 "PM3",
                                                                 "PM1"])

    def test_count_occurences_special_cases(self):
        classifier = ACMGClassifier2015()

        self.assertListEqual(classifier.occurences(re.compile("PP.*"), ["BS2",
                                                                 "PP3",
                                                                 "BS4",
                                                                 "PVS1",
                                                                 "PVS3",
                                                                 "PM3",
                                                                 "PP3",
                                                                 "PP1",
                                                                 "PP2"]),
                                                                ["PP3", # The first of the PP3s returned.
                                                                 "PP1",
                                                                 "PP2"])

        self.assertListEqual(classifier.occurences(re.compile("PP.*"), ["BS2",
                                                                 "PP3",
                                                                 "BS4",
                                                                 "PVS1",
                                                                 "PVS3",
                                                                 "PM3",
                                                                 "PP3",
                                                                 "PP1",
                                                                 "PP1"]),
                                                                ["PP3", # The first of the PP3s returned.
                                                                 "PP1",
                                                                 "PP1"])

        self.assertListEqual(classifier.occurences(re.compile("BP.*"), ["BP4",
                                                                 "PP3",
                                                                 "BP4",
                                                                 "PVS3",
                                                                 "PVS3",
                                                                 "PM3",
                                                                 "BP3",
                                                                 "PP1",
                                                                 "PP1",
                                                                 "BP4",
                                                                 "BP4"]),
                                                                ["BP4",
                                                                 "BP3"])

        self.assertListEqual(classifier.occurences(re.compile("BS.*"), ["BS1",
                                                                 "BS1",
                                                                 "BP4",
                                                                 "PVS3",
                                                                 "PVS3",
                                                                 "PM3",
                                                                 "BP3",
                                                                 "PP1",
                                                                 "PP1",
                                                                 "BP4",
                                                                 "BP4"]),
                                                                ["BS1"])

    def test_classify_pathogenic(self):
        classifier = ACMGClassifier2015()
        path_res = classifier.pathogenic(["BS2",
                "BS4",
                "PVS1",
                "BP7",
                "PS3",
                "PP1"])
        self.assertListEqual(path_res,
                               ["PVS1", # 1PVS* AND >=1PS*
                                "PS3"])

        path_res = classifier.pathogenic(["BS2",
                "PVS1",
                "BS4",
                "PVSX1"])
        self.assertListEqual(path_res,
                               ["PVS1", # >=2PVS*
                                "PVSX1"])

        path_res = classifier.pathogenic([
                "BS2",
                "BS4",
                "PVS1",
                "PS3",
                "PS3",
                "PS3",
                "PP1"])
        self.assertListEqual(path_res,
            ["PVS1", # First 1PVS* AND >=1PS*
            "PS3",
            "PS3",
            "PS3",
            "PS3", # Then >=2 PS*, because of not shortcut/conversion to set:
            "PS3",
            "PS3"
            ])

        path_res = classifier.pathogenic([
                "BS2",
                "PS4",
                "PM2",
                "PM1",
                "BA3",
                "PP3",
                "PP1"])
        self.assertListEqual(path_res,
            ["PS4", # 1PS* AND 2PM* AND >=2PP*
            "PM2",
            "PM1",
            "PP3",
            "PP1"
            ])

        path_res = classifier.pathogenic([
                "BS2",
                "PS4",
                "PP4",
                "PP6",
                "PP1",
                "BA3",
                "PP3",
                "PP3",
                "PM1"])
        self.assertListEqual(path_res,
            ["PS4", # 1PS* AND 1PM* AND >=4PP*
            "PM1",
            "PP4",
            "PP6",
            "PP1",
            "PP3"
            ])

        self.assertFalse(classifier.pathogenic([
                "BS2",
                "PS4",
                "PP4",
                "PP6",
                "BA3",
                "PP3",
                "PP3",
                "PM1"]))

        self.assertFalse(classifier.pathogenic([
                "BS2",
                "PP4",
                "PP1",
                "PP6",
                "BA3",
                "PP3",
                "PP3",
                "PM1"]))

    def test_classify_likely_pathogenic(self):
        classifier = ACMGClassifier2015()
        lp_res = classifier.likely_pathogenic([
                "BS2",
                "PS4",
                "PP4",
                "PP6",
                "BA3",
                "PP3",
                "PP3",
                "PM1"])
        self.assertListEqual(lp_res,
            ["PS4", # 1PS* AND 1PM*
            "PM1",
            "PS4", # 1PS* AND >=2PP*
            "PP4",
            "PP6",
            "PP3"
            ])

        lp_res = classifier.likely_pathogenic([
                "BS2",
                "PS4",
                "PP4",
                "PP6",
                "PP1",
                "BA3",
                "PP3",
                "PP3",
                "PM1"])
        self.assertListEqual(lp_res,
            ["PS4", # First 1PS* AND 1PM*
            "PM1",
            "PS4", # Then 1PS* AND >=2PP*
            "PP4",
            "PP6",
            "PP1",
            "PP3",
            "PM1", # Then 1PM* AND >=4PP*
            "PP4",
            "PP6",
            "PP1",
            "PP3"
            ])

        lp_res = classifier.likely_pathogenic([
                "BS2",
                "PP4",
                "PP6",
                "PP1",
                "BA3",
                "PP3",
                "PP3",
                "PM1"])
        self.assertListEqual(lp_res,
            ["PM1", # 1PM* AND >=4PP*
            "PP4",
            "PP6",
            "PP1",
            "PP3"
            ])

        lp_res = classifier.likely_pathogenic([
                "BS2",
                "BP4",
                "BP6",
                "BP1",
                "PVS3",
                "BP3",
                "PM3",
                "BM1"])

        self.assertListEqual(lp_res,[
                "PVS3", # 1PVFS* AND 1PM*
                "PM3"])

        self.assertFalse(classifier.likely_pathogenic([
             "PVSX1",
             "PP6",
             "BS2"]))

    def test_classify_benign(self):
        classifier = ACMGClassifier2015()
        lp_res = classifier.benign([
                "BS2",
                "PS4",
                "BAX1",
                "PP6",
                "BA3",
                "BS1",
                "BS2",
                "PM1"])
        self.assertListEqual(lp_res,
            ["BAX1", # >=1BA* OR >=2BS*
             "BA3",
             "BS2",
             "BS1",
             "BS2"])

        self.assertFalse(classifier.benign([
             "PP7",
             "PP6",
             "BS2"]))

    def test_classify_likely_benign(self):
        classifier = ACMGClassifier2015()
        lp_res = classifier.likely_benign([
                "PP2",
                "PS4",
                "BS2",
                "PP6",
                "BA3",
                "BP3"])
        self.assertListEqual(lp_res,
            ["BS2", # 1BS* AND 1BP*
             "BP3"])

        lp_res = classifier.likely_benign([
                "BP2",
                "PS4",
                "PP6",
                "BA3",
                "BP3"])
        self.assertListEqual(lp_res,
            ["BP2", # >=2BP*
             "BP3"])

        self.assertFalse(classifier.likely_benign([
             "PP7",
             "PP6",
             "BS2"]))

    def test_contradict(self):
        classifier = ACMGClassifier2015()
        pathogenic = ["PVS1",
            "PS3"]
        likely_pathogenic = ["PS4",
            "PM1",
            "PS4",
            "PP4",
            "PP6",
            "PP3"]
        benign = ["BA3",
            "BS2",
            "BS1",
            "BS2"]
        likely_benign = ["BS2",
            "BP3"]
        contradict = ["BS2",
            "PVS1",
            "PM3"]
        contradict2 = ["BS2",
                  "PVS1",
                  "PS3",
                  "PS3",
                  "PS3",
                  "PP1"]              
        contributors = classifier.contradict(pathogenic)
        self.assertEquals(contributors, [])
        
        contributors = classifier.contradict(likely_pathogenic)
        self.assertEquals(contributors, [])

        contributors = classifier.contradict(benign)
        self.assertEquals(contributors, [])

        contributors = classifier.contradict(likely_benign)
        self.assertEquals(contributors, [])
        
        contributors = classifier.contradict(contradict)
        self.assertEquals(contributors, ["PVS1", "PM3", "BS2"])
        
        contributors = classifier.contradict(contradict2)
        self.assertEquals(contributors, ["PVS1", "PS3", "PS3", "PS3", "BS2"])

    def test_classify(self):
        classifier = ACMGClassifier2015()

        passed = ["PVS1",
                  "PS2",
                  "BA1"]
        self.assertEquals(classifier.classify(passed), ClassificationResult(3, "Uncertain significance",
                 ["PVS1",
                  "PS2",
                  "BA1"
                  ], "Contradiction"))

        passed = ["BS2",
                  "PVS1",
                  "PS3",
                  "PS3",
                  "PS3",
                  "PP1"]
        
        self.assertEquals(classifier.classify(passed), ClassificationResult(3, "Uncertain significance",
            ["PVS1",
            "PS3",
            "PS3",
            "PS3",
            "BS2"], "Contradiction"))
        
        passed = ["BS2",
                  "PVS1",
                  "PM3"]
        result = classifier.classify(passed)
        
        expected = ClassificationResult(3, "Uncertain significance",
            ["PVS1",
            "PM3", 
            "BS2"
            ], "Contradiction")
        
        self.assertEquals(result.message, expected.message)
    
        passed = [
                "BS2",
                "PP4",
                "PP6",
                "BA3",
                "BS1",
                "BS2",
                "PM1"]
                
        result = classifier.classify(passed)
        expected = ClassificationResult(3, "Uncertain significance",
            ["PM1",
             "BA3",
             "BS2",
             "BS1",
             "BS2"
             ], "Contradiction")
        self.assertEquals(result.contributors, expected.contributors)

        passed = [
                "BP4",
                "BP6",
                "PM1"]
        self.assertEquals(classifier.classify(passed), ClassificationResult(2, "Likely benign",
            ["BP4",
             "BP6"
             ], "Likely benign"))

        passed = [
                "BP6",
                "PM1"]
        self.assertEquals(classifier.classify(passed), ClassificationResult(3, "Uncertain significance",
            [], "None"))
