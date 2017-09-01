import re
from itertools import takewhile
from functools import reduce
import logging

"""
GenAP Rule Classifier, GRC

Creates the final ACMG classification based on result from the GRE rule engine.
Uses regexp programs to represent code patterns.
"""
class ACMGClassifier2015:

    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger("test_1")
    
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
        
        codes_by_precedence = self.filter_out_criteria_with_lower_precedense(passed_codes)
        
         # Special rule for AMG, not official ACMG guidelines
        likely_benign_amg = self.likely_benign_amg(codes_by_precedence)
        pathogenic = self.pathogenic(codes_by_precedence)
        likely_pathogenic = self.likely_pathogenic(codes_by_precedence)
        benign = self.benign(codes_by_precedence)
        likely_benign = self.likely_benign(codes_by_precedence)
        contradiction = self.contradict(codes_by_precedence)
        
        if contradiction:
            return ClassificationResult(3, "Uncertain significance", contradiction, "Contradiction")
        if benign:
            return ClassificationResult(1, "Benign", benign, "Benign")
        if likely_benign_amg:
            return ClassificationResult(2, "Likely benign", likely_benign_amg, "Likely benign")
        if pathogenic:
            return ClassificationResult(5, "Pathogenic", pathogenic, "Pathogenic")
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
    The occurences matching the given pattern in the codes list. Each occurence
    of a specific code is only counted once.
    """
    def occurences(self, pattern, codes):
        occ = set()
        for code in codes:
            if pattern.match(code):
                occ.add(code)
        return sorted(list(occ))
    
    def find_highest_precedense(self, a, b):
        precedense = ["PVS", "PS", "PM", "PP", "BA", "BS", "BP"]
        if(precedense.index(a) < precedense.index(b)):
            return a
        else:
            return b
        
    def has_higher_precedense(self, a_criteria, b_criteria):   
        # The presedence is given by this order
        # The criteria with lowest index thus has the highest precedense
        precedense = ["PVS", "PS", "PM", "PP", "BA", "BS", "BP"]
        
        # extracting numbers from criterias so it is possible to 
        # do lookup in precedense list using index
        a = ''.join(takewhile(lambda x: not x.isdigit(), a_criteria))
        b = ''.join(takewhile(lambda x: not x.isdigit(), b_criteria))
        
        if "x" in a and "x" in b:
            # Exploiting the fact that derived codes are 
            # always written like this: [PVS/PS/PM/PP/BP/BS/BA]x[source]
            derivedA, sourceA = a.split("x")
            derivedB, sourceB = b.split("x")
            
            ah = self.find_highest_precedense(sourceA, derivedA)
            bh = self.find_highest_precedense(sourceB, derivedB)
            
            if(self.has_higher_precedense(ah, bh)):
                return True
            else: 
                return False
        
        if "x" in a:
            return not self.has_higher_precedense(b_criteria, a_criteria)
        
        if "x" in b:
            derivedB, sourceB = b.split("x")
            if(self.has_higher_precedense(sourceB, derivedB)):
              return True
            else:
              return False  
        
        # The criteria with the lowest index has the highest precedense
        if precedense.index(a) < precedense.index(b):
          return True
        else:
            return False
    
    def find_source_criteria(self, criteria):
        derived = criteria.split("x")
        if len(derived) == 1:
            return criteria
        else:
            return derived[1]
        
    def select_criteria_by_precedense(self, existing_sources, source, selectedCriteria):
        if len(existing_sources) == 0:
            return existing_sources + [selectedCriteria]
        elif self.has_higher_precedense(selectedCriteria, existing_sources[0]):
            low_precedense_removed = filter(lambda x: source not in x, existing_sources)
            return [selectedCriteria] + low_precedense_removed
        else:
            return existing_sources
        
    def handle_criteria(self, accum, criteria):
        if len(accum) == 0:
            return accum + [criteria]
        else:
            source_criteria = self.find_source_criteria(criteria)
            existing_criterias_of_this_kind = filter(lambda x: source_criteria in x, accum)
            other_criterias = filter(lambda x: source_criteria not in x, accum)
            return other_criterias + self.select_criteria_by_precedense(existing_criterias_of_this_kind, source_criteria, criteria)
            
    def filter_out_criteria_with_lower_precedense(self, criterias):
        return reduce(lambda accum, criteria: self.handle_criteria(accum, criteria), criterias, [])
         
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
