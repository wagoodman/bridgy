from yaml.representer import Representer
import collections
import logging
import yaml
import sys
import os

from bridgy import inventory
from bridgy.config.base import ConfigBase

logger = logging.getLogger()

CONFIG_TEMPLATE_NAME = 'sample_config_2.yml'


class Config(ConfigBase):

    def sources(self):
        sources = self.dig('inventory', 'source')
        ret = []
        for srcCfg in sources:
            source = srcCfg['type']
            ret.append( (source, srcCfg, ) )
        return ret

    @property
    def version(self):
        return 2

    @property
    def config_template_path(self):
        return CONFIG_TEMPLATE_NAME

    def verify(self):
        super(Config, self).verify()

        for source, srcCfg in self.sources():
            if source == 'aws':
                if 'name' not in srcCfg:
                    logger.error("AWS inventory sources must specify name.")
                    sys.exit(1)
                if 'profile' in srcCfg:
                    if 'access_key_id' in srcCfg or 'secret_access_key' in srcCfg or 'session_token' in srcCfg:
                        logger.error("AWS profile conflicts with access_key_id, secret_access_key, or session_token.")
                        sys.exit(1)
                if 'access_key_id' in srcCfg or 'secret_access_key' in srcCfg or 'session_token' in srcCfg:
                    if 'profile' in srcCfg:
                        logger.error("AWS access_key_id, secret_access_key, and session_token conflict with profile.")
                        sys.exit(1)
