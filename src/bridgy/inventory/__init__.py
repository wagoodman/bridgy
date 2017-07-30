import os

from source import Instance
from aws import AwsInventory
# from gcp import GcpInventory
from flatfile import CsvInventory

SOURCES = {
    'aws': AwsInventory,
    # 'gcp': GcpInventory,
    'csv': CsvInventory,
}


def inventory(config):

    source = config['inventory']['source']
    srcCfg = config[source]
    if source == 'aws':
        return AwsInventory(aws_access_key_id=srcCfg['access_key_id'],
                            aws_secret_access_key=srcCfg['secret_access_key'],
                            aws_session_token=srcCfg['session_token'],
                            region_name=srcCfg['region'])
    if source == 'csv':
        csvPath = os.path.join(config.inventoryDir(source), srcCfg['name'])
        # TODO: make delimiter optional if missing from config
        return CsvInventory(path=csvPath,
                            fields=srcCfg['fields'],
                            delimiter=srcCfg['delimiter'] )

def instances(config):
    return inventory(config).instances()

def search(config, targets):
    return inventory(config).search(targets)

def update(config):
    inventory(config).update()
