import os
import re
import sys
import logging
from functools import partial

from bridgy.utils import memoize
from bridgy.inventory.source import Instance, InventorySet
from bridgy.inventory.aws import AwsInventory
from bridgy.inventory.flatfile import CsvInventory
from bridgy.inventory.newrelic import NewRelicInventory
# from gcp import GcpInventory

logger = logging.getLogger()

SOURCES = {
    'aws': AwsInventory,
    # 'gcp': GcpInventory,
    'csv': CsvInventory,
    'newrelic': NewRelicInventory,
}


@memoize
def inventory(config):
    inventorySet = InventorySet()

    for source, srcCfg in config.sources():
        if source == 'aws':
            # the cache directory for the original v1 config did not separate 
            # out multiple aws profiles into subdirectories
            if config.version == 1:
                cache_dir = config.inventoryDir(AwsInventory.name)
            else:
                cache_dir = config.inventoryDir(AwsInventory.name, srcCfg['name'])
            
            if not os.path.exists(cache_dir):
                os.mkdir(cache_dir)

            from botocore.exceptions import ProfileNotFound
            try:
                inv = AwsInventory(cache_dir, **srcCfg)
                inventorySet.add(inv)
            except ProfileNotFound:
                logger.error("Unconfigured AWS profile configured.")
                sys.exit(1)

        elif source == 'csv':
            inv = CsvInventory(path=config.inventoryDir(source, srcCfg['file']), **srcCfg)
            inventorySet.add(inv)

        elif source == 'newrelic':

            proxies = {}

            if config.dig('inventory', 'http_proxy'):
                proxies['http'] = config.dig('inventory', 'http_proxy')
            elif 'HTTP_PROXY' in os.environ:
                proxies['http'] = os.environ['HTTP_PROXY']
            elif 'http_proxy' in os.environ:
                proxies['http'] = os.environ['http_proxy']

            if config.dig('inventory', 'https_proxy'):
                proxies['https'] = config.dig('inventory', 'https_proxy')
            elif 'HTTPS_PROXY' in os.environ:
                proxies['https'] = os.environ['HTTPS_PROXY']
            elif 'https_proxy' in os.environ:
                proxies['https'] = os.environ['https_proxy']

            inv = NewRelicInventory(data_path=config.inventoryDir(NewRelicInventory.name),
                                    proxies=proxies,
                                    **srcCfg)
 
            inventorySet.add(inv)
        
    return inventorySet

def instance_filter(instance, include_re=None, exclude_re=None):
    comparables = [instance.name, instance.address]

    if instance.aliases:
        comparables.extend(list(instance.aliases))

    if include_re:
        for name in comparables:
            if include_re.search(name):
                return True
        return False
    elif exclude_re:
        for name in comparables:
            if exclude_re.search(name):
                return False
        return True
    else:
        return True

@memoize
def instances(config):
    include_re, exclude_re = None, None
    if config.dig('inventory', 'include_pattern'):
        include_re = re.compile(config.dig('inventory', 'include_pattern'))
    if config.dig('inventory', 'exclude_pattern'):
        exclude_re = re.compile(config.dig('inventory', 'exclude_pattern'))

    all_instances = inventory(config).instances()
    config_instance_filter = partial(instance_filter, include_re=include_re, exclude_re=exclude_re)
    return list(filter(config_instance_filter, all_instances))

def search(config, targets):
    fuzzy = False
    if config.dig('inventory', 'fuzzy_search'):
        fuzzy = config.dig('inventory', 'fuzzy_search')

    include_re, exclude_re = None, None
    if config.dig('inventory', 'include_pattern'):
        include_re = re.compile(config.dig('inventory', 'include_pattern'))
    if config.dig('inventory', 'exclude_pattern'):
        exclude_re = re.compile(config.dig('inventory', 'exclude_pattern'))

    matched_instances = inventory(config).search(targets, fuzzy=fuzzy)
    config_instance_filter = partial(instance_filter, include_re=include_re, exclude_re=exclude_re)
    return list(filter(config_instance_filter, matched_instances))

def update(config):
    inventory(config).update()
