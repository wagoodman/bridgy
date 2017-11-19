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
    def config_template_path(self):
        return CONFIG_TEMPLATE_NAME

    def verify(self):

        if self.dig('inventory', 'source') == None:
            logger.error("No inventory source specified (%s):" % self.path)
            sys.exit(1)
        
        if self.dig('inventory', 'include_pattern') != None and self.dig('inventory', 'exclude_pattern') != None:
            logger.error("'exclude_pattern' and 'include_pattern' are mutually exclusive")
            sys.exit(1)

        for source, srcCfg in self.sources():
            # verify each source here
            if source == 'newrelic':
                if 'insights_query_api_key' in srcCfg and srcCfg['insights_query_api_key'] == "API_KEY":
                    logger.error("New Relic inventory selected but no API key was specified: %s" % self.path)
                    sys.exit(1)
