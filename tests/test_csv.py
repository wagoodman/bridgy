try:
    import builtins
    builtin_mock = 'builtins'
except ImportError:
    import __builtin__
    builtin_mock = '__builtin__'

try:
    import unittest.mock as mock
except ImportError:
    import mock

import csv
import pytest
import shlex

from bridgy.inventory import Instance
from bridgy.inventory.flatfile import CsvInventory
from bridgy.config import Config

DATA = """\
testenv-pubsrv|1.2.3.4|somethingrandom0
testenv-pubsrv|5.6.7.8|somethingrandom1
devenv-pubsrv|9.10.11.12|somethingrandom2
devenv-pubsrv|13.14.15.16|somethingrandom3
testenv-formsvc|17.18.19.20|somethingrandom4"""


@mock.patch("%s.open" % builtin_mock, mock.mock_open(read_data=DATA))
@mock.patch("csv.DictReader")
def test_newrelic_instances(mock_csv_reader):
    # for whatever reason mock_open is not sufficent since the DictReader will return nothing
    # so mocking the csv reader is necessary
    ret = []
    for line in DATA.split("\n"):
        ret.append(dict(zip(['name','address','random'], line.split("|"))))
    mock_csv_reader.return_value = ret

    csv_obj = CsvInventory('/tmp/dummy/path', ' name,address, random ', ' | ')
    instances = csv_obj.instances()

    expected_instances = [Instance(name='devenv-pubsrv', address='13.14.15.16'),
                          Instance(name='testenv-pubsrv', address='1.2.3.4'),
                          Instance(name='devenv-pubsrv', address='9.10.11.12'),
                          Instance(name='testenv-pubsrv', address='5.6.7.8'),
                          Instance(name='testenv-formsvc', address='17.18.19.20')]
    assert set(instances) == set(expected_instances)
