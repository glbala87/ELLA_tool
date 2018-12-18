from marshmallow import Schema, pre_dump, post_dump
from rule_engine.grm import GRM


class RuleSchema(Schema):
    class Meta:
        fields = ["code", "source", "value", "match", "op"]

    @pre_dump(pass_many=False)
    def add_operator(self, obj):
        mapping = [
            [GRM.InRule, "$in"],
            [GRM.AllRule, "$all"],
            [GRM.AtLeastRule, "$at_least"],
            [GRM.GtRule, "$gt"],
            [GRM.LtRule, "$lt"],
            [GRM.RangeRule, "$range"],
            [GRM.NotRule, "$not"],
        ]
        for m in mapping:
            if isinstance(obj, m[0]):
                obj.op = m[1]
                break

        return obj


class ClassificationSchema(Schema):
    class Meta:
        fields = ["clazz", "classification", "message", "contributors", "meta"]

    @post_dump()
    def rename_class(self, data):
        data["class"] = data["clazz"]
        del data["clazz"]
        return data
