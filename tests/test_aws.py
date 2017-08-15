import os
import mock
import pytest
import shlex

from bridgy.inventory import Instance
from bridgy.inventory.aws import AwsInventory
from bridgy.config import Config


def test_aws_instances(mocker):
    test_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(test_dir, 'aws_stubs')

    aws_obj = AwsInventory(cache_dir, 'access_key_id', 'secret_access_key', 'session_token', 'region')
    instances = aws_obj.instances()

    expected_instances = [Instance(name=u'test-forms', address=u'devbox'),
                          Instance(name=u'devlab-forms', address=u'devbox'),
                          Instance(name=u'test-account-svc', address=u'devbox'),
                          Instance(name=u'devlab-pubsrv', address=u'devbox'),
                          Instance(name=u'devlab-game-svc', address=u'devbox'),
                          Instance(name=u'test-game-svc', address=u'devbox'),
                          Instance(name=u'test-pubsrv', address=u'devbox'),
                          Instance(name=u'test-pubsrv', address=u'devbox')]

    assert set(instances) == set(expected_instances)
