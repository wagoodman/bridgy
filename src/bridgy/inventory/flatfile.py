from inventory.source import InventorySource, Instance

import os
import csv

class CsvInventory(InventorySource):

    @property
    def name(self): return 'csv'

    def __init__(self, path, fields, delimiter=','):
        self.csvPath = path
        self.fields = [f.strip() for f in fields.split(",")]
        self.delimiter = delimiter.strip()

    def update(self): pass

    def instances(self, stub=True):
        instances = set()
        with open(self.csvPath, 'rb') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=self.fields, delimiter=self.delimiter)
            for row in reader:
                instances.add(Instance(row['name'].strip(), row['address'].strip()))

        return list(instances)
