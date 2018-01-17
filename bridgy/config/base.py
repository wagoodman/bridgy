import collections
import logging
import pkgutil
import yaml
import abc
import sys
import os

from yaml.representer import Representer

from bridgy import inventory

logger = logging.getLogger()


class ConfigBase(object):
    __metaclass__ = abc.ABCMeta

    path = "~/.bridgy/config.yml"
    inventory = "~/.bridgy/inventory"
    mount = "~/.bridgy/mounts"
    conf = None

    def __init__(self, initial_data=None):
        # this is usefule for testing purposes
        self.conf = initial_data

    @abc.abstractproperty
    def version(self): pass

    @abc.abstractproperty
    def config_template_path(self): pass

    @abc.abstractproperty
    def sources(self): pass

    def verify(self): 
        if self.dig('inventory', 'source') == None:
            logger.error("No inventory source specified (%s):" % self.path)
            sys.exit(1)

        if self.dig('inventory', 'include_pattern') != None and self.dig('inventory', 'exclude_pattern') != None:
            logger.error("'exclude_pattern' and 'include_pattern' are mutually exclusive")
            sys.exit(1)

        names = []
        dupNames = []
        for source, srcCfg in self.sources():
            if 'name' in srcCfg and srcCfg['name'] in names:
                dupNames.append(srcCfg['name'])

            # verify each source here
            if source == 'newrelic':
                if 'insights_query_api_key' in srcCfg and srcCfg['insights_query_api_key'] == "API_KEY":
                    logger.error("New Relic inventory selected but no API key was specified: %s" % self.path)
                    sys.exit(1)

        if len(dupNames) > 0:
            logger.error("Duplicate inventory source names detected: %s" % ', '.join(dupNames))
            sys.exit(1)

    @property
    def config_template_contents(self): 
        return pkgutil.get_data('bridgy', 'config/samples/' + self.config_template_path)

    def read(self):
        # ensure yaml uses a defaultdict(str)
        yaml.add_representer(collections.defaultdict,
                             Representer.represent_str)
        try:
            with open(os.path.expanduser(self.path), 'r') as fh:
                self.conf = yaml.load(fh)
        except Exception as ex:
            logger.error("Unable to read config (%s): %s" % (self.path, ex))
            sys.exit(1)

    def exists(self):
        config_file = os.path.expanduser(self.path)
        return os.path.exists(config_file)

    def create(self):
        created = False
        if not self.exists():
            config_file = os.path.expanduser(self.path)
            parent_dir = os.path.dirname(config_file)
            if not os.path.exists(parent_dir):
                os.mkdir(parent_dir)
            with open(config_file, 'wb') as fh:
                fh.write(self.config_template_contents)
            created = True

        inventory_cache = os.path.expanduser(self.inventory)
        if not os.path.exists(inventory_cache):
            parent_dir = os.path.dirname(inventory_cache)
            if not os.path.exists(parent_dir):
                os.mkdir(parent_dir)
            os.mkdir(inventory_cache)

        for source in list(inventory.SOURCES.keys()):
            source_path = os.path.join(inventory_cache, source)
            if not os.path.exists(source_path):
                os.mkdir(source_path)

        mount_path = os.path.expanduser(self.mount)
        if not os.path.exists(mount_path):
            os.mkdir(mount_path)
        
        return created

    def inventoryDir(self, source, name=''):
        if source not in list(inventory.SOURCES.keys()):
            raise RuntimeError("Unexpected inventory source: %s" % repr(source))
        return os.path.join(os.path.expanduser(self.inventory), source, name)

    @property
    def mount_root_dir(self):
        return os.path.expanduser(self.mount)

    def __iter__(self):
        return iter(self.conf)

    def dig(self, *original_keys):
        def __dig(d, *keys):
            try:
                if len(keys) == 1:
                    try:
                        return d[keys[0]]
                    except TypeError:
                        return None
                return __dig(d[keys[0]], *keys[1:])
            except KeyError:
                return None
        return __dig(self.conf, *original_keys)

    def __getitem__(self, key):
        return self.conf[key]

    def __setitem__(self, key, value):
        self.conf[key] = value

    def __repr__(self):
        return repr(self.conf)
