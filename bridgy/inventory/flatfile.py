import os
import csv

from inventory.source import InventorySource, Instance

class CsvInventory(InventorySource):

    name = 'csv'

    def __init__(self, path, fields, delimiter=','):
        self.csv_path = path
        self.fields = [f.strip() for f in fields.split(",")]
        self.delimiter = delimiter.strip()

    def update(self): pass

    def instances(self):
        instances = set()
        with open(self.csv_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file, fieldnames=self.fields, delimiter=self.delimiter)
            for row in reader:
                instances.add(Instance(row['name'].strip(), row['address'].strip()))

        return list(instances)
