import os
import mock
import pytest
import shlex

from bridgy.inventory import Instance
from bridgy.inventory.aws import AwsInventory


def test_aws_instances(mocker):
    test_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(test_dir, 'aws_stubs')

    aws_obj = AwsInventory(cache_dir=cache_dir, access_key_id='access_key_id',
                           secret_access_key='secret_access_key', session_token='session_token',
                           region='region')
    instances = aws_obj.instances()

    expected_instances = [Instance(name='test-forms', address='devbox', aliases=('devbox', 'ip-172-31-8-185.us-west-2.compute.internal', 'i-e54cbaeb'), source='aws', container_id=None, type='VM'),
                          Instance(name='devlab-forms', address='devbox', aliases=('devbox', 'ip-172-31-0-138.us-west-2.compute.internal', 'i-f7d726f9'), source='aws', container_id=None, type='VM'),
                          Instance(name='test-account-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-139.us-west-2.compute.internal', 'i-f4d726fa'), source='aws', container_id=None, type='VM'),
                          Instance(name='devlab-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-0-142.us-west-2.compute.internal', 'i-f5d726fb'), source='aws', container_id=None, type='VM'),
                          Instance(name='devlab-game-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-140.us-west-2.compute.internal', 'i-f2d726fc'), source='aws', container_id=None, type='VM'),
                          Instance(name='test-game-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-141.us-west-2.compute.internal', 'i-f3d726fd'), source='aws', container_id=None, type='VM'),
                          Instance(name='test-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-2-38.us-west-2.compute.internal', 'i-0f500447384e95942'), source='aws', container_id=None, type='VM'),
                          Instance(name='test-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-2-39.us-west-2.compute.internal', 'i-0f500447384e95943'), source='aws', container_id=None, type='VM')]

    assert set(instances) == set(expected_instances)

def test_aws_instances_profile(mocker):
    test_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(test_dir, 'aws_stubs')
    config_dir = os.path.join(test_dir, 'aws_configs')

    aws_obj = AwsInventory(cache_dir=cache_dir, profile='somewhere', region='region', config_path=config_dir)
    instances = aws_obj.instances()

    expected_instances = [Instance(name='test-forms', address='devbox', aliases=('devbox', 'ip-172-31-8-185.us-west-2.compute.internal', 'i-e54cbaeb'), source='aws', container_id=None, type='VM'),
                          Instance(name='devlab-forms', address='devbox', aliases=('devbox', 'ip-172-31-0-138.us-west-2.compute.internal', 'i-f7d726f9'), source='aws', container_id=None, type='VM'),
                          Instance(name='test-account-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-139.us-west-2.compute.internal', 'i-f4d726fa'), source='aws', container_id=None, type='VM'),
                          Instance(name='devlab-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-0-142.us-west-2.compute.internal', 'i-f5d726fb'), source='aws', container_id=None, type='VM'),
                          Instance(name='devlab-game-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-140.us-west-2.compute.internal', 'i-f2d726fc'), source='aws', container_id=None, type='VM'),
                          Instance(name='test-game-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-141.us-west-2.compute.internal', 'i-f3d726fd'), source='aws', container_id=None, type='VM'),
                          Instance(name='test-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-2-38.us-west-2.compute.internal', 'i-0f500447384e95942'), source='aws', container_id=None, type='VM'),
                          Instance(name='test-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-2-39.us-west-2.compute.internal', 'i-0f500447384e95943'), source='aws', container_id=None, type='VM')]

    assert set(instances) == set(expected_instances)

    from botocore.exceptions import ProfileNotFound
    with pytest.raises(ProfileNotFound):
        aws_obj = AwsInventory(cache_dir=cache_dir, profile='some-unconfigured-profile', region='region', config_path=config_dir)