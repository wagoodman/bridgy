from yaml.representer import Representer
import collections
import logging
import yaml
import os

CONFIG_TEMPLATE = """
# what source should be used as an inventory source
inventory:
  source: csv
  update_at_start: false

# if you are using a csv file
csv:
  name: example.csv
  # requires at least name and address
  fields: name, address, random
  delimiter: '|'

# all aws inventory configuration
aws:
  access_key_id: ACCESS_KEY
  secret_access_key: SECRET_KEY
  session_token: SESSION_TOKEN
  region: us-west-2

# define ssh behavior and preferences
ssh:
  user: ubuntu
  template: -C -o ServerAliveInterval=255
  command: sudo -i su - another_user -s /bin/bash

# if you need to connect to aws hosts via a bastion, then
# provide all connectivity information here
bastion:
  user: ubuntu
  address: zest
  template: -C -o ServerAliveInterval=255

# define tmux layouts and (optional) canned commands
tmux:
  layout:
    # bridgy ssh -l example host...
    example:
      - cmd: split-window -h
        run: echo "first split" && bash
      - cmd: split-window -h
        run: echo "second split" && bash
      - cmd: split-window -v
        run: echo "third split" && bash
"""


# closest to a singleton config that acts like a dict
class ConfigDef(type):
    __path = "~/.bridgy/config.yml"
    __inventory = "~/.bridgy/inventory"
    __mount = "~/.bridgy/mounts"
    __conf = None
    inventorySources = ['gcp', 'aws', 'csv']

    @classmethod
    def read(cls):
        # ensure yaml uses a defaultdict(str)
        yaml.add_representer(collections.defaultdict,
                             Representer.represent_str)
        with open(os.path.expanduser(ConfigDef.__path), 'r') as fh:
            ConfigDef.__conf = yaml.load(fh)

    @classmethod
    def create(cls):
        configFile = os.path.expanduser(ConfigDef.__path)
        if not os.path.exists(configFile):
            logging.getLogger().info("Creating %s" % ConfigDef.__path)
            parentDir = os.path.dirname(configFile)
            if not os.path.exists(parentDir):
                os.mkdir(parentDir)
            with open(configFile, 'w') as fh:
                fh.write(CONFIG_TEMPLATE)

        inventoryCache = os.path.expanduser(ConfigDef.__inventory)
        if not os.path.exists(inventoryCache):
            parentDir = os.path.dirname(inventoryCache)
            if not os.path.exists(parentDir):
                os.mkdir(parentDir)
            os.mkdir(inventoryCache)

        for source in Config.inventorySources:
            sourcePath = os.path.join(inventoryCache, source)
            if not os.path.exists(sourcePath):
                os.mkdir(sourcePath)

        mountPath = os.path.expanduser(ConfigDef.__mount)
        if not os.path.exists(mountPath):
            os.mkdir(mountPath)


    def inventoryDir(cls, source):
        if source not in Config.inventorySources:
            raise RuntimeError(
                "Unexpected inventory source: %s" % repr(source))
        return os.path.join(os.path.expanduser(ConfigDef.__inventory),
                            source)

    @property
    def mountRootDir(cls):
        return os.path.expanduser(ConfigDef.__mount)

    # TODO
    @classmethod
    def verify(cls): pass

    @classmethod
    def __iter__(cls):
        return iter(ConfigDef.__conf)

    @classmethod
    def __getitem__(cls, key):
        return ConfigDef.__conf[key]

    @classmethod
    def __repr__(cls):
        return repr(ConfigDef.__conf)


class Config(object):
    __metaclass__ = ConfigDef
