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
    Call with a list of passed rules to get the correct ClassificationResult.
    """
    def classify(self, passed_rules):
        pathogenic = self.pathogenic(passed_rules)
        likely_pathogenic = self.likely_pathogenic(passed_rules)
        benign = self.benign(passed_rules)
        likely_benign = self.likely_benign(passed_rules)
        (cont_rules, cont_message) = self.contradict(pathogenic, likely_pathogenic, benign, likely_benign)
        if cont_rules: 
            return ClassificationResult(3, "Uncertain significance", cont_rules, cont_message)
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
    If the rules given satisfy the requirements for pathogenic, return list of all rules contributing, otherwise
    empty list. 
    """
    def pathogenic(self, rules):
        return (
        self._OR(
            self.contrib(self.PVS, rules, lambda n : n >= 2),
            self._AND(
                      self.contrib(self.PVS, rules, lambda n : n == 1),
                      (self._OR(
                                self.contrib(self.PS, rules, lambda n : n >= 1),
                                self.contrib(self.PM, rules, lambda n : n >= 2),
                                self._AND(
                                          self.contrib(self.PM, rules, lambda n : n == 1),
                                          self.contrib(self.PP, rules, lambda n : n == 1)
                                          ),
                                self.contrib(self.PP, rules, lambda n : n >= 2)
                                )
                       )
                      ),
            self.contrib(self.PS, rules, lambda n : n >= 2),
            self._AND(
                      self.contrib(self.PS, rules, lambda n : n == 1),
                      self._OR(
                               self.contrib(self.PM, rules, lambda n : n >= 3),
                               self._AND(
                                         self.contrib(self.PM, rules, lambda n : n == 2),
                                         self.contrib(self.PP, rules, lambda n : n >= 2)
                                         ),
                               self._AND(
                                         self.contrib(self.PM, rules, lambda n : n == 1),
                                         self.contrib(self.PP, rules, lambda n : n >= 4)
                                         )
                               )
                      )
                )
        )

    """
    If the rules given satisfy the requirements for likely pathogenic, return list of all rules contributing, otherwise
    empty list. 
    """
    def likely_pathogenic(self, rules):
        return  (
        self._OR(
            self._AND(
                      self.contrib(self.PVS, rules, lambda n : n == 1),
                      self.contrib(self.PM, rules, lambda n : n == 1)                                
                      ),                           
            self._AND(
                      self.contrib(self.PS, rules, lambda n : n == 1),
                      self.contrib(self.PM, rules, lambda n : n == 1)                                
                      ),
            self._AND(
                      self.contrib(self.PS, rules, lambda n : n == 1),
                      self.contrib(self.PP, rules, lambda n : n >= 2)     
                      ), 
            self.contrib(self.PM, rules, lambda n : n >= 3),
            self._AND(
                      self.contrib(self.PM, rules, lambda n : n == 2),
                      self.contrib(self.PP, rules, lambda n : n >= 2)     
                      ),
            self._AND(
                      self.contrib(self.PM, rules, lambda n : n == 1),
                      self.contrib(self.PP, rules, lambda n : n >= 4)     
                      )
                )
        )

    """
    If the rules given satisfy the requirements for benign, return list of all rules contributing, otherwise
    empty list. 
    """
    def benign(self, rules):
        return  (
        self._OR(
                 self.contrib(self.BA, rules, lambda n : n >= 1),
                 self.contrib(self.BS, rules, lambda n : n >= 2)
                 )
        ) 

    """
    If the rules given satisfy the requirements for likely benign, return list of all rules contributing, otherwise
    empty list. 
    """
    def likely_benign(self, rules):
        return  (
        self._OR(
                 self._AND(
                           self.contrib(self.BS, rules, lambda n : n == 1),
                           self.contrib(self.BP, rules, lambda n : n == 1)
                           ),
                 self.contrib(self.BP, rules, lambda n : n >= 2)
                 )
        )

    """
    List-or which returns a list containing elems of all contributing lists.
    Will contain duplicates if rules may contribute to the classification in different ways. 
    """
    def _OR(self, *lists):
        ret = []
        for lst in lists:
            if lst: ret.extend(lst)
        return ret

    """
    List-and which returns a list containing elems of all contributing lists.
    Will contain duplicates if rules may contribute to the classification in different ways. 
    """
    def _AND(self, *lists):
        ret = []
        for lst in lists:
            if lst: ret.extend(lst)
            else: return []
        return ret
        
    """
    If the number of occurences of the given pattern in rules passes the given constraint, return the occurences list. 
    """
    def contrib(self, pattern, rules, length_constraint):
        occ = self.occurences(pattern, rules)
        if length_constraint(len(occ)):
            return occ
        return []
        
    """
    The occurences matching the given pattern in the rules list.
    Takes into account special counting rules for PP3 and BP4.
    """
    def occurences(self, pattern, rules):
        occ = []
        # These to be counted only once each:
        n_PP3 = 0
        n_BP4 = 0
        for rule in rules:
            code = rule.code
            if pattern.match(code):
                if code == "PP3":
                    if not n_PP3:
                        occ.append(rule)
                        n_PP3 += 1
                elif code == "BP4":
                    if not n_BP4:
                        occ.append(rule)
                        n_BP4 += 1
                else:
                    occ.append(rule)                    
        return occ

    """
    If criteria are in contradiction:
      Return tuple (contributing rules,message)
    Else
      (None, None)
    """
    def contradict(self, pathogenic, likely_pathogenic, benign, likely_benign):
        # TODO: Do we want contradiction logic on the lower rule level?
        if pathogenic and benign: return pathogenic + benign, (
                                           "Contradiction: Pathogenic/Benign. Pathogenic from sources "  +
                                           "[%s]" % ", ".join(map(str, [r.source+":"+r.code for r in pathogenic])) +
                                           ". Benign from sources " +
                                           "[%s]" % ", ".join(map(str, [r.source+":"+r.code for r in benign])) +"."
                                        )
        if not pathogenic and not benign:
            if likely_pathogenic and likely_benign: return likely_pathogenic + likely_benign, (
                                           "Contradiction: Likely pathogenic/Likely benign. Likely pathogenic from sources "  +
                                           "[%s]" % ", ".join(map(str, [r.source+":"+r.code for r in likely_pathogenic])) +
                                           ". Likely benign from sources " +
                                           "[%s]" % ", ".join(map(str, [r.source+":"+r.code for r in likely_benign])) + "."
                                        )
        return (None, None)
        
        
"""
Result of ACMG classification. Aggregate of classification and metadata.
"""
class ClassificationResult:
    clazz = None
    classification = None
    contributors = None
    message = None
    meta = dict()

    def __init__(self, clazz, classification, contributors, message):
        self.clazz = clazz
        self.classification = classification
        self.contributors = contributors
        self.message = message
        
    def __eq__(self, other):
            return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)
