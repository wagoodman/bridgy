import os
import csv
import sys
import logging

from bridgy.inventory.source import InventorySource, Instance, InstanceType

logger = logging.getLogger()

class CsvInventory(InventorySource):

    name = 'csv'

    def __init__(self, path, fields, delimiter=',', **kwargs):
        if 'name' not in kwargs and 'file' in kwargs:
            kwargs['name'] = kwargs['file']

        super(CsvInventory, self).__init__(path, fields, delimiter, **kwargs)

        self.csv_path = path
        self.fields = [f.strip() for f in fields.split(",")]
        self.delimiter = delimiter.strip()

    def update(self): pass

    def instances(self):
        instances = set()
        try:
            with open(self.csv_path, 'r') as csv_file:
                reader = csv.DictReader(csv_file, fieldnames=self.fields, delimiter=self.delimiter)
                for row in reader:
                    instances.add(Instance(row['name'].strip(), row['address'].strip(), None, self.name, None, InstanceType.VM))
        except IOError as ex:
            logger.error("Unable to read inventory: %s" % ex)
            sys.exit(1)
        return list(instances)
