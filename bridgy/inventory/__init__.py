from config import Config
from inventory.aws import AwsInventory
# from inventory.gcp import GcpInventory
from inventory.flatfile import CsvInventory

# TODO: register meta classes

SOURCES = {
    'aws': AwsInventory,
    # 'gcp': GcpInventory,
    'csv': CsvInventory,
}

def getInventory():
    source = Config['inventory']['source']
    return SOURCES[source]()
