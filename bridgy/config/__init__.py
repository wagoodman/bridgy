import collections
import logging
import yaml
import sys
import os
from yaml.representer import Representer

from bridgy.config.base import ConfigBase

logger = logging.getLogger()


def _readConfig():
    # ensure yaml uses a defaultdict(str)
    yaml.add_representer(collections.defaultdict,
                         Representer.represent_str)
    try:
        with open(os.path.expanduser(ConfigBase.path), 'r') as fh:
            config = yaml.load(fh)
    except Exception as ex:
        logger.error("Unable to read config (%s): %s" % (ConfigBase.path, ex))
        sys.exit(1)

    return config

def _detectConfigSchema(config):
    if 'config-schema' in config:
        return str(config['config-schema'])

    if 'inventory' in config:
        if 'source' in config['inventory']:
            source = config['inventory']['source']
            if isinstance(source, str):
                return '1'
            if isinstance(source, list):
                return '2'

    # support legacy behavior: default to original config schema if detection fails
    return '1'

def Config(initialData=None):
    if initialData != None:
        configContents = initialData
        schema = _detectConfigSchema(configContents)
    else:
        if os.path.exists(os.path.expanduser(ConfigBase.path)):
            configContents = _readConfig()
            schema = _detectConfigSchema(configContents)
        else:
            # the config does not exist and needs to be created. Use the latest schema
            schema = '2'

    if schema == '2':
        from bridgy.config.v2 import Config
        return Config(initialData)

    elif schema == '1':
        from bridgy.config.v1 import Config
        return Config(initialData)
    
    raise RuntimeError("Listed config schema is unsupported (%s)." % repr(schema))