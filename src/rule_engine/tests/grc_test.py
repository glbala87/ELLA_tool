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
                                                                ["PM1",
                                                                 "PM3"])

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
                                                                ["PP1", # The first of the PP3s returned.
                                                                 "PP2",
                                                                 "PP3"])

        self.assertListEqual(classifier.occurences(re.compile("PP.*"), ["BS2",
                                                                 "PP3",
                                                                 "BS4",
                                                                 "PVS1",
                                                                 "PVS3",
                                                                 "PM3",
                                                                 "PP3",
                                                                 "PP1",
                                                                 "PP1"]),
                                                                ["PP1", # The first of the PP3s returned.
                                                                 "PP3"])

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
                                                                ["BP3",
                                                                 "BP4"])
        
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
            "PS3", # Then >=2 PS*, because of not shortcut/conversion to set:
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
            "PM1",
            "PM2",
            "PP1",
            "PP3"
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
            "PP1",
            "PP3",
            "PP4",
            "PP6"
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
            "PP3",
            "PP4",
            "PP6"
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
                
        expected =  ['PS4', # First 1PS* AND 1PM*
                    'PM1',
                    'PS4', # Then 1PS* AND >=2PP*
                    'PP1',
                    'PP3',
                    'PP4',
                    'PP6',
                    'PM1', # Then 1PM* AND >=4PP*
                    'PP1',
                    'PP3',
                    'PP4',
                    'PP6']
                    
        self.assertListEqual(lp_res, expected)
     
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
            "PP1",
            "PP3",
            "PP4",
            "PP6"
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

        self.assertTrue(classifier.likely_pathogenic([
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
            ["BA3", 
             "BAX1", # >=1BA* OR >=2BS*
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
        self.assertEquals(contributors, ["PVS1", "PS3", "PP1", "BS2"])

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
            "PP1",
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
             "PP4",
             "PP6",
             "BA3",
             "BS1",
             "BS2"
             ], "Contradiction")
        self.assertEquals(result.contributors, expected.contributors)

        passed = [
                "BP4",
                "BP6",
                "PM1"]
        self.assertEquals(classifier.classify(passed), ClassificationResult(3, "Uncertain significance",
            ["PM1",
             "BP4",
             "BP6"
             ], "Contradiction"))

        passed = [
                "PM1",
                "BP6",
                "PP6",                
                "BP7"]        
        self.assertEquals(classifier.classify(passed), 
            ClassificationResult(3, "Uncertain significance",
                [
                "PM1",
                "PP6",
                "BP6",
                "BP7"], 
                "Contradiction"
                )
            )
            
        passed = [
                "BS1",
                "BP6",
                "PP6",                
                "BP7"]        
        self.assertEquals(classifier.classify(passed), 
            ClassificationResult(3, "Uncertain significance",
                ["PP6",
                 "BS1",
                 "BP6",
                 "BP7"
                ], "Contradiction"))

        passed = [
                "BP6",
                "PM1"]
        self.assertEquals(classifier.classify(passed), ClassificationResult(3, "Uncertain significance",
            ["PM1",
             "BP6"
            ], "Contradiction"))
            
        
    def test_presedence(self):    
        classifier = ACMGClassifier2015()
        self.assertEquals(classifier._has_higher_precedence("PVS1", "PS1"), True)
        self.assertEquals(classifier._has_higher_precedence("PS1", "PVS1"), False)
        self.assertEquals(classifier._has_higher_precedence("PS3", "PMxPS3"), True)
        self.assertEquals(classifier._has_higher_precedence("PMxPS3", "PS3"), False)
        self.assertEquals(classifier._has_higher_precedence("PMxPS3", "PVSxPS3"), False)
        self.assertEquals(classifier._has_higher_precedence("PVSxPS3", "PMxPS3"), True)
        self.assertEquals(classifier._has_higher_precedence("PVS1", "PVSxPS3"), True)
        self.assertEquals(classifier._has_higher_precedence("PVSxPS3", "PVS1"), False)
        
    def test_find_base_code(self):    
        classifier = ACMGClassifier2015()
        self.assertEquals(classifier.find_base_code("PMxPS1"), "PS1")
        self.assertEquals(classifier.find_base_code("PS1"), "PS1")
        
    def test_normalize_codes(self):    
        classifier = ACMGClassifier2015()
        
        self.assertEquals(classifier.normalize_codes(
                ["PM1", "PVSxPM1", "PS3", "PMxPS3"]), ["PVSxPM1", "PS3"])
                
        # Tests data below are given by domain expert Morten Eike
        self.assertEquals(classifier.normalize_codes(
            # Duplicates PP1 is filtered out
            ["PM1", "PP1", "PP1", "PP2", "PP3"]), ["PM1", "PP1", "PP2", "PP3"])
            
        self.assertEquals(classifier.normalize_codes(
            # PM1 takes precedence above PPxPM1, hence PPxPM1 gets filtered out
            ["PM1", "PP1", "PP2", "PP3", "PPxPM1"]), ["PP1", "PP2", "PP3", "PM1"])
        
        self.assertEquals(classifier.normalize_codes(
            # PM1 takes precedence above PPxPM1, hence PPxPM1 gets filtered out
            ["PMxPP1", "PM1", "PP1", "PP2", "PPxPS1"]), ["PM1", "PMxPP1", "PP2", "PPxPS1"])
            
        self.assertEquals(classifier.normalize_codes(
            # PSxPM1 takes precedence above PS1, hence PS1 gets filtered out
            ["PSxPM1", "PS1", "PM1"]), ["PS1", "PSxPM1"])
            
        self.assertEquals(classifier.normalize_codes(
            # BSxBP1 takes precedence above BS1, hence BP1 gets filtered out
            ["BSxBP1", "BP1", "BS1"]), ["BSxBP1", "BS1"])
        
        self.assertEquals(classifier.normalize_codes(
            ["BS1", "BS2"]), ["BS1", "BS2"])
            
        self.assertEquals(classifier.normalize_codes(
            ["PVS1", "BA1"]), ["PVS1", "BA1"])    
            
    def test_classification_codes_with_precedence(self):        
        classifier = ACMGClassifier2015()
        
        case1 = classifier.classify(["PM1", "PP1", "PP1", "PP2", "PP3"])
        
        # Tests below are given by domain expert Morten Eike
        self.assertEquals(case1.clazz, 3)
        self.assertEquals(case1.contributors, [])
            
        case2 = classifier.classify(["PM1", "PP1", "PP2", "PP3", "PPxPM1"])    
        self.assertEquals(case2.clazz, 3)
        self.assertEquals(case2.contributors, [])
        
        case3 = classifier.classify(["PMxPP1", "PM1", "PP1", "PP2", "PPxPS1"])
        self.assertEquals(case3.clazz, 4)
        self.assertEquals(case3.contributors, ["PM1", "PMxPP1", "PP1" , "PP2", "PPxPS1"])

        case4 = classifier.classify(["PSxPM1", "PS1", "PM1"]) 
        self.assertEquals(case4.clazz, 5)
        # 2*PS will short circuit PM according to the rule,
        # thus PM will not be counted as a contributor
        self.assertEquals(case4.contributors, ["PS1", "PSxPM1"])
            
        case5 = classifier.classify(["BSxBP1", "BP1", "BS1"])
        self.assertEquals(case5.clazz, 1)
        # 2*BS is the rule for benign, BP1 will not be counted and 
        # therefore BP1 is not a contributor
        self.assertEquals(case5.contributors, ["BS1", "BSxBP1"])
        
        case6 = classifier.classify(["BS1", "BS2"])
        self.assertEquals(case6.clazz, 1)
        self.assertEquals(case6.contributors, ["BS1", "BS2"])
        
        case7 = classifier.classify(["PVS1", "BA1"])
        self.assertEquals(case7.clazz, 3)
        self.assertEquals(case7.contributors, ["PVS1", "BA1"])