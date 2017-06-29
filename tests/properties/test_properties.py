import pytest

from sourcelyzer.properties import load_from_str

def test_string_parser():

    conf = """;comment
key1=value1
key2=value=2
"""

    props = load_from_str(conf)

    assert props['key1'] == "value1"
    assert props['key2'] == "value=2"

