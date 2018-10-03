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

import pytest
import shlex

from bridgy.inventory import Instance
from bridgy.inventory.newrelic import NewRelicInventory
from bridgy.config import Config

DATA = """
{
    "ECS":{
        "results":[
        {"events":[
            {"containerName":"ardvark?",
            "hostname":"c-04267e627f88362ed-DEV-self-formsvc",
            "entityName":"c-04267e627f88362ed-DEV-self-formsvc",
            "containerId":"dd3456789098765432",
            "hostID":null,
            "agentName":"Infrastructure",
            "timestamp":1501814878000},

            {"containerName":"awesomecontainer",
            "hostname":"ip-672-16-223-200",
            "entityName":"ip-672-16-223-200",
            "containerId":"123456789098765432",
            "hostID":null,
            "agentName":"Infrastructure",
            "timestamp":1501814844000},

            {"containerName":"coolcucumber",
            "hostname":"c-0f9a3f0d9399a6c17-PROD-prfsvclmt",
            "entityName":"c-0f9a3f0d9399a6c17-PROD-prfsvclmt",
            "containerId":"cc3456789098765432",
            "hostID":null,
            "agentName":"Infrastructure",
            "timestamp":1501814820000}
            ]
        }]
    },
    "VM":{
        "results":[
        {"events":[
            {"fullHostname":"i-04267e627f88362ed-DEV-self-formsvc",
            "hostname":"i-04267e627f88362ed-DEV-self-formsvc",
            "entityName":"i-04267e627f88362ed-DEV-self-formsvc",
            "ipV4Address":"172.16.221.211/24",
            "hostID":null,
            "agentName":"Infrastructure",
            "timestamp":1501814878000},

            {"fullHostname":"localhost",
            "hostname":"ip-172-16-223-200",
            "entityName":"ip-172-16-223-200",
            "ipV4Address":"172.16.223.200/24",
            "hostID":null,
            "agentName":"Infrastructure",
            "timestamp":1501814844000},

            {"fullHostname":"localhost",
            "hostname":"i-0f9a3f0d9399a6c17-PROD-prfsvclmt",
            "entityName":"i-0f9a3f0d9399a6c17-PROD-prfsvclmt",
            "ipV4Address":"172.16.225.232/25",
            "hostID":null,
            "agentName":"Infrastructure",
            "timestamp":1501814820000}
            ]
        }],
    "metadata":
        {"eventTypes": ["NetworkSample"],
        "eventType": "NetworkSample",
        "openEnded":true,
        "beginTime":"2017-08-04T01:48:19Z",
        "endTime":"2017-08-04T02:48:19Z",
        "beginTimeMillis":1501811299090,
        "endTimeMillis":1501814899090,
        "rawSince":"60 MINUTES AGO",
        "rawUntil":"`now`",
        "rawCompareWith":"",
        "guid":"333db43-8446-9e66-4688-a89876771322",
        "routerGuid":"3456c3c5-9f58-833a-54a0-4345e90456bf",
        "messages":[],
        "contents":[
                {"function":"events",
                "limit":3,
                "columns":[
                        {"relation":"event","name":"timestamp"},
                        {"relation":"event","name":"entityName"},
                        {"relation":"event","name":"fullHostname"},
                        {"relation":"event","name":"hostname"},
                        {"relation":"event","name":"hostID"},
                        {"relation":"event","name":"ipV4Address"},
                        {"relation":"event","name":"agentName"}
                        ],
                "order":
                    {"column":"timestamp","descending":true}
                }
            ]
        }
    }
}
"""


@mock.patch("%s.open" % builtin_mock, mock.mock_open(read_data=DATA))
def test_newrelic_instances():

    newrelic_obj = NewRelicInventory('account_number','api_key','/tmp/dummy/path')
    instances = newrelic_obj.instances()
    expected_instances = [
        Instance(name=u'coolcucumber', address=None, aliases=None, source='acct:account_number (newrelic)', type='ECS'), 
        Instance(name=u'ip-172-16-223-200', address=u'172.16.223.200', aliases=None, source='acct:account_number (newrelic)', type='VM'), 
        Instance(name=u'i-0f9a3f0d9399a6c17-PROD-prfsvclmt', address=u'172.16.225.232', aliases=None, source='acct:account_number (newrelic)', type='VM'), 
        Instance(name=u'awesomecontainer', address=u'672.16.223.200', aliases=None, source='acct:account_number (newrelic)', type='ECS'), 
        Instance(name=u'ardvark?', address=None, aliases=None, source='acct:account_number (newrelic)', type='ECS'), 
        Instance(name=u'i-04267e627f88362ed-DEV-self-formsvc', address=u'172.16.221.211', aliases=None, source='acct:account_number (newrelic)', type='VM')
    ]
    assert set(instances) == set(expected_instances)
