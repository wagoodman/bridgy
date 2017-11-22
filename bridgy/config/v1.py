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
        source = self.dig('inventory', 'source')
        return [ (source, self[source],) ]

    @property
    def version(self):
        return 1

    @property
    def config_template_path(self):
        return CONFIG_TEMPLATE_NAME

    def verify(self):
        source = self.dig('inventory', 'source')
        if source == None:
            logger.error("No inventory source specified (%s):" % self.path)
            sys.exit(1)

        if source == 'newrelic' and self.dig('newrelic', 'insights_query_api_key') == "API_KEY":
            logger.error("New Relic inventory selected but no API key was specified: %s" % self.path)
            sys.exit(1)

        if source not in self.conf.keys():
            logger.error("No inventory-specific section specified for %s source (%s):" % (repr(source), self.path))
            sys.exit(1)

        if self.dig('inventory', 'include_pattern') != None and self.dig('inventory', 'exclude_pattern') != None:
            logger.error("'exclude_pattern' and 'include_pattern' are mutually exclusive")
            sys.exit(1)
