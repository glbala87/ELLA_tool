# -*- coding: utf-8 -*-

import os
import re
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
    ConfigLoader.add_constructor("!env_{}".format(tag), environment_constructor)

if "ELLA_CONFIG" in os.environ:
    with open(os.environ["ELLA_CONFIG"]) as ella_config_file:
        config = yaml.load(ella_config_file, Loader=ConfigLoader)
else:
    assert not str2bool(
        os.environ["PRODUCTION"]
    ), "No config specified. This is only possible when not running in PRODUCTION mode: $PRODUCTION={}".format(
        os.environ["PRODUCTION"]
    )
    config = {}

config["acmg"] = acmgconfig
config["custom_annotation"] = customannotationconfig


def get_user_config(app_config, usergroup_config, user_config):
    # Use json instead of copy.deepcopy for performance
    merged_config = copy.deepcopy(app_config["user"]["user_config"])
    merged_config.update(copy.deepcopy(usergroup_config))
    merged_config.update(copy.deepcopy(user_config))
    return merged_config


def get_filter_config(app_config, filter_config):
    """
    filter_config is shallow merged with the default
    provided in application config.
    """

    merged_filters = list()
    assert "filters" in filter_config
    for filter_step in filter_config["filters"]:

        base_config = dict(app_config["filter"]["default_filter_config"][filter_step["name"]])
        base_config.update(filter_step.get("config", {}))

        filter_exceptions = []
        for filter_exception in filter_step.get("exceptions", []):
            filter_exceptions.append(
                {"name": filter_exception["name"], "config": filter_exception.get("config", {})}
            )

        merged_filters.append(
            {"name": filter_step["name"], "config": base_config, "exceptions": filter_exceptions}
        )
    merged_filters = copy.deepcopy(merged_filters)
    return merged_filters
