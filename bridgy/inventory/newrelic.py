import os
import json
import requests
try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

from bridgy.inventory.source import InventorySource, Instance

class NewRelicInventory(InventorySource):

    name = 'newrelic'
    url = "https://insights-api.newrelic.com/v1/accounts/{}/query?nrql={}"

    def __init__(self, account_number, insights_query_api_key, data_path, proxies=None, **kwargs):
        super(NewRelicInventory, self).__init__(account_number, insights_query_api_key, data_path, proxies, **kwargs)

        self.account_number = account_number
        self.insights_query_api_key = insights_query_api_key
        self.data_file = os.path.join(data_path, '%s.json' % str(account_number))
        self.query = quote_plus("SELECT entityName, fullHostname, hostname, ipV4Address from NetworkSample LIMIT 999")
        if proxies:
            self.proxies = proxies
        else:
            self.proxies = {}

    def update(self):
        headers = {'X-Query-Key': self.insights_query_api_key,
                   'Accept': 'application/json'}

        response = requests.get(NewRelicInventory.url.format(self.account_number, self.query),
                                headers=headers,
                                proxies=self.proxies)

        with open(self.data_file, 'w') as data_file:
            data_file.write(response.text)

    def instances(self):
        instances = set()
        with open(self.data_file, 'r') as data_file:
            data = json.load(data_file)

        for results_dict in data['results']:
            for event_dict in results_dict['events']:
                hostname = event_dict['hostname']
                address = event_dict['ipV4Address'].strip().split("/")[0]
                if hostname == None:
                    hostname = address
                instances.add(Instance(hostname, address, None, self.name))

        return list(instances)
