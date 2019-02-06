import json
import hypothesis as ht
import hypothesis.strategies as st
import pytest
import jsonschema


@pytest.fixture(scope="module")
def filterconfig_schema():
    with open("/ella/src/vardb/datamodel/jsonschemas/filterconfig.json") as f:
        s = json.load(f)
    return s


def _filterconfig():
    with open("/ella/src/vardb/testdata/filterconfigs.json") as f:
        fc = json.load(f)
    return fc


@pytest.fixture(scope="module")
def filterconfig():
    return _filterconfig()


@st.composite
def modify_filterconfig(draw):
    """Modified default filter config by taking a quasi-random node in the
    config tree.

    1. If the node is a dict, either
    - Extend the dict (adding a property)
    - Changing a key (property name)

    2. If the node is a list, either
    - Extend the list with dummy data
    - Changing the data at an index in the list

    3. If the node is a number, change the sign of the number

    The assumptions for this test, is that the schema is (and can be) extensively written.

    Assumptions:
    1. Any dict (JSON objects) can not be extended with arbitrary keys
    2. Any list can not contain arbitrary data (e.g. constrained by enum items)
    3. Defined numbers are constrained as either non-negative or non-positive
    """
    fc = json.loads(json.dumps(_filterconfig()))

    def modify(node):
        if isinstance(node, dict):
            if len(node) == 0:
                modification = "extend"
            else:
                modification = draw(st.sampled_from(["modify", "extend"]))
            if modification == "extend":
                node["!!EXTENDED!!"] = "!!EXTENDED!!"
            elif modification == "modify":
                key = draw(st.sampled_from(list(node.keys())))
                v = node.pop(key)
                node["!!MODIFIED!!"] = v
        elif isinstance(node, list):
            if len(node) == 0:
                modification = "extend"
            else:
                modification = draw(st.sampled_from(["modify", "extend"]))
            if modification == "modify":
                key = draw(st.integers(min_value=0, max_value=len(node) - 1))
                node[key] = "!!MODIFIED!!"
            elif modification == "extend":
                node.append("!!EXTENDED!!")
        else:
            raise RuntimeError("Unexpected: Did not modify json")

    # Store path to modified element in tree for debugging purposes
    path = []

    def traverse(node, key):
        # print(node)
        # Append to path
        if key is not None:
            path.append(key)

        # Stop at node if x<0.1
        x = draw(st.floats(min_value=0, max_value=1.0))
        if x < 0.1 and isinstance(node, (dict, list)):
            modify(node)
            return
        else:
            # Traverse further down if possible, otherwise modify node
            if isinstance(node, dict):
                key = draw(st.sampled_from(list(node.keys())))
            elif isinstance(node, list):
                if len(node) == 0:
                    modify(node)
                    return
                key = draw(st.integers(min_value=0, max_value=len(node) - 1))
            if not isinstance(node[key], (list, dict)):
                if isinstance(node[key], (int, float)):
                    # This can no longer be used if we have filters that allow
                    # both positive and negative numbers
                    ht.assume(abs(node[key]) < 1e-8)
                    node[key] = -node[key]
                else:
                    modify(node)
                return
            else:
                modify(node)
                return
            traverse(node[key], key)

    # Traverse to a "random" node in the filterconfig, and modify it
    traverse(fc, None)
    ht.assume(fc != filterconfig)
    return fc, path


def test_passing_jsonschema_filterconfig(filterconfig_schema, filterconfig):
    for fc in filterconfig:
        jsonschema.validate(fc, filterconfig_schema)


@ht.given(st.one_of(modify_filterconfig()))
def test_failing_jsonschema_filterconfig(filterconfig_schema, filterconfig, modified_and_path):
    modified, path = modified_and_path
    try:
        with pytest.raises(jsonschema.ValidationError):
            for fc in modified:
                jsonschema.validate(fc, filterconfig_schema)
    except:
        # Print path in tree, and modified element
        print(path)

        def traverse(node, path):
            if not path:
                print(node)
            else:
                traverse(node[path.pop(0)], path)

        traverse(modified, path)
        raise
