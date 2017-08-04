from source import InventorySource, Instance

import os
import json
import urllib
import requests

class NewRelicInventory(InventorySource):

    name = 'newrelic'
    url = "https://insights-api.newrelic.com/v1/accounts/{}/query?nrql={}"
    query = urllib.quote_plus("SELECT entityName, fullHostname, hostname, ipV4Address from NetworkSample LIMIT 999")

    def __init__(self, account_number, insights_query_api_key, data_path):
        self.account_number = account_number
        self.insights_query_api_key = insights_query_api_key
        self.data_file = os.path.join(data_path, '%s.json' % str(account_number))

    def update(self):
        headers = {'X-Query-Key': self.insights_query_api_key,
                   'Accept': 'application/json'}
        response = requests.get(NewRelicInventory.url.format(self.account_number, NewRelicInventory.query),
                                headers=headers)

        with open(self.data_file, 'wb') as data_file:
            data_file.write(response.text)

    def instances(self):
        instances = set()
        with open(self.data_file, 'rb') as data_file:
            data = json.load(data_file)

        for results_dict in data['results']:
            for event_dict in results_dict['events']:
                hostname = event_dict['hostname']
                address = event_dict['ipV4Address'].strip().split("/")[0]
                if hostname == None:
                    hostname = address
                instances.add(Instance(hostname, address))

        return list(instances)
