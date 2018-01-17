from yaml.representer import Representer
import collections
import logging
import yaml
import sys
import os

from bridgy import inventory
from bridgy.config.base import ConfigBase

logger = logging.getLogger()

CONFIG_TEMPLATE_NAME = 'sample_config_1.yml'


class Config(ConfigBase):

    def sources(self):
        srcCfg = self.dig('inventory', 'source')
        if srcCfg:
            return [ (srcCfg['type'], srcCfg,) ]
        return []

    @property
    def version(self):
        return 1

    @property
    def config_template_path(self):
        return CONFIG_TEMPLATE_NAME

    def verify(self):
        super(Config, self).verify()

        for source, srcCfg in self.sources():
            if source not in srcCfg.keys():
                logger.error("No inventory-specific section specified for %s source (%s):" % (repr(source), self.path))
                sys.exit(1)


