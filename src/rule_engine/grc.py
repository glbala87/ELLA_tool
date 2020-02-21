import re
import logging
from functools import reduce

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
    Call with a list of passed codes to get the correct ClassificationResult.
    """

    def classify(self, passed_codes):

        codes_by_precedence = self.normalize_codes(passed_codes)

        # Rules according to the official ACMG guidelines
        pathogenic = self.pathogenic(codes_by_precedence)
        likely_pathogenic = self.likely_pathogenic(codes_by_precedence)
        benign = self.benign(codes_by_precedence)
        likely_benign = self.likely_benign(codes_by_precedence)
        contradiction = self.contradict(codes_by_precedence)

        if contradiction:
            contributors = self.contradict(passed_codes)
            return ClassificationResult(3, "Uncertain significance", contributors, "Contradiction")
        if benign:
            contributors = self.benign(passed_codes)
            return ClassificationResult(1, "Benign", contributors, "Benign")
        if pathogenic:
            contributors = self.pathogenic(passed_codes)
            return ClassificationResult(5, "Pathogenic", contributors, "Pathogenic")
        if likely_pathogenic:
            contributors = self.likely_pathogenic(passed_codes)
            return ClassificationResult(4, "Likely pathogenic", contributors, "Likely pathogenic")
        if likely_benign:
            contributors = self.likely_benign(passed_codes)
            return ClassificationResult(2, "Likely benign", contributors, "Likely benign")
        return ClassificationResult(3, "Uncertain significance", [], "None")

    """
    If the codes given satisfy the requirements for pathogenic, return list of all codes contributing, otherwise
    empty list.
    """

    def pathogenic(self, codes):
        return self._OR(
            self.contrib(self.PVS, codes, lambda n: n >= 2),
            self._AND(
                self.contrib(self.PVS, codes, lambda n: n == 1),
                (
                    self._OR(
                        self.contrib(self.PS, codes, lambda n: n >= 1),
                        self.contrib(self.PM, codes, lambda n: n >= 2),
                        self._AND(
                            self.contrib(self.PM, codes, lambda n: n == 1),
                            self.contrib(self.PP, codes, lambda n: n == 1),
                        ),
                        self.contrib(self.PP, codes, lambda n: n >= 2),
                    )
                ),
            ),
            self.contrib(self.PS, codes, lambda n: n >= 2),
            self._AND(
                self.contrib(self.PS, codes, lambda n: n == 1),
                self._OR(
                    self.contrib(self.PM, codes, lambda n: n >= 3),
                    self._AND(
                        self.contrib(self.PM, codes, lambda n: n == 2),
                        self.contrib(self.PP, codes, lambda n: n >= 2),
                    ),
                    self._AND(
                        self.contrib(self.PM, codes, lambda n: n == 1),
                        self.contrib(self.PP, codes, lambda n: n >= 4),
                    ),
                ),
            ),
        )

    """
    If the codes given satisfy the requirements for likely pathogenic, return list of all codes contributing, otherwise
    empty list.
    """

    def likely_pathogenic(self, codes):
        return self._OR(
            self._AND(
                self.contrib(self.PVS, codes, lambda n: n == 1),
                self._OR(
                    self.contrib(self.PM, codes, lambda n: n == 1),
                    # NB: PVS + PP = class 4 is not based on official ACMG guidelines, but added to fill logical gap
                    self.contrib(self.PP, codes, lambda n: n == 1),
                ),
            ),
            self._AND(
                self.contrib(self.PS, codes, lambda n: n == 1),
                self.contrib(self.PM, codes, lambda n: n == 1),
            ),
            self._AND(
                self.contrib(self.PS, codes, lambda n: n == 1),
                self.contrib(self.PP, codes, lambda n: n >= 2),
            ),
            self.contrib(self.PM, codes, lambda n: n >= 3),
            self._AND(
                self.contrib(self.PM, codes, lambda n: n == 2),
                self.contrib(self.PP, codes, lambda n: n >= 2),
            ),
            self._AND(
                self.contrib(self.PM, codes, lambda n: n == 1),
                self.contrib(self.PP, codes, lambda n: n >= 4),
            ),
        )

    """
    If the codes given satisfy the requirements for benign, return list of all codes contributing, otherwise
    empty list.
    """

    def benign(self, codes):
        return self._OR(
            self.contrib(self.BA, codes, lambda n: n >= 1),
            self.contrib(self.BS, codes, lambda n: n >= 2),
        )

    """
    If the codes given satisfy the requirements for likely benign, return list of all codes contributing, otherwise
    empty list.
    """

    def likely_benign(self, codes):
        return self._OR(
            self._AND(
                self.contrib(self.BS, codes, lambda n: n == 1),
                self.contrib(self.BP, codes, lambda n: n == 1),
            ),
            self.contrib(self.BP, codes, lambda n: n >= 2),
        )

    """
    List-or which returns a list containing elems of all contributing lists.
    Will contain duplicates if codes may contribute to the classification in different ways.
    """

    def _OR(self, *lists):
        ret = []
        for lst in lists:
            if lst:
                ret.extend(lst)
        return ret

    """
    List-and which returns a list containing elems of all contributing lists.
    Will contain duplicates if codes may contribute to the classification in different ways.
    """

    def _AND(self, *lists):
        ret = []
        for lst in lists:
            if lst:
                ret.extend(lst)
            else:
                return []
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
    The occurences matching the given pattern in the codes list. The returned list
    has only unique elements and is sorted.
    """

    @staticmethod
    def occurences(pattern, codes):
        occ = [code for code in set(codes) if pattern.match(code)]
        return sorted(occ)

    """
    Precedence for criteria, index 0 has highest precedence
    """
    precedence = ["PVS", "PS", "PM", "PP", "BA", "BS", "BP"]

    #    Help method for _has_higher_precedence, returns the criteria with highest
    #    precedence.
    #
    def _find_highest_precedence(self, code_a, code_b):
        if self.precedence.index(code_a) < self.precedence.index(code_b):
            return code_a
        return code_b

    """
    Returns True if criteria a has higher precedence than criteria b, else
    Returns False.

    Input may be normal criterias like PS1, PM1 etc. or derived criterias
    like PMxPS1, PMxPVS1 etc. They must be preselected by criteria source (done
    in __accumulate_criteria__).
    """

    def _has_higher_precedence(self, code_a, code_b):
        # extracting numbers from criterias so it is possible to
        # do lookup in precedense list using index, i.e. PS1 is
        # converted to PS.

        a = re.split(r"\d", code_a)[0]
        b = re.split(r"\d", code_b)[0]

        if "x" in a and "x" in b:
            # Exploiting the fact that derived codes are
            # always written like this: [PVS/PS/PM/PP/BP/BS/BA]x[source]
            derived_a, source_a = a.split("x")
            derived_b, source_b = b.split("x")

            ah = self._find_highest_precedence(source_a, derived_a)
            bh = self._find_highest_precedence(source_b, derived_b)

            return self._has_higher_precedence(ah, bh)

        if "x" in a:
            return not self._has_higher_precedence(code_b, code_a)

        if "x" in b:
            derived_b, source_b = b.split("x")
            bh = self._find_highest_precedence(source_b, derived_b)

            # PS3 and PMxPS3 --> use PS3 only, the PM part would be
            # filtered out in the previous step
            if a == bh:
                return True

            return self._has_higher_precedence(a, bh)

        # The criteria with the lowest index has the highest precedence
        return self.precedence.index(a) < self.precedence.index(b)

    """
    Finding the base code from the derived code, if this is not a
    derived code, the same code is returned.

    Derived codes are always written like this:
    [PVS/PS/PM/PP/BP/BS/BA]x[base]
    """

    @staticmethod
    def find_base_code(code):
        derived = code.split("x")
        if len(derived) == 1:
            return code
        return derived[1]

    #    Selecting the criteria of highest precedence
    def _select_codes_by_precedence(self, existing_codes, target_code):
        assert len(existing_codes) <= 1, (
            "Internal error when selecting criteria with highest precedence: %s, there should never be more than one criteria at this state."
            % existing_codes
        )

        try:
            existing_code = existing_codes.pop(0)
        except IndexError:
            existing_code = None

        if existing_code is None:
            return [target_code]
        elif self._has_higher_precedence(target_code, existing_code):
            return [target_code]
        else:
            return [existing_code]

    #    Accumulate criterias according to their precedence. Criterias with higher precedence
    #    are added. Already existing criterias with lower precedence are removed from the accum
    #    list.
    def _accumulate_codes(self, accum, target_code):
        if accum == []:
            return accum + [target_code]

        base_code = self.find_base_code(target_code)
        existing_codes_of_this_kind = [code for code in accum if base_code in code]
        other_codes = [code for code in accum if base_code not in code]

        return other_codes + self._select_codes_by_precedence(
            existing_codes_of_this_kind, target_code
        )

    """
    Returning a list where all codes with lower precedence are filtered out.
    """

    def normalize_codes(self, codes):
        return reduce(lambda accum, code: self._accumulate_codes(accum, code), codes, [])

    """
    If the codes given satisfy the requirements for contradiction, return list of all codes contributing, otherwise
    empty list.
    """

    def contradict(self, codes):
        return self._AND(
            self._OR(
                self.contrib(self.PVS, codes, lambda n: n >= 1),
                self.contrib(self.PS, codes, lambda n: n >= 1),
                self.contrib(self.PM, codes, lambda n: n >= 1),
                self.contrib(self.PP, codes, lambda n: n >= 1),
            ),
            self._OR(
                self.contrib(self.BA, codes, lambda n: n >= 1),
                self.contrib(self.BS, codes, lambda n: n >= 1),
                self.contrib(self.BP, codes, lambda n: n >= 1),
            ),
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
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__
