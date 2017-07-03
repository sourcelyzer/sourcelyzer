import pytest
import os

from sourcelyzer.properties import load_from_str, load_from_file

def test_string_parser():

    conf = """;comment
key1=value1
key2=value=2
"""

    props = load_from_str(conf)

    assert props['key1'] == "value1"
    assert props['key2'] == "value=2"

def test_immutability():
    conf = "key1=value1\nkey2=value2"
    props = load_from_str(conf)

    with pytest.raises(RuntimeError):
        props['key2'] = 'value3'    

def test_check_for_item():
    conf = "key1=value1\nkey2=value2"
    props = load_from_str(conf)

    good = True if 'key2' in props else False
    bad  = True if 'key3' not in props else False

    assert good == True
    assert bad == True

def test_load_file():
    fn = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.ini')
    print('test ini: %s' % fn)

    props = load_from_file(fn)

    assert props['key1'] == 'value1'
    assert props['key2'] == 'value=2'

def test_hash():
    fn = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.ini')
    props = load_from_file(fn)

    print(hash(props))

