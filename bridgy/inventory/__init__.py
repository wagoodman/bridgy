import os

from bridgy.utils import memoize
from bridgy.inventory.source import Instance
from bridgy.inventory.aws import AwsInventory
from bridgy.inventory.flatfile import CsvInventory
from bridgy.inventory.newrelic import NewRelicInventory
# from gcp import GcpInventory

SOURCES = {
    'aws': AwsInventory,
    # 'gcp': GcpInventory,
    'csv': CsvInventory,
    'newrelic': NewRelicInventory,
}

@memoize
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
        if os.path.exists(os.path.expanduser("~/.aws")):
            return AwsInventory(cache_dir=config.inventoryDir(AwsInventory.name))

        return AwsInventory(cache_dir=config.inventoryDir(AwsInventory.name),
                            access_key_id=srcCfg['access_key_id'],
                            secret_access_key=srcCfg['secret_access_key'],
                            session_token=srcCfg['session_token'],
                            region=srcCfg['region'])
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

@memoize
def instances(config):
    return inventory(config).instances()

def search(config, targets):
    fuzzy = False
    if config.dig('inventory', 'fuzzy_search'):
        fuzzy = config.dig('inventory', 'fuzzy_search')

    return inventory(config).search(targets, fuzzy=fuzzy)

def update(config):
    inventory(config).update()
