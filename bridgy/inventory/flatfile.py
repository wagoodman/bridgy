from inventory.source import InventorySource, Instance
from config import Config

import os
import csv


class CsvInventory(InventorySource):

    @property
    def name(self): return 'csv'

    def __init__(self):
        self.csvPath = os.path.join(Config.inventoryDir(self.name),
                                    Config['csv']['name'])

    def update(self): pass

    def instances(self, stub=True):
        instances = set()
        with open(self.csvPath, 'rb') as csvfile:
            fields = [f.strip() for f in Config['csv']['fields'].split(",")]
            reader = csv.DictReader(
                csvfile, fieldnames=fields, delimiter=Config['csv']['delimiter'].strip() or ',')
            for row in reader:
                instances.add(Instance(row['name'].strip(), row['address'].strip()))

        return list(instances)
