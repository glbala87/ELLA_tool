from gra import GRA
from grl import GRL

"""
GenAP Rule Engine, GRE

Capable of evaluating a dataset into lists of passed/notpassed ACMG codes using rules specified in for example GRL.
"""


class GRE:

    """
    Main entry point for GRE. Pass rules and data as JSON. Returns passed,notpassed, each of which is a list rule objects.
    """

    def query(self, rules, data):
        return GRA().applyRules(GRL().parseRules(rules), GRA().parseNodeToSourceKeyedDict(data))
