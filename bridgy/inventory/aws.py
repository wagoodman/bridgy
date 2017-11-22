import os
import boto3
import placebo
import logging

from bridgy.inventory.source import InventorySource, Instance

logger = logging.getLogger()

class AwsInventory(InventorySource):

    name = 'aws'

    # kwargs: access_key_id, secret_access_key, session_token, region, profile, config_path
    def __init__(self, cache_dir, **kwargs):
        super(AwsInventory, self).__init__(cache_dir, **kwargs)

        # this is an override for the config location (at least useful for testing)
        if 'config_path' in kwargs:
            os.environ['AWS_CONFIG_FILE'] = os.path.join(kwargs['config_path'], "config")
            os.environ['AWS_SHARED_CREDENTIALS_FILE'] = os.path.join(kwargs['config_path'], "credentials")

        if 'profile' in kwargs and kwargs['profile'] != None:
            session = boto3.Session(
                profile_name=kwargs['profile'],
                region_name=kwargs['region']
            )
        elif 'access_key_id' in kwargs and 'secret_access_key' in kwargs and 'session_token' in kwargs and 'region' in kwargs:
            session = boto3.Session(
                aws_access_key_id=kwargs['access_key_id'],
                aws_secret_access_key=kwargs['secret_access_key'],
                aws_session_token=kwargs['session_token'],
                region_name=kwargs['region']
            )
        else:
            # pull from ~/.aws/* configs (or other boto search paths)
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
                aliases = list()
                if 'Tags' in list(instance.keys()):
                    for tagDict in instance['Tags']:
                        if tagDict['Key'] == 'Name':
                            aliases.append(tagDict['Value'])
                            break

                if instance['PublicDnsName']:
                    aliases.append(instance['PublicDnsName'])
                if instance['PrivateDnsName']:
                    aliases.append(instance['PrivateDnsName'])
                if instance['InstanceId']:
                    aliases.append(instance['InstanceId'])

                aliases[:] = [x for x in aliases if x != None]
                name = aliases.pop(0)

                # take note of this instance
                if name != None and address != None:
                    if len(aliases) > 0:
                        instances.append(Instance(name, address, tuple(aliases), self.name))
                    else:
                        instances.append(Instance(name, address, self.name))

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
