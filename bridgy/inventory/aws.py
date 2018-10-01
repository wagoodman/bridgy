import os
import boto3
import shutil
import placebo
import logging
import warnings
import itertools
import collections

from bridgy.inventory.source import InventorySource, Instance, InstanceType

with warnings.catch_warnings():
    # This warns about using the slow implementation of SequenceMatcher
    # instead of the python-Levenshtein module, which requires compilation.
    # I'd prefer for users tp simply use this tool without the need to
    # compile since the search space is probably fairly small
    warnings.filterwarnings("ignore", category=UserWarning)
    from fuzzywuzzy import fuzz

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
        # clear cache before updating
        shutil.rmtree(self.cache_dir)
        os.makedirs(self.cache_dir, mode=0o755)
        try:
            self.__ec2_search(stub=False)
            self.__ecs_search(stub=False)
        except KeyboardInterrupt:
            logger.error("Cancelled by user")

    def instances(self):
        instances = []
        ec2Instances = self.ec2Instances()
        instances.extend(ec2Instances)
        instances.extend(self.ecsInstances(ec2Instances))
        return instances

    def ec2Instances(self):
        data = self.__ec2_search(stub=True)

        instances = []
        for reservation in data['Reservations']:
            for instance in reservation['Instances']:
                instanceId = None
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
                    instanceId = instance['InstanceId']
                    aliases.append(instanceId)

                aliases[:] = [x for x in aliases if x != None]
                name = aliases.pop(0)

                # take note of this instance
                if name != None and address != None:
                    if len(aliases) > 0:
                        instances.append(Instance(name, address, tuple(aliases), self.name, InstanceType.VM, instanceId))
                    else:
                        instances.append(Instance(name, address, None, self.name, InstanceType.VM, instanceId))

        return instances

    def ecsInstances(self, ec2Instances):
        instances = []
        taskDescriptions, containerInstanceIds = self.__ecs_search(stub=True)

        # since we always search by instanceId, build a fast lookup
        instanceIdLookup = {}
        for instance in ec2Instances:
            if instance.instanceId != None:
                instanceIdLookup[instance.instanceId] = instance

        for taskArn, taskDescription in taskDescriptions.items():
            containerInstanceArn = taskDescription['containerInstanceArn']
            containerInstanceId = containerInstanceIds[containerInstanceArn]

            if containerInstanceId == None:
                continue
            
            if containerInstanceId not in instanceIdLookup:
                continue

            containerInstance = instanceIdLookup[containerInstanceId]

            # add the associated service with the instance so it will match on a search
            aliases = [taskDescription['group']]
            instances.append(Instance(taskArn, containerInstance.address, tuple(aliases), self.name, InstanceType.ECS, None, taskArn))

        return instances

    def __ecs_search(self, value=None, stub=True):
        def fetchData():
            taskDescriptions = {}  # { taskArn : { task-description... } }
            containerInstanceIds = {}  # { containerInstanceArn : ecs-instance-id }

            # obtain all tasks in all clusters
            clusters = self.ecsClient.list_clusters()
            for cluster in clusters['clusterArns']:
                tasksResponse = self.ecsClient.list_tasks(cluster=cluster)
                tasks = tasksResponse['taskArns']
                for taskArns in groupsOf(100, tasks):
                    descriptions = self.ecsClient.describe_tasks(cluster=cluster, tasks=taskArns)
                    for taskDescription in descriptions['tasks']:
                        taskDescriptions[taskDescription['taskArn']] = taskDescription

                        # now we have a set of container instances to later look up
                        if taskDescription['containerInstanceArn'] not in containerInstanceIds.keys():
                            containerInstanceIds[taskDescription['containerInstanceArn']] = None

            # find all container instances
            for containerInstanceArns in groupsOf(100, containerInstanceIds.keys()):
                descriptions = self.ecsClient.describe_container_instances(cluster=cluster, containerInstances=containerInstanceArns)
                for containerInstanceDescription in descriptions['containerInstances']:
                    instanceArn = containerInstanceDescription['containerInstanceArn']
                    containerInstanceIds[instanceArn] = containerInstanceDescription['ec2InstanceId']

            return taskDescriptions, containerInstanceIds

        if stub:
            self.pill.playback()
            taskDescriptions, containerInstanceIds = fetchData()
        else:
            self.pill.record()
            taskDescriptions, containerInstanceIds = fetchData()
            self.pill.stop()
        return taskDescriptions, containerInstanceIds

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
            self.pill.record()
            data = self.ec2Client.describe_instances(Filters=filters)
            self.pill.stop()
        return data
