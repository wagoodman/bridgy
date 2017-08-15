import boto3
import placebo
import logging

from bridgy.inventory.source import InventorySource, Instance

logger = logging.getLogger()

class AwsInventory(InventorySource):

    name = 'aws'

    def __init__(self, cache_dir, access_key_id=None, secret_access_key=None, session_token=None, region=None):
        if access_key_id == None and secret_access_key == None and session_token == None and region == None:
            session = boto3.Session(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                aws_session_token=session_token,
                region_name=region
            )
        else:
            session = boto3.Session()

        self.pill = placebo.attach(session, data_path=cache_dir)

        self.client = session.client('ec2')

    def update(self):
        try:
            self.__ec2_search(stub=False)
        except KeyboardInterrupt:
            logger.error("Cancelled by user")

    def instances(self):
        data = self.__ec2_search(stub=True)

        instances = []
        for reservation in data['Reservations']:
            for instance in reservation['Instances']:

                # try to find the best dns/ip address to reach this box
                address = None
                if instance['PublicDnsName']:
                    address = instance['PublicDnsName']
                elif instance['PrivateIpAddress']:
                    address = instance['PrivateIpAddress']

                # try to find the best field to match a name against
                name = None
                if 'Tags' in list(instance.keys()):
                    for tagDict in instance['Tags']:
                        if tagDict['Key'] == 'Name':
                            name = tagDict['Value']
                            break

                if name == None:
                    if instance['PublicDnsName']:
                        name = instance['PublicDnsName']
                    elif instance['PrivateDnsName']:
                        name = instance['PrivateDnsName']

                # take note of this instance
                if name != None and address != None:
                    instances.append(Instance(name, address))

        return instances

    def __ec2_search(self, tag=None, value=None, stub=True):
        filters = []
        if value:
            filters.append({
                'Name': 'tag:' + tag,
                'Values': [value]
            })

        if stub:
            self.pill.playback()
            data = self.client.describe_instances(Filters=filters)
        else:
            self.pill.record()
            data = self.client.describe_instances(Filters=filters)
            self.pill.stop()
        return data
