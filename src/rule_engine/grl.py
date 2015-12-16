import collections
from grm import GRM

"""
GenAP Rule Language, GRL

A JSON backed language for gene variant rules
"""
class GRL:
    
    """
    Parses a JSON object with n rules and returns a code keyed dict of lists of Rule objects
    """
    def parseRules(self, jsonobject):
        rules = collections.OrderedDict()
        for ruleblock in jsonobject:
            code = ruleblock["code"]
            rulespec = ruleblock["rule"]
            rules.setdefault(code, []).append(self.parseRule(rulespec, code))
        return rules
    
    def parseRule(self, rulebody, code, source=None, aggregate=False):
        if not isinstance(rulebody, collections.Mapping):
            # Just for example "transcript.splice.effect": "de_novo"
            return GRM.InRule([rulebody], source, code)
        for left, right in rulebody.iteritems():
            if left == "$or":
                return GRM.OrRule([self.parseRule(r, code, source, aggregate) for r in right], code, aggregate)
            elif left == "$and":
                return GRM.AndRule([self.parseRule(r, code, source, aggregate) for r in right], code, aggregate)
            elif left == "$in":
                return GRM.InRule(right,source, code)
            elif left == "$gt":
                return GRM.GtRule(right, source, code)
            elif left == "$lt":
                return GRM.LtRule(right, source, code)
            elif left == "$range":
                return GRM.RangeRule(right, source, code)
            elif left == "$not":
                return GRM.NotRule(self.parseRule(right, code, source, aggregate))
            elif left == "$all":
                return GRM.AllRule(right, source, code, aggregate)
            elif left == "$atleast":
                return GRM.AtLeastRule(right[1:], code, right[0], aggregate)
            elif left == "$$aggregate":
                return self.parseRule(right, code, source, True)
            else:
                # Left is a source
                return self.parseRule(right, code, left)
