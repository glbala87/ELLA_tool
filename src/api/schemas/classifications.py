from marshmallow import fields, Schema
from gre.grm import GRM 
from gre.grc import ClassificationResult

# From https://github.com/marshmallow-code/marshmallow/issues/120#issuecomment-81382070 , the built in Dict doesn't work. 
class DictField(fields.Field):

    def __init__(self, key_field, nested_field, *args, **kwargs):
        fields.Field.__init__(self, *args, **kwargs)
        self.key_field = key_field
        self.nested_field = nested_field

    def _deserialize(self, value):
        ret = {}
        for key, val in value.items():
            k = self.key_field.deserialize(key)
            v = self.nested_field.deserialize(val)
            ret[k] = v
        return ret

    def _serialize(self, value, attr, obj):
        ret = {}
        for key, val in value.items():
            k = self.key_field._serialize(key, attr, obj)
            v = self.nested_field.serialize(key, self.get_value(attr, obj))
            ret[k] = v
        return ret

class Rule(fields.Field):
    def _serialize(self, value, attr, o):
        if isinstance(value, list):
            return [self._serialize(e, attr, o) for e in value]
        if isinstance(value, ClassificationResult) :
            return {"class" : value.clazz, "classification" : value.classification, "message" : value.message, "contributors" : value.contributors}
        elif isinstance(value, GRM.AndRule):
            return {"class" : value.__class__.__name__, "$and" : self._serialize(value.subrules, attr, o) }
        elif isinstance(value, GRM.OrRule):
            return {"class" : value.__class__.__name__, "$or" : self._serialize(value.subrules, attr, o) }
        elif isinstance(value, GRM.NotRule):
            return {"class" : value.__class__.__name__, "$not" : self._serialize(value.subrule, attr,o)}
        elif isinstance(value, GRM.AtLeastRule):
            return {"class" : value.__class__.__name__, "atleast": value.atleast, "value" : value.value, "code" : value.code}
        elif isinstance(value, GRM.Rule):
            return {"class" : value.__class__.__name__, "value" : value.value, "source" : value.source, "code" : value.code}
        else:
            raise RuntimeError("Can't serialize: " + value)

class ClassificationSchema(Schema):
    class Meta:
        fields = ["alleles"]
    alleles = DictField(fields.Int(), Rule())
    
