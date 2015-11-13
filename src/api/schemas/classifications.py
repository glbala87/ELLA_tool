from marshmallow import fields, Schema
from gre.grm import GRM 
from gre.grc import ClassificationResult

class Rule(fields.Field):
    def _serialize(self, value, attr, o):
        if isinstance(o, ClassificationResult) :
            return {"class" : o.clazz, "classification" : o.classification, "message" : o.message, "contributors" : o.contributors}
        elif isinstance(o, GRM.AndRule):
            return {"class" : o.__class__.__name__, "$and" : [r for r in o.subrules]}
        elif isinstance(o, GRM.OrRule):
            return {"class" : o.__class__.__name__, "$or" : [r for r in o.subrules]}
        elif isinstance(o, GRM.NotRule):
            return {"class" : o.__class__.__name__, "$not" : o.subrule}
        elif isinstance(o, GRM.AtLeastRule):
            return {"class" : o.__class__.__name__, "atleast": o.atleast, "value" : o.value, "code" : o.code}
        elif isinstance(o, GRM.Rule):
            return {"class" : o.__class__.__name__, "value" : o.value, "source" : o.source, "code" : o.code}

class ClassificationSchema(Schema):
    class Meta:
        fields = ("class",
                  "classification",
                  "contributors",
                  "message")
        contributors = Rule(many = True)
    
