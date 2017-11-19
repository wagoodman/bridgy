import pytest
import shlex

from bridgy.config import Config


def test_detect_config_schema_by_list():
    config = Config({
        'config-schema': '1'
    })

    assert config.config_template_path == 'sample_config_1.yml'

    config = Config({
        'config-schema': '2'
    })

    assert config.config_template_path == 'sample_config_2.yml'


def test_detect_config_schema_indirectly():
    config = Config({
        'inventory': {
            'source': 'csv'
        }
    })

    assert config.config_template_path == 'sample_config_1.yml'

    config = Config({
        'inventory': {
            'source': [
                {'type': 'csv'},
                {'type': 'aws'},
             ]
        }
    })

    assert config.config_template_path == 'sample_config_2.yml'