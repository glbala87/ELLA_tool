import re

"""
GenAP Rule Classifier, GRC

Creates the final ACMG classification based on result from the GRE rule engine.
Uses regexp programs to represent code patterns.
"""
class ACMGClassifier2015:

    # Regexp patterns
    PVS = re.compile("PVS.*")
    PS = re.compile("PS.*")
    PM = re.compile("PM.*")
    PP = re.compile("PP.*")
    BA = re.compile("BA.*")
    BS = re.compile("BS.*")
    BP = re.compile("BP.*")
    
    """
    Patterns only used in special AMG rule
    """
    BS1 = re.compile("BS1")
    BS2 = re.compile("BS2")
    BP7 = re.compile("BP7")
    
    """
    Call with a list of passed codes to get the correct ClassificationResult.
    """
    def classify(self, passed_codes):
         # Special rule for AMG, not official ACMG guidelines
        likely_benign_amg = self.likely_benign_amg(passed_codes)
        pathogenic = self.pathogenic(passed_codes)
        likely_pathogenic = self.likely_pathogenic(passed_codes)
        benign = self.benign(passed_codes)
        likely_benign = self.likely_benign(passed_codes)
        contradiction = self.contradict(passed_codes)
        if contradiction:
            return ClassificationResult(3, "Uncertain significance", contradiction, "Contradiction")
        if likely_benign_amg:
            return ClassificationResult(2, "Likely benign", likely_benign_amg, "Likely benign")
        if pathogenic:
            return ClassificationResult(5, "Pathogenic", pathogenic, "Pathogenic")
        if benign:
            return ClassificationResult(1, "Benign", benign, "Benign")
        if likely_pathogenic:
            return ClassificationResult(4, "Likely pathogenic", likely_pathogenic, "Likely pathogenic")
        if likely_benign:
            return ClassificationResult(2, "Likely benign", likely_benign, "Likely benign")
        return ClassificationResult(3, "Uncertain significance", [], "None")

    """
    If the codes given satisfy the speical AMG requirements for likely benign, return list of all codes
    contributing otherwise empty list.
    """
    def likely_benign_amg(self, codes):
        return(
            self._OR(
                self.contrib(self.BS1, codes, lambda n : n >= 1),
                self.contrib(self.BS2, codes, lambda n : n >= 1),
                self.contrib(self.BP7, codes, lambda n : n >= 1)
            )
        )

    """
    If the codes given satisfy the requirements for pathogenic, return list of all codes contributing, otherwise
    empty list.
    """
    def pathogenic(self, codes):
        return (
        self._OR(
            self.contrib(self.PVS, codes, lambda n : n >= 2),
            self._AND(
                      self.contrib(self.PVS, codes, lambda n : n == 1),
                      (self._OR(
                                self.contrib(self.PS, codes, lambda n : n >= 1),
                                self.contrib(self.PM, codes, lambda n : n >= 2),
                                self._AND(
                                          self.contrib(self.PM, codes, lambda n : n == 1),
                                          self.contrib(self.PP, codes, lambda n : n == 1)
                                          ),
                                self.contrib(self.PP, codes, lambda n : n >= 2)
                                )
                       )
                      ),
            self.contrib(self.PS, codes, lambda n : n >= 2),
            self._AND(
                      self.contrib(self.PS, codes, lambda n : n == 1),
                      self._OR(
                               self.contrib(self.PM, codes, lambda n : n >= 3),
                               self._AND(
                                         self.contrib(self.PM, codes, lambda n : n == 2),
                                         self.contrib(self.PP, codes, lambda n : n >= 2)
                                         ),
                               self._AND(
                                         self.contrib(self.PM, codes, lambda n : n == 1),
                                         self.contrib(self.PP, codes, lambda n : n >= 4)
                                         )
                               )
                      )
                )
        )

    """
    If the codes given satisfy the requirements for likely pathogenic, return list of all codes contributing, otherwise
    empty list.
    """
    def likely_pathogenic(self, codes):
        return  (
        self._OR(
            self._AND(
                self.contrib(self.PVS, codes, lambda n: n == 1),
                self._OR(
                    self.contrib(self.PM, codes, lambda n: n == 1),
                    # NB: PVS + PP = class 4 is not based on official ACMG guidelines, but added to fill logical gap
                    self.contrib(self.PP, codes, lambda n: n >= 1)
                )
            ),            
            self._AND(
                      self.contrib(self.PS, codes, lambda n : n == 1),
                      self.contrib(self.PM, codes, lambda n : n == 1)
                      ),
            self._AND(
                      self.contrib(self.PS, codes, lambda n : n == 1),
                      self.contrib(self.PP, codes, lambda n : n >= 2)
                      ),
            self.contrib(self.PM, codes, lambda n : n >= 3),
            self._AND(
                      self.contrib(self.PM, codes, lambda n : n == 2),
                      self.contrib(self.PP, codes, lambda n : n >= 2)
                      ),
            self._AND(
                      self.contrib(self.PM, codes, lambda n : n == 1),
                      self.contrib(self.PP, codes, lambda n : n >= 4)
                      )
                )
        )

    """
    If the codes given satisfy the requirements for benign, return list of all codes contributing, otherwise
    empty list.
    """
    def benign(self, codes):
        return  (
        self._OR(
                 self.contrib(self.BA, codes, lambda n : n >= 1),
                 self.contrib(self.BS, codes, lambda n : n >= 2)
                 )
        )

    """
    If the codes given satisfy the requirements for likely benign, return list of all codes contributing, otherwise
    empty list.
    """
    def likely_benign(self, codes):
        return  (
        self._OR(
                 self._AND(
                           self.contrib(self.BS, codes, lambda n : n == 1),
                           self.contrib(self.BP, codes, lambda n : n == 1)
                           ),
                 self.contrib(self.BP, codes, lambda n : n >= 2)
                 )
        )

    """
    List-or which returns a list containing elems of all contributing lists.
    Will contain duplicates if codes may contribute to the classification in different ways.
    """
    def _OR(self, *lists):
        ret = []
        for lst in lists:
            if lst: ret.extend(lst)
        return ret

    """
    List-and which returns a list containing elems of all contributing lists.
    Will contain duplicates if codes may contribute to the classification in different ways.
    """
    def _AND(self, *lists):
        ret = []
        for lst in lists:
            if lst: ret.extend(lst)
            else: return []
        return ret

    """
    If the number of occurences of the given pattern in codes passes the given constraint, return the occurences list.
    """
    def contrib(self, pattern, codes, length_constraint):
        occ = self.occurences(pattern, codes)
        if length_constraint(len(occ)):
            return occ
        return []

    """
    All codes should be counted exactly once, hence [PM1, PM1] should be 
    counted only as one PM1. This method checks if we already have an 
    existing sample code (i.e. PM1 etc.) in the occurences list.
    """
    def occurence_has_been_counted(self, code, occurences):
        for occurence in occurences:
            if occurence == code:
                return True
        return False

    """
    The occurences matching the given pattern in the codes list.
    """
    def occurences(self, pattern, codes):
        occ = []
        
        for code in codes:
            hasBeenCounted =  self.occurence_has_been_counted(code, occ)
            if pattern.match(code) and hasBeenCounted == False:
                occ.append(code)
        return occ

    """
    If the codes given satisfy the requirements for contradiction, return list of all codes contributing, otherwise
    empty list.
    """
    def contradict(self, codes):
        return (
        self._AND(
            self._OR(
                      self.contrib(self.PVS, codes, lambda n : n >= 1),
                      self.contrib(self.PS, codes, lambda n : n >= 1),
                      self.contrib(self.PM, codes, lambda n : n >= 1),
                     ),
            self._OR(
                      self.contrib(self.BA, codes, lambda n : n >= 1),
                      self.contrib(self.BS, codes, lambda n : n >= 1),
                     )
                  )
        )
        
        
"""
Result of ACMG classification. Aggregate of classification and metadata.
"""
class ClassificationResult:

    def __init__(self, clazz, classification, contributors, message):
        self.clazz = clazz
        self.classification = classification
        self.contributors = contributors
        self.message = message
        self.meta = dict()

    def __eq__(self, other):
            return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)
