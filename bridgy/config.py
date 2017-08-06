from __future__ import absolute_import
from yaml.representer import Representer
import collections
import logging
import yaml
import os

from bridgy import inventory

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

# all newrelic inventory configuration
newrelic:
  account_number: ACCOUNT_NUMBER
  insights_query_api_key: API_KEY

# define ssh behavior and preferences
ssh:
  user: ubuntu
  options: -C -o ServerAliveInterval=255
  command: sudo -i su - another_user -s /bin/bash

# if you need to connect to aws hosts via a bastion, then
# provide all connectivity information here
bastion:
  user: ubuntu
  address: zest
  options: -C -o ServerAliveInterval=255

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


class Config(object):
    __path = "~/.bridgy/config.yml"
    __inventory = "~/.bridgy/inventory"
    __mount = "~/.bridgy/mounts"
    __conf = None

    def __init__(self, initial_data=None):
        self.__conf = initial_data

    def read(self):
        # ensure yaml uses a defaultdict(str)
        yaml.add_representer(collections.defaultdict,
                             Representer.represent_str)
        with open(os.path.expanduser(self.__path), 'r') as fh:
            self.__conf = yaml.load(fh)

    def create(self):
        config_file = os.path.expanduser(self.__path)
        if not os.path.exists(config_file):
            logging.getLogger().info("Creating %s" % self.__path)
            parent_dir = os.path.dirname(config_file)
            if not os.path.exists(parent_dir):
                os.mkdir(parent_dir)
            with open(config_file, 'w') as fh:
                fh.write(CONFIG_TEMPLATE)

        inventory_cache = os.path.expanduser(self.__inventory)
        if not os.path.exists(inventory_cache):
            parent_dir = os.path.dirname(inventory_cache)
            if not os.path.exists(parent_dir):
                os.mkdir(parent_dir)
            os.mkdir(inventory_cache)

        for source in list(inventory.SOURCES.keys()):
            source_path = os.path.join(inventory_cache, source)
            if not os.path.exists(source_path):
                os.mkdir(source_path)

        mount_path = os.path.expanduser(self.__mount)
        if not os.path.exists(mount_path):
            os.mkdir(mount_path)

    def inventoryDir(self, source):
        if source not in list(inventory.SOURCES.keys()):
            raise RuntimeError(
                "Unexpected inventory source: %s" % repr(source))
        return os.path.join(os.path.expanduser(self.__inventory),
                            source)

    @property
    def mount_root_dir(self):
        return os.path.expanduser(self.__mount)

    # TODO
    def verify(self): pass

    def __iter__(self):
        return iter(self.__conf)

    def dig(self, *original_keys):
        def __dig(d, *keys):
            try:
                if len(keys) == 1:
                    return d[keys[0]]
                return __dig(d[keys[0]], *keys[1:])
            except KeyError:
                return None
        return __dig(self.__conf, *original_keys)

    def __getitem__(self, key):
        return self.__conf[key]

    def __setitem__(self, key, value):
        self.__conf[key] = value

    def __repr__(self):
        return repr(self.__conf)
