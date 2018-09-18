import os
import boto3
import shutil
import placebo
import logging
import itertools

from bridgy.inventory.source import InventorySource, Instance, InstanceType

logger = logging.getLogger()

def groupsOf(n, iterable):
    it = iter(iterable)
    while True:
       chunk = tuple(itertools.islice(it, n))
       if not chunk:
           return
       yield chunk

class AwsInventory(InventorySource):

    name = 'aws'

    # kwargs: access_key_id, secret_access_key, session_token, region, profile, config_path
    def __init__(self, cache_dir, **kwargs):
        super(AwsInventory, self).__init__(cache_dir, **kwargs)
        self.cache_dir = cache_dir

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

        self.ec2Client = session.client('ec2')
        self.ecsClient = session.client('ecs')

    def update(self):
        try:
            self.__ecs_search(stub=False)
            self.__ec2_search(stub=False)
        except KeyboardInterrupt:
            logger.error("Cancelled by user")

    def instances(self):
        instances = []
        # instances.extend(self.ec2Instances())
        instances.extend(self.ecsInstances())
        return instances

    def ec2Instances(self):
        data = self.__ec2_search(stub=True)

        instances = []
        for reservation in data['Reservations']:
            for instance in reservation['Instances']:

                # try to find the best dns/ip address to reach this box
                address = None
                if instance.get('PublicDnsName'):
                    address = instance['PublicDnsName']
                elif instance.get('PrivateIpAddress'):
                    address = instance['PrivateIpAddress']

                # try to find the best field to match a name against
                aliases = list()
                if 'Tags' in list(instance.keys()):
                    for tagDict in instance['Tags']:
                        if tagDict['Key'] == 'Name':
                            aliases.insert(0, tagDict['Value'])
                        else:
                            aliases.append(tagDict['Value'])

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
                        instances.append(Instance(name, address, tuple(aliases), self.name, None, InstanceType.VM))
                    else:
                        instances.append(Instance(name, address, None, self.name, None, InstanceType.VM))

        return instances

    def ecsInstances(self):
        data = self.__ecs_search(stub=True)

        print(data)

        return []

    def __ecs_search(self, value=None, stub=True):

        def fetchData():
            allTasks = []
            taskDescriptions = {}
            clusters = self.ecsClient.list_clusters()
            for cluster in clusters['clusterArns']:
                tasks = self.ecsClient.list_tasks(cluster=cluster)
                allTasks.extend(tasks['taskArns'])
                for taskArns in groupsOf(100, allTasks):
                    descriptions = self.ecsClient.describe_tasks(cluster=cluster, tasks=taskArns)
                    for taskDescription in descriptions['tasks']:
                        taskDescriptions[taskDescription['taskArn']] = taskDescription

            for x in taskDescriptions.items():
                print(x)
            return allTasks

        if stub:
            self.pill.playback()
            allTasks = fetchData()
        else:
            # clear cache before updating
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, mode=0o755)

            # update
            self.pill.record()
            allTasks = fetchData()
            self.pill.stop()
        return allTasks

    def __ec2_search(self, tag=None, value=None, stub=True):
        filters = []
        if value:
            filters.append({
                'Name': 'tag:' + tag,
                'Values': [value]
            })

        if stub:
            self.pill.playback()
            data = self.ec2Client.describe_instances(Filters=filters)
        else:
            # clear cache before updating
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, mode=0o755)

            # update
            self.pill.record()
            data = self.ec2Client.describe_instances(Filters=filters)
            self.pill.stop()
        return data
