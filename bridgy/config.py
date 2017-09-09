from yaml.representer import Representer
import collections
import logging
import yaml
import sys
import os

from bridgy import inventory

logger = logging.getLogger()

CONFIG_TEMPLATE = """
# Bridgy uses an inventory of hostnames and addresses as a source to search against and ssh into.
inventory:
#   # Supported values are: csv, newrelic, aws
#   source: csv

  # Attempts to pull the latest inventory when running any bridgy command (optional)
  update_at_start: true

  # When matching instance names to a given input, use fuzzy search instead of partial match
  fuzzy_search: true

  # If you need to fetch your inventory from behind a proxy bridgy will first check for http_proxy and https_proxy
  # keys from the config, then check the environment for the same keys. (optional)
  # http_proxy: someurl
  # https_proxy: someurl

# All inventory parameters for a CSV source
csv:
  # Name of the inventory CSV placed in ~/.bridgy/inventory/csv
  # name: example.csv

  # These are the csv column names, specify at least 'name' and 'address'
  # fields: name, address, random

  # Optional. Defaults to ','
  # delimiter: '|'

# All inventory parameters to support querying AWS
aws:
  # ~/.aws/* configs will be referenced by default, but can be overridden here

  # access_key_id: ACCESS_KEY
  # secret_access_key: SECRET_KEY
  # session_token: SESSION_TOKEN
  # region: us-west-2

# All inventory parameters to support querying AWS
newrelic:
  # account_number: ACCOUNT_NUMBER
  # insights_query_api_key: API_KEY

# All SSH connectivity configuration
ssh:
  # User to use when SSHing into a host (optional)
  # user: johnybgoode

  # Any valid cli options you would specify to SSH (optional)
  # Note: these options are not applied to sshfs
  options: -C -o ForwardAgent=yes -o FingerprintHash=sha256 -o TCPKeepAlive=yes -o ServerAliveInterval=255 -o StrictHostKeyChecking=no

  # Run a command upon logging into any host (optional)
  # command: sudo -i su - another_user -s /bin/bash

  # Tmux is automatically used to wrap all ssh sessions, specify otherwise here (optional)
  # no-tmux: true

# If you need to connect to aws hosts via a bastion, then provide all connectivity information here
bastion:
  # User to use when SSHing into the bastion host (optional)
  # user: johnybgoode

  # Address of the bastion host
  # address: zest

  # Any valid cli options you would specify to SSH (optional)
  options: -C -o ServerAliveInterval=255 -o FingerprintHash=sha256 -o ForwardAgent=yes -o TCPKeepAlive=yes

# This specifies any SSHFS options for mounting remote directories
sshfs:
   # Any sshfs option that you would specify to sshfs (optional)
   # Tip: if you need to be another user on the remote system you can do so via sudo:
   # options: -o sftp_server="/usr/bin/sudo /usr/lib/openssh/sftp-server"
   options: -o auto_cache,reconnect,no_readahead -C -o TCPKeepAlive=yes -o ServerAliveInterval=255 -o StrictHostKeyChecking=no

tmux:

  # You can make multiple panes to a single host by specifying a layout definition. Simply
  # define each tmux command to run and an optional command to run in that pane.
  # Use these layouts by name with the -l cli option (bridgy ssh -l somename host...)
  layout:
  # an example layout... :

  #  somename:
  #  - cmd: split-window -h
  #    run: echo "first split" && bash
  #  - cmd: split-window -h
  #    run: echo "second split" && bash
  #  - cmd: split-window -v
  #     run: echo "third split" && bash

  # another example layout... :
  #  someothername:
  #  - cmd: split-window -h
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
        try:
            with open(os.path.expanduser(self.__path), 'r') as fh:
                self.__conf = yaml.load(fh)
        except Exception as ex:
            logger.error("Unable to read config (%s): %s" % (self.__path, ex))
            sys.exit(1)

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

    def verify(self):
        source = self.dig('inventory', 'source')
        if source == None:
            logger.error("No inventory source specified (%s):" % self.__path)
            sys.exit(1)

        if source == 'newrelic' and self.dig('newrelic', 'insights_query_api_key') == "API_KEY":
            logger.error("New Relic inventory selected but no API key was specified: %s" % self.__path)
            sys.exit(1)

        if source not in self.__conf.keys():
            logger.error("No inventory-specific section specified for %s source (%s):" % (repr(source), self.__path))
            sys.exit(1)

    def __iter__(self):
        return iter(self.__conf)

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
        return __dig(self.__conf, *original_keys)

    def __getitem__(self, key):
        return self.__conf[key]

    def __setitem__(self, key, value):
        self.__conf[key] = value

    def __repr__(self):
        return repr(self.__conf)