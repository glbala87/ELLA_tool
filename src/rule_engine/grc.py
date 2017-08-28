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
    ACMG guideline: "If multiple pieces of evidence point to the same basic argument, only the strongest
    piece of eveidence is considered". This is relevant especially for the use of derived codes (with "x").
    If original AND derived code, use strongest ONLY. 
    
    Order of precedence:
    PVS > PS > PM and BA > BS > BP
    
    Examples:
    PS3 and PMxPS3 => use PS3 only
    PSxPM1 and PM1 => use PSxPM1 only
    """
    def normalize_pathogenic(self, occ):
        pvs = self.collect_pattern(occ, re.compile(".*PVS.*"))
        
        if pvs:
            relevant_criterias = self.exclude_patterns(occ, [re.compile(".*PVS.*"), re.compile(".*PS.*"), re.compile(".*PM.*")])
            return pvs + relevant_criterias
        
        ps = self.collect_pattern(occ, re.compile(".*PS.*"))
        
        if ps:
            relevant_criterias = self.exclude_patterns(occ, [re.compile(".*PS.*"), re.compile(".*PM.*")])
            return ps + relevant_criterias
        
        pm = self.collect_pattern(occ, re.compile(".*PM.*"))
        
        if pm:
            relevant_criterias = self.exclude_patterns(occ, [re.compile(".*PM.*")])
            return pm + relevant_criterias
        
        return occ

    """
    See documenation on the function normalize_pathogenic
    """
    def normalize_benign(self, occ):    
        ba = self.collect_pattern(occ, re.compile(".*BA.*"))
        
        if ba:
            relevant_criterias = self.exclude_patterns(occ, [re.compile(".*BA.*"), re.compile(".*BS.*"), re.compile(".*BP.*")])
            return ba + relevant_criterias
        
        bs = self.collect_pattern(occ, re.compile(".*BS.*"))
        
        if bs:
            relevant_criterias = self.exclude_patterns(occ, [re.compile(".*BS.*"), re.compile(".*BP.*")])
            return bs + relevant_criterias
        
        bp = self.collect_pattern(occ, re.compile(".*BP.*"))
        
        if bp:
            relevant_criterias = self.exclude_patterns(occ, [re.compile(".*BP.*")])
            return bp + relevant_criterias
        
        return occ

    """
    Collect all items in a list given a reg exp pattern
    """
    def collect_pattern(self, lst, pattern):
        result = []
        for el in lst:
            if pattern.match(el):
                result.append(el)
        return result
    
    def exclude_patterns(self, lst, patterns):    
        result = []
        for el in lst:
            exists = []
            for p in patterns:
                if p.match(el):
                    exists.append(p)
            if not exists:
                result.append(el)
        return result
    
    """
    The occurences matching the given pattern in the codes list. Each occurence
    of a specific code is only counted once.
    """
    def occurences(self, pattern, codes):
        occ = set()
        for code in codes:
            if pattern.match(code):
                occ.add(code)
                
        pathogenic = self.normalize_pathogenic(list(occ))        
        benign = self.normalize_benign(list(occ))
        return pathogenic + benign
            

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
