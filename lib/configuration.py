#!/usr/bin/env python
"""
Configuration handling for tower companion
"""
from __future__ import print_function
from __future__ import absolute_import
import subprocess
import os
import logging
import requests.packages.urllib3 as urllib3

from .utils import BadKarma
from .utils import which

# in python 3, ConfigParser has been renamed configparser
try:
    from ConfigParser import ConfigParser
except ImportError:
    # python 3
    from configparser import ConfigParser

CONFIG_FILE = os.path.expanduser('~/.tower_cli.cfg')

def set_tower_cli_config(key, value):
    """
    Calls tower-cli and overwrite the given key with the given value in the
    configuration file
    Args:
        key (str): configuration key to update
        value (str): configuration value to update
    """
    cmd = [which('tower-cli'),
           'config',
           key,
           value]
    tower = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tower.wait()
    if tower.returncode != 0:
        raise BadKarma(tower.stderr)
    else:
        print("Configuration for {0} overwritten".format(key))


def set_tc_config(key, value, config, config_file=CONFIG_FILE):
    """
    Modifies the tower-cli configuration for values which are not supported by
    tower-cli
    Args:
        key (str): configuration key to update
        value (str): configuration value to update
    """
    config.set('general', key, value)
    cfgfile = open(config_file, "w")
    config.write(cfgfile)
    cfgfile.close()
    print("Configuration for {0} overwritten".format(key))


def set_config(key, value, config=None):
    """
    Calles the right set configuration function based on the value which is
    to modify
    Args:
        key (str): configuration key to update
        value (str): configuration value to update
        config (ConfigParser obj): current configuration
    """
    tower_cli_config = ['host', 'username', 'password', 'verify_ssl']
    if key in tower_cli_config:
        set_tower_cli_config(key, value)
    else:
        set_tc_config(key, value, config)


def overwrite_config_tower_cli():
    """
    Search the environment for local set configuration. If values set in the
    environment variables then overwrite the tower-cli config with these values
    """
    username = os.environ.get('TC_USERNAME')
    if username:
        set_config('username', username)
    password = os.environ.get('TC_PASSWORD')
    if password:
        set_config('password', password)
    host = os.environ.get('TC_HOST')
    if host:
        set_config('host', host)
    verify_ssl = os.environ.get('TC_VERIFY_SSL')
    if verify_ssl:
        set_config('verify_ssl', verify_ssl)

def overwrite_config_tc(config):
    """
    Search the environment for local set configuration. If values set in the
    environment variables then overwrite the tower-cli config with these values
    """
    reckless_mode = os.environ.get('TC_RECKLESS_MODE')
    if reckless_mode:
        set_config('reckless_mode', reckless_mode, config)


def get_config(config_file=CONFIG_FILE):
    """
    Returns a configuration object.
    It reads the default tower_cli.cfg file
    Args:
        config_file (str): configuration file, use the tower-cli default
            configuration.
    Returns:
        config (ConfigParser): a nice convenient way to carry your configuration
            with you. Believe me it's the new black.
    """
    # This step also makes sure that the configuration will be created if at least one
    # value is given as environment variable
    overwrite_config_tower_cli()

    if not os.path.isfile(config_file):
        raise BadKarma('No configuration set. Refusing to proceed any further')
    config = ConfigParser()
    config.read(config_file)
    # We know we have a config file which we can modify if needed
    overwrite_config_tc(config)
    if config.has_option('general', 'reckless_mode'):
        if config.get('general', 'reckless_mode') == 'yes':
            set_reckless_mode()
    return config


def set_reckless_mode():
    """
    Live fast, die young, get hacked and cry.
    If you're here, you have bad SSL certficates
    urllib3, used by requests, clobbers the output with a lot of SSL warnings
    the following lines, just disables the warning messages.

    Enable this only if you're a bad person.
    """
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.CRITICAL)
    urllib3.disable_warnings()
