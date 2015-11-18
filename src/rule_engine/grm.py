"""
GenAP Rule Model, GRM
"""
class GRM:

    """
    Base class for rules.
    """
    class Rule:
        
        def __init__(self, value, source, code=None, aggregate=False):
            self.value = value
            self.source = source
            self.code = code
            self.aggregate = aggregate
            
        def __eq__(self, other):
            return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

        def __hash__(self):
            return hash((self.source, self.value, self.code, self.aggregate))
            
        def __str__(self):
            return self.value + " " + self.source + " " + self.code
        """
        Applies this rule to some data. The return value is a list of rules which contributed
        to the result. Empty list means no match. The returned list can be used to inspect which
        data sources contributed to a match. 
        """
        def query(self, data):
            pass
        
    """
    Rule which evaluates if the data is contained in the value which is assumed to be a list
    """
    class InRule(Rule):
        
        def query(self, data):
            datalist = ((data,) if not isinstance(data, list) else data)
            if set(datalist).intersection(set(self.value)):
                return [self]
            else:
                return list()        
    
    """
    Evaluates to true if the data value applied is greater than this rule's value
    """
    class GtRule(Rule):
        # TODO consider making these also work if value is a named source, such as hi_frq_cutoff
        def query(self, data):
            # TODO do some check that data and value is a number here
            if float(data) > float(self.value):
                return [self]
            else:
                return list()

    """
    Evaluates to true if the data value applied is less than this rule's value
    """
    class LtRule(Rule):
        # TODO consider making these also work if value is a named source, such as hi_frq_cutoff
        def query(self, data):
            if float(data) < float(self.value):
                return [self]
            else:
                return list()

    """
    Evaluates to true if the data value applied is in the range (exclusive) indicated by this rule's value.
    The value is a list of 2 elems. 
    """
    class RangeRule(Rule):

        def query(self, data):            
            if data > self.value[0] and data < self.value[1]:
                return [self]
            else:
                return list()
    
    class NotRule(Rule):

        def __init__(self, subrule):
            self.subrule = subrule
            self.value = None
            self.source = None
            self.code = None

        def query(self, data):
            subresult = self.subrule.query(data)
            if subresult: return False
            return self.subrule

    """
    Rules made up from other rules, for example oneRule AND anotherRule
    """
    class CompositeRule(Rule):

        def __init__(self, subrules, code=None, aggregate=False):
            self.subrules = subrules
            self.code = code
            self.aggregate = aggregate
            self.source = None
            
        def query(self, data):
            pass
        
    class AndRule(CompositeRule):
        
        def query(self, data):
            results = [rule.query(data) for rule in self.subrules]
            if all(results):
                # Explode list of lists
                return [rule for resultlist in results for rule in resultlist]
            else:
                return list()
    
    class OrRule(CompositeRule):
        
        def query(self, data):
            results = [rule.query(data) for rule in self.subrules]
            if any(results):
                return [rule for resultlist in results for rule in resultlist]
            else:
                return list()

    """
    Evaluates to true if the passed set of codes contain all of this rule's codes (value)
    """
    class AllRule(Rule):
        
        def query(self, data):
            # Support trailing wildcard, so write this out.            
            for code in set(self.value):
                codefound = False
                for datacode in set(data):
                    if code.endswith("*"):
                        if datacode.startswith(code[:-1]): codefound = True
                    else:
                        if code == datacode: codefound = True
                if not codefound: return []
            return [self]

    """
    Evaluates to true if the passed set of codes contains at least the given number of this rule's codes (value)
    """
    class AtLeastRule(Rule):
        
        def __init__(self, value, code, atleast, aggregate=False):
            self.value = value
            self.code = code
            self.atleast = atleast
            self.aggregate = aggregate
            self.source = None

        def query(self, data):
            # Support trailing wildcard, so write this out.            
            nfound=0
            for code in set(self.value):
                for datacode in set(data):
                    if code.endswith("*"):
                        if datacode.startswith(code[:-1]): nfound += 1
                    else:
                        if code == datacode: nfound += 1
            if nfound >= self.atleast:
                return [self]
            return []

