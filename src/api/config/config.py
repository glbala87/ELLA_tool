# -*- coding: utf-8 -*-

import os
import json
import jsonschema
import copy
import yaml

from .acmgconfig import acmgconfig
from .customannotationconfig import customannotationconfig

ELLA_ROOT = os.path.abspath(os.path.join(os.path.split(os.path.abspath(__file__))[0], "../../.."))


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def file_constructor(loader, node):
    resolved = os.path.join(ELLA_ROOT, node.value)
    assert os.path.isfile(
        resolved
    ), "File specified in config {} (interpreted as {}) does not exists".format(
        node.value, resolved
    )
    return resolved


def environment_constructor(loader, node):
    "Load !env and !env_<subtag> tags"
    if isinstance(node.value, str):
        # Default to "null", which will be resolved by yaml to None
        value = os.environ.get(node.value, "null")
    elif isinstance(node.value, list):
        assert (
            len(node.value) == 2
        ), "List {} is not of length 2: [ENVIRONMENT_VARIABLE, default]".format(node.value)
        value = os.environ.get(node.value[0].value, node.value[1].value)
    # Extract tag to construct value
    if "_" in node.tag:
        # Explicit
        # Resolve tag from e.g. "str" -> "tag:yaml.org,2002:str"
        unresolved_tag = node.tag.split("_")[1]
        if loader.DEFAULT_TAGS["!!"] + unresolved_tag in loader.yaml_constructors:
            # Tag is standard (bool, str, int etc)
            tag = loader.DEFAULT_TAGS["!!"] + unresolved_tag
        else:
            tag = loader.DEFAULT_TAGS["!"] + unresolved_tag
    else:
        # Resolve tag implicitly by value
        tag = loader.resolve(yaml.nodes.ScalarNode, value, [True, False])

    # Create new node
    new_node = yaml.nodes.ScalarNode(tag, value)

    # Run constructor on new node
    return loader.yaml_constructors[tag](loader, new_node)


class ConfigLoader(yaml.SafeLoader):
    pass


# Add custom YAML constructors
ConfigLoader.add_constructor("!file", file_constructor)
ConfigLoader.add_constructor("!env", environment_constructor)
# Add YAML constructors for !env_bool, !env_str, !env_file etc
default_tags = [
    tag.split(":")[-1].lstrip("!") for tag in ConfigLoader.yaml_constructors if tag is not None
]
for tag in default_tags:
    if tag == "str":
        continue
    ConfigLoader.add_constructor("!env_{}".format(tag), environment_constructor)

if "ELLA_CONFIG" in os.environ:
    with open(os.environ["ELLA_CONFIG"]) as ella_config_file:
        config = yaml.load(ella_config_file, Loader=ConfigLoader)
    schema_path = os.path.join(os.path.split(os.path.abspath(__file__))[0], "config.schema.json")
    with open(schema_path, "r") as schema_file:
        schema = json.load(schema_file)
    jsonschema.validate(config, schema)
else:
    assert not str2bool(
        os.environ["PRODUCTION"]
    ), "No config specified. This is only possible when not running in PRODUCTION mode: $PRODUCTION={}".format(
        os.environ["PRODUCTION"]
    )
    config = {}

config.setdefault("transcripts", {})["consequences"] = [
    "transcript_ablation",
    "splice_donor_variant",
    "splice_acceptor_variant",
    "stop_gained",
    "frameshift_variant",
    "start_lost",
    "initiator_codon_variant",
    "stop_lost",
    "inframe_insertion",
    "inframe_deletion",
    "missense_variant",
    "protein_altering_variant",
    "transcript_amplification",
    "splice_region_variant",
    "incomplete_terminal_codon_variant",
    "synonymous_variant",
    "stop_retained_variant",
    "coding_sequence_variant",
    "mature_miRNA_variant",
    "5_prime_UTR_variant",
    "3_prime_UTR_variant",
    "non_coding_transcript_exon_variant",
    "non_coding_transcript_variant",
    "intron_variant",
    "NMD_transcript_variant",
    "upstream_gene_variant",
    "downstream_gene_variant",
    "TFBS_ablation",
    "TFBS_amplification",
    "TF_binding_site_variant",
    "regulatory_region_variant",
    "regulatory_region_ablation",
    "regulatory_region_amplification",
    "feature_elongation",
    "feature_truncation",
    "intergenic_variant",
]

config["annotation"] = {
    "clinvar": {
        "clinical_significance_status": {
            "criteria provided, conflicting interpretations": 1,
            "criteria provided, multiple submitters, no conflicts": 2,
            "criteria provided, single submitter": 1,
            "no assertion criteria provided": 0,
            "no assertion provided": 0,
            "practice guideline": 4,
            "reviewed by expert panel": 3,
        }
    }
}


config["acmg"] = acmgconfig
config["custom_annotation"] = customannotationconfig


def get_user_config(app_config, usergroup_config, user_config):
    # Use json instead of copy.deepcopy for performance
    merged_config = copy.deepcopy(app_config.get("user", {}).get("user_config", {}))
    merged_config.update(copy.deepcopy(usergroup_config))
    merged_config.update(copy.deepcopy(user_config))
    return merged_config
