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
        
        #TODO: check if pp also need to be implemented, although it is left out from the requirements
        #pp = self.collect_pattern(occ, re.compile(".*PP.*"))
        
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
    
    """
    Remove all items from the list that is matched in the given patterns.
    """
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
          
        # TODO:        
        # This must probably be done after the rules have been applied to make sense ...                
        # Recon they should be implemented in the contrib for the classified class
        # They don't do any impact here it seems ...
        pathogenic = self.normalize_pathogenic(list(occ))        
        pathogenic_with_benign = self.normalize_benign(pathogenic)
        
        return sorted(pathogenic_with_benign)
    
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
    
    def find_source(self, criteria):
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
        
    def handle_criteria(self, accum, selectedCriteria):
        if len(accum) == 0:
            return accum + [selectedCriteria]
        else:
            source = self.find_source(selectedCriteria)
            existing_sources = filter(lambda x: source in x, accum)
            others = filter(lambda x: source not in x, accum)
            return others + self.select_criteria_by_precedense(existing_sources, source, selectedCriteria)
            
    def filter_out_criteria_with_lower_precedense(self, criterias):
        return reduce(lambda accum, y: self.handle_criteria(accum, y), criterias, [])
       
    def has_presedence(self, a, b):    
        order_of_presedence = ["PVS", "PS", "PM", "PP", "BA", "BS", "BP"]
        index_of_a = order_of_presedence.index(a)
        index_of_b = order_of_presedence.index(b)
        if index_of_a < index_of_b:
            return True
        else:
            return False
        
    """
    Match on complex pattern, i.e. pattern = PM, we want to find the
    PSxPM1
    """
    def match_on_complex_pattern(self, pattern, code):        
        result = []
        regexp = re.compile(".*" + pattern + "\d")
        
        if regexp.match(code) and code.find('x') >= 0:
            result.append(code)
            return result
        
        return result    
            
    """
    Need to somehow count PSxPM1 instead of PM1 because this has higher 
    presedence
    """        
    def handle_presedence(self, pattern, codes):
        result = []
        
        x_pattern = re.compile("(" + pattern + "x" + ")")
        
        for code in codes:
            if self.match_on_complex_pattern(pattern, code):
                # If it has a higher presedence, add it if not ignore it
                result.append(code)
                
        return result        
            
    def occ(self, pattern, codes):
        
        any_match = re.compile(".*" + pattern + ".*")
        x_pattern = re.compile(pattern + "x")
        number_pattern = re.compile(pattern + "\d")
        
        tmp = []
        occ = set()
        for code in codes:
            if pattern.match(code):
                tmp.append(code)
                
        if len(tmp) > 1:
            for c in tmp:
                if c.find('x') == -1:
                   occ.add(c) 
            return list(occ)
        else: 
            return tmp
            
    def occ1(self, pattern, codes):
        occ = set()
        for code in codes:
            results = re.search(pattern, code)
            if results:
                occ.add(results.group(1))
        return list(occ)
            
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
