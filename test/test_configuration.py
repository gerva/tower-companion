import os
import pytest
from lib.configuration import Config, ConfigError

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
EMPTY_CONFIG = os.path.join(CURRENT_DIR, 'empty_config_1')
WRITE_CONFIG = os.path.join(CURRENT_DIR, 'write_config_1')


def test_configuration_initialization():
    config_file = EMPTY_CONFIG
    config = Config(config_file)
    assert config.configparser.has_section('general') == True
    with pytest.raises(ConfigError):
        config.get('this value does not exist')


def test_values_from_environment():
    config_file = EMPTY_CONFIG
    config = Config(config_file)
    path = os.environ['PATH']
    config._update_from_env('PATH', 'path')
    assert config.has_option('path') == True
    assert config.get('path') == path


def test_reckless_mode(monkeypatch):
    config_file = EMPTY_CONFIG
    config = Config(config_file)

    def mockreturn(section, option):
        return True
    monkeypatch.setattr(config.configparser, 'getboolean', mockreturn)
    config._reckless_mode()


def test_multiple_add_general_section():
    config_file = EMPTY_CONFIG
    config = Config(config_file)
    config._add_general_section()
    config._add_general_section()
    config._add_general_section()


def test_update():
    config_file = EMPTY_CONFIG
    config = Config(config_file)
    # bad values
    with pytest.raises(ConfigError):
        config.update('test', ())
    with pytest.raises(ConfigError):
        config.update('test', [])
    with pytest.raises(ConfigError):
        config.update('test', {})
    with pytest.raises(ConfigError):
        config.update('test', 0)
    with pytest.raises(ConfigError):
        config.update('test', 0.0)
    with pytest.raises(ConfigError):
        config.update('test', None)
    # bad options
    with pytest.raises(ConfigError):
        config.update((), 'test')
    with pytest.raises(ConfigError):
        config.update([], 'test')
    with pytest.raises(ConfigError):
        config.update({}, 'test')
    with pytest.raises(ConfigError):
        config.update(10, 'test')
    with pytest.raises(ConfigError):
        config.update(0.0, 'test')
    with pytest.raises(ConfigError):
        config.update(None, 'test')

    option = 'option'
    value = 'value'
    config.update(option, value)
    assert config.get(option) == value


def test_getboolean():
    config_file = EMPTY_CONFIG
    config = Config(config_file)
    config.update('test', '')
    assert config.configparser.has_section('general') == True
    with pytest.raises(ConfigError):
        config.getboolean('this value does not exist')


def test_configuration_write():
    config_file = EMPTY_CONFIG
    out_config_file = WRITE_CONFIG
    config = Config(config_file)
    option = 'write_test'
    value = 'a_test_just_a_test'
    # write the new file
    config.update(option, value)
    assert config.get(option) == value
    config.config_file = out_config_file
    config.write()
    # read the new configuration
    new_config = Config(WRITE_CONFIG)
    assert new_config.get(option) == value


def teardown_module(module):
    for filename in (EMPTY_CONFIG, WRITE_CONFIG):
        try:
            os.remove(filename)
        except OSError:
            # filename does not exist
            pass
