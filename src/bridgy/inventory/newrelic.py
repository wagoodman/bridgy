from source import InventorySource, Instance

import os
import json
import requests

class NewRelicInventory(InventorySource):

    name = 'newrelic'

    def __init__(self, account_number, insights_query_api_key, data_path):
        self.account_number = account_number
        self.insights_query_api_key = insights_query_api_key
        self.data_file = os.path.join(data_path, '%s.json' % str(account_number))

    def update(self):
        pass

    def instances(self):
        instances = set()
        with open(self.data_file, 'rb') as data_file:
            data = json.load(data_file)

        for results_dict in data['results']:
            for event_dict in results_dict['events']:
                instances.add(Instance(event_dict['event']['fullHostname'].strip(),
                                       event_dict['event']['ipV4Address'].strip().split("/")[0]))

        return list(instances)
