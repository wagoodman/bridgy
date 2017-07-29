import abc
import collections
from fuzzywuzzy import fuzz

Instance = collections.namedtuple("Instance", "name address")

class InventorySource(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, config): pass

    @abc.abstractproperty
    def name(self): pass

    @abc.abstractmethod
    def update(self): pass

    @abc.abstractmethod
    def instances(self, stub=True): pass

    def search(self, targets, partial=True, fuzzy=False):
        allInstances = self.instances()
        matchedInstances = set()

        for host in targets:
            for instance in allInstances:
                if fuzzy:
                    score = fuzz.partial_ratio(
                        host.lower(), instance.name.lower())
                    if score > 95 or host.lower() in instance.name.lower():
                        matchedInstances.add(instance)
                elif partial and host.lower() in instance.name.lower():
                    matchedInstances.add(instance)
                elif host.lower() == instance.name.lower():
                    matchedInstances.add(instance)

        return matchedInstances
