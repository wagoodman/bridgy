from __future__ import absolute_import
import os

from inventory.source import Instance
from inventory.aws import AwsInventory
# from gcp import GcpInventory
from inventory.flatfile import CsvInventory
from inventory.newrelic import NewRelicInventory

SOURCES = {
    'aws': AwsInventory,
    # 'gcp': GcpInventory,
    'csv': CsvInventory,
    'newrelic': NewRelicInventory,
}

def inventory(config):
    source = config.dig('inventory', 'source')
    srcCfg = config[source]

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

    if source == 'aws':
        return AwsInventory(aws_access_key_id=srcCfg['access_key_id'],
                            aws_secret_access_key=srcCfg['secret_access_key'],
                            aws_session_token=srcCfg['session_token'],
                            region_name=srcCfg['region'],
                            data_path=config.inventoryDir(AwsInventory.name))
    if source == 'csv':
        csvPath = os.path.join(config.inventoryDir(source), srcCfg['name'])
        # TODO: make delimiter optional if missing from config
        return CsvInventory(path=csvPath,
                            fields=srcCfg['fields'],
                            delimiter=srcCfg['delimiter'] )

    if source == 'newrelic':
        return NewRelicInventory(account_number=srcCfg['account_number'],
                                 insights_query_api_key=srcCfg['insights_query_api_key'],
                                 data_path=config.inventoryDir(NewRelicInventory.name),
                                 proxies=proxies)

def instances(config):
    return inventory(config).instances()

def search(config, targets):
    return inventory(config).search(targets)

def update(config):
    inventory(config).update()
