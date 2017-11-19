import os
import mock
import pytest
import shlex

import bridgy.inventory
from bridgy.inventory import InventorySet, Instance
from bridgy.inventory.aws import AwsInventory
from bridgy.config import Config

def get_aws_inventory():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(test_dir, 'aws_stubs')

    aws_obj = AwsInventory(cache_dir=cache_dir, access_key_id='access_key_id',
                           secret_access_key='secret_access_key', session_token='session_token',
                           region='region')
    
    return aws_obj

def test_inventory_set(mocker):
    test_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(test_dir, 'aws_stubs')

    aws_obj = get_aws_inventory()

    inventorySet = InventorySet()
    inventorySet.add(aws_obj)
    inventorySet.add(aws_obj)
    print(aws_obj.instances())

    all_instances = inventorySet.instances()

    aws_instances = [Instance(name='test-forms', address='devbox', aliases=('devbox', 'ip-172-31-8-185.us-west-2.compute.internal', 'i-e54cbaeb'), source='aws'), 
                     Instance(name='devlab-forms', address='devbox', aliases=('devbox', 'ip-172-31-0-138.us-west-2.compute.internal', 'i-f7d726f9'), source='aws'), 
                     Instance(name='test-account-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-139.us-west-2.compute.internal', 'i-f4d726fa'), source='aws'), 
                     Instance(name='devlab-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-0-142.us-west-2.compute.internal', 'i-f5d726fb'), source='aws'), 
                     Instance(name='devlab-game-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-140.us-west-2.compute.internal', 'i-f2d726fc'), source='aws'), 
                     Instance(name='test-game-svc', address='devbox', aliases=('devbox', 'ip-172-31-0-141.us-west-2.compute.internal', 'i-f3d726fd'), source='aws'), 
                     Instance(name='test-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-2-38.us-west-2.compute.internal', 'i-0f500447384e95942'), source='aws'), 
                     Instance(name='test-pubsrv', address='devbox', aliases=('devbox', 'ip-172-31-2-39.us-west-2.compute.internal', 'i-0f500447384e95943'), source='aws')]

    expected_instances = aws_instances + aws_instances

    assert len(all_instances) == len(expected_instances)
    assert set(all_instances) == set(expected_instances)

