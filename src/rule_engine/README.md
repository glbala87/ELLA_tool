# genAP Rule Engine

The genAP rule engine lets you configure and query a nested rule set for classification of gene variant data using different sources of classification rules. 

The engine consists of 3 parts:

1. The rule model, GRE
2. The JSON rule config parser, GRL
3. The JSON data parser and applier, GRA

## Rule model, GRE

A rule model consists of a number of objects of any subclass of `Rule`.

Any `Rule` has the following capabilities:

1. It may have a value. This is for example the number `0.01` for a `GtRule`, or `["lost_splice_site", "new_cryptic_splice_site"]` for an `InRule`.
2. It may have a source. If it has, that should be used to look up data to query the rule with.
3. It may have a code. This is used to classify the rule itself, both when returning an output report and when nesting rules together. It is not an id, multiple rules may
produce the code `PP2` for example.
4. It may be an aggregate rule. If it is, it is intended to process the list of codes of previously passed rules. This is the key to nesting rules from multiple sources. 
5. It may have a list of subrules. Then it is a `CompositeRule`, such as `AndRule` or `OrRule`. In this case, it will query its subrules when itself is queried.
6. It may be queried by calling `query()`. This returns either empty list as `False` or the list of rules which passed as `True`.

## Rule parser, GRL

This module parses a JSON rule specification into a code-keyed ordered dictionary of lists of rule objects. The specification defines an *ordering* of rule querying. It is important to know that order of rules matters in the JSON file.

The supported syntax is as given below.
(*Note:* Source names and data values are invented for the purpose of example.)

### Value equality

You can specify a requirement for value equality as follows:

```
{
  "code": "PP5",
  "rule": {"genepanel.hi_freq_cutoff": 0.001}
}
```

*Note:* This is internally translated to an in rule with a single value.

### In rule

Use the in rule like the following example:

```
{
  "code": "BP1",
  "rule": {"transcript.Consequence": {"$in": ["missense_variant", "synonymous_variant"]}}        
}
```

If the data passed in (the data for `transcript.Consequence` in the example) is a list, the rule will perform a set intersection and return true if that has elements. 

### Gt rule

The Gt rule performs a greater than operation:

```
{
  "code": "rBP7-5",
  "rule": {"my.value": {"$gt": 0.5}}
}
```

This evaluates to true if the data value passed is greater than 0.5. 

### Lt rule

The Lt rule performs a less than operation:

```
{
  "code": "rBP7-5",
  "rule": {"my.value": {"$lt": 0.5}}
}
```

### Range rule

The range rule checks if the passed value lies within a given numeric range (exclusive):

```
{
  "code": "rBP7-6",
  "rule": {"my.value": {"$range": [0, 1.6]}}
}
```

### And rule

The and rule allows you to perform a logical and between two rules:

```
{
  "code": "PP5",
  "rule": {"$and": [
                    {"genepanel.hi_freq_cutoff": 0.001},
                    {"transcript.Consequence": {"$in": ["missense_variant", "synonymous_variant"]}}   
                   ]}
}
```

### Or rule

The or rule performs logical or:

```
{
  "code": "PP2",
  "rule": {"$or": [
                    {"genepanel.hi_freq_cutoff": 0.001},
                    {"transcript.Consequence": {"$in": ["missense_variant", "synonymous_variant"]}}   
                   ]}
}
```

### Not rule

The not rule performs logical negation:

```
{
  "code": "PP1",
  "rule": {"transcript.Consequence": {"$not": {"$in": ["missense_variant", "synonymous_variant"]}}}
}
```

### Aggregation

The `$$aggregate` keyword indicates that a rule will process the set of codes of hitherto passed rules, not source data. Hence, aggregate rules have no source. 

### All rule

The all rule is true if all of the given values are in the input data. This is used in aggregation to require a number of codes to have been passed, in the following way:

```
{
  "code": "PP7",
  "rule": {"$$aggregate": {"$all": ["rBP7-3", "rBP7-4"]}}
}
```

Here, PP7 is included as passed if the two other codes were passed. 

### Atleast rule

The atleast rule allows you to specify that n out of a set of m rule codes must have passed:

```
{
  "code": "PP7",
  "rule": {"$$aggregate": {"$atleast": [2, "rBP7-3", "rBP7-4", "rBP7-5"]}}
}
```

In the example above, the constraint is that at least 2 of the 3 given codes must have passed.

### Nesting rules

You may nest arbitrary complex rules with the syntax described above. Here is an example of a more complex rule:

```
{
  "code": "PP2",
  "rule": {"$$aggregate": {"$and":
                                  [
                                    "REQ_missense",
                                    {"$in": ["REQ_GP_lof_missense", 
                                             "REQ_GP_missense_only"]},
                                    {"$not": {"$in": ["PS1", "PM5"]}}
                                  ]
                           }
           }
}
```

Informally, this example translates to: Set the code PP2 if the code `REQ_missense` is set, one or more of the codes `REQ_GP_lof_missense` and `REQ_GP_missense_only` are set; but neither `PS1` nor `PM5`.

## Rule applier, GRA

This module parses the data input and applies to the rule model. It then produces an output where grouped sources are presented with the rules they contributed to, if any. Also present in the output is the list of codes of rules which queried to `True`.

## Final ACMG classification

The GRE does not currently have JSON config syntax to represent the rules for ACMG final classification. This has to happen outside the GRE, based on known semantics of the codes in the `passed` list returned from GRE. 

