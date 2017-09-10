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

Instance = collections.namedtuple("Instance", "name address aliases")
# allow there to be optional kwargs that default to None
Instance.__new__.__defaults__ = (None,) * len(Instance._fields)

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
                names = [instance.name]
                if instance.aliases != None:
                    names += list(instance.aliases)
                for name in names:
                    if fuzzy:
                        score = fuzz.partial_ratio(host.lower(), name.lower())
                        if score > 85 or host.lower() in name.lower():
                            matchedInstances.add((score, instance))
                    elif partial and host.lower() in name.lower():
                        matchedInstances.add((99, instance))
                    elif host.lower() == name.lower():
                        matchedInstances.add((100, instance))

        return [ v for k,v in sorted(list(matchedInstances)) ]
