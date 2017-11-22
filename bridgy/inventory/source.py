import abc
import warnings
import collections

with warnings.catch_warnings():
    # Thiw warns about using the slow implementation of SequenceMatcher
    # instead of the python-Levenshtein module, which requires compilation.
    # I'd prefer for users tp simply use this tool without the need to
    # compile since the search space is probably fairly small
    warnings.filterwarnings("ignore", category=UserWarning)
    from fuzzywuzzy import fuzz

Instance = collections.namedtuple("Instance", "name address aliases source")
# allow there to be optional kwargs that default to None
Instance.__new__.__defaults__ = (None,) * len(Instance._fields)

class InventorySource(object):
    __metaclass__ = abc.ABCMeta

    name = "Invalid"

    def __init__(self, *args, **kwargs):
        if 'name' in kwargs:
            self.name = "%s (%s)" % (kwargs['name'], self.name)

    @abc.abstractmethod
    def update(self): pass

    @abc.abstractmethod
    def instances(self, stub=True): pass

    def search(self, targets, partial=True, fuzzy=False):
        allInstances = self.instances()
        matchedInstances = set()

        for host in targets:
            for instance in allInstances:
                names = [instance.name]
                if instance.aliases != None:
                    names += list(instance.aliases)
                for name in names:
                    if host.lower() == name.lower():
                        matchedInstances.add((100, instance))
                    elif partial and host.lower() in name.lower():
                        matchedInstances.add((99, instance))
                    
                    if fuzzy:
                        score = fuzz.partial_ratio(host.lower(), name.lower())
                        if score > 85 or host.lower() in name.lower():
                            matchedInstances.add((score, instance))

        # it is possible for the same instance to be matched, if so, it should only
        # appear on the return list once (still ordered by the most probable match)
        return list(collections.OrderedDict([(v, None) for k, v in sorted(list(matchedInstances))]).keys())


class InventorySet(InventorySource):

    def __init__(self, inventories=None, **kwargs):
        super(InventorySet, self).__init__(inventories, **kwargs)
        self.inventories = []

        if inventories != None:
            if not isinstance(inventories, list) and not isinstance(inventories, tuple):
                raise RuntimeError("InventorySet only takes a list of inventories. Given: %s" % repr(type(inventories)))

            for inventory in inventories:
                self.add(inventory)

    def add(self, inventory):
        if not isinstance(inventory, InventorySource):
            raise RuntimeError("InventorySet item is not an inventory. Given: %s" % repr(type(inventory)))

        self.inventories.append(inventory)

    @property
    def name(self):
        return " + ".join([inventory.name for inventory in self.inventories])

    def update(self):
        for inventory in self.inventories:
            inventory.update()

    def instances(self, stub=True):
        instances = []

        for inventory in self.inventories:
            instances.extend(inventory.instances())

        return instances

    def search(self, targets, partial=True, fuzzy=False):
        instances = []

        for inventory in self.inventories:
            instances.extend(inventory.search(targets, partial, fuzzy))

        return instances