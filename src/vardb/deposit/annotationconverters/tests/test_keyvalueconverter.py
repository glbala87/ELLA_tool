import pytest
from vardb.deposit.annotationconverters.keyvalueconverter import KeyValueConverter


def test_keyvalueconverter_identity():
    element_config = {}
    converter = KeyValueConverter(None, element_config)
    for value in [1, "1", None, True]:
        processed = converter(value)
        assert processed == value, str(value)


def test_keyvalueconverter_int():
    element_config = {"target_type": "int"}
    converter = KeyValueConverter(None, element_config)
    for value, expected in [(1, 1), ("1", 1), (True, 1), (False, 0)]:
        processed = converter(value)
        assert processed == expected, str(value)
    # Test invalid data
    for value in ["1.0", None, "dabla"]:
        with pytest.raises(ValueError):
            converter(value)


def test_keyvalueconverter_float():
    element_config = {"target_type": "float"}
    converter = KeyValueConverter(None, element_config)
    for value, expected in [(1, 1.0), ("1", 1.0), ("1.0", 1.0), (True, 1.0)]:
        processed = converter(value)
        assert processed == expected, str(value)

    for value in [None, "dabla"]:
        with pytest.raises(ValueError):
            converter(value)


def test_keyvalueconverter_bool():
    element_config = {"target_type": "bool"}
    converter = KeyValueConverter(None, element_config)
    # Test true values
    for value in [True, 1, 2, 0.1, "1", "True", "true", "t", "y", "T", "Y", "yes", "on", [0]]:
        processed = converter(value)
        assert processed is True, str(value)
    # Test false value
    for value in [False, None, 0, 0.0, "0", "False", "false", "f", "F", "N", "n", "no", "off", []]:
        processed = converter(value)
        assert processed is False, str(value)
    # Test invalid data
    for value in ["dabla"]:
        with pytest.raises(ValueError):
            converter(value)


def test_keyvalueconverter_string():
    element_config = {"target_type": "string"}
    converter = KeyValueConverter(None, element_config)
    for value in [1, "1"]:
        processed = converter(value)
        assert processed == str(value), str(value)


def test_keyvalueconverter_split():
    element_config = {"split": "|"}
    converter = KeyValueConverter(None, element_config)
    processed = converter("1|2|3")
    assert processed == ["1", "2", "3"]

    element_config = {"target_type": "int", "split": "|"}
    converter = KeyValueConverter(None, element_config)
    processed = converter("1|2|3")
    assert processed == [1, 2, 3]

    with pytest.raises(ValueError):
        processed = converter("1|2|dabla")

    element_config = {"target_type": "int", "target_type_throw": False, "split": "|"}
    converter = KeyValueConverter(None, element_config)
    processed = converter("1|2|dabla")
    assert processed is None
