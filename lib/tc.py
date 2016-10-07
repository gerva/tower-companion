#!/usr/bin/env python
"""
Start and monitor ansilbe tower jobs from the command line, in real time.
Grab your pop corns.
"""
from __future__ import print_function
import click
import json
import logging
import os
import requests
import subprocess
import sys
import yaml
from time import sleep
import requests.packages.urllib3 as urllib3


# in python 3, ConfigParser has been renamed configparser
try:
    from ConfigParser import ConfigParser
except ImportError:
    # python 3
    from configparser import ConfigParser


# some constants
CONFIG_FILE = os.path.expanduser('~/.tower_cli.cfg')
SLEEP_INTERVAL = 1.0  # sleep interval

# more about the configuration file:
# this script expects you have a file called ~/.tower_cli.cfg with the following
# content:
#
# [general]
# host = myansibletower.com
# username = jdoe
# password = super_secret
# verify_ssl = false


class BadKarma(Exception):
    """
    What goes around comes around
    """
    pass


def which(executable):
    """
    A poor man replacement for the 'which' command
    It returns a string with the path of executable.
    It returns an empty string if executable is not found
    Also this function is not nice at all. Ask it to find something it does not
    exist and it will give you a BadKarma exception

    Args:
        executable (str): name of the executable

    Returns:
        (str): executable path

    Raises:
        BadKarma
    """
    for path in os.environ['PATH'].split(':'):
        full_path = os.path.join(path, executable)
        if os.path.isfile(full_path):
            return full_path
    msg = "{0} is not in your path. Giving up. Have a good day".format(
        executable)
    raise BadKarma(msg)


def set_config(key, value):
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


def overwrite_config():
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
    overwrite_config()
    if not os.path.isfile(config_file):
        raise BadKarma('No configuration set. Refusing to proceed any further')
    config = ConfigParser()
    config.read(config_file)
    if config.has_option('general', 'reckless_mode'):
        if config.get('general', 'reckless_mode') == 'yes':
            reckless_mode()
    return config


def reckless_mode():
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


def get_template_id_from_name(template_name):
    """
    Returns a template id from a template name
    Args:
        template_name (str): the name of template

    Retruns:
        (str): template id if found

    Raises:
        BadKarma
    """
    cmd = [which('tower-cli'),
           'job_template',
           'get',
           '--name', template_name,
           '--format=json']
    tower = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # We can block here, it takes a split of a second to ask ansible tower to
    # start a specific job.
    tower.wait()
    try:
        result = json.load(tower.stdout)
        return result['id']
    except ValueError:
        msg = "Did not find {0} template".format(template_name)
        raise BadKarma(msg)


def _validate_extra_vars(extra_vars):
    """
    according to the tower-cli inline help.
    -e, --extra-vars TEXT   yaml format text that contains extra variables to
    pass on. Use @ to get these from a file.

    This function needs some love.

    Args:
        extra_vars (str): yml formatted string that contains your extra
            variables for your job template
    """
    # check if extra_vars is a file
    if extra_vars.startswith('@'):
        # yes, it's a file, let's check this file exists..
        # partition all the way! If you think the next line of code is
        # unreadealbe, you're probably right, but regex won't make it any better
        # Let's delegate the validation of the yml file to tower-cli.
        return os.path.isfile(extra_vars.partition['@'][2].strip())

    # extra_vars is not pointing to a file, let's try to load it..
    try:
        yaml.load(extra_vars)
    # trap here all the exceptions, there may be some more
    except (yaml.scanner.ScannerError, ):
        msg = 'Provided extra-vars are not valid: {0}'.format(extra_vars)
        raise BadKarma(msg)


def kick(template_id, extra_vars):
    """
    Starts a job in ansible tower
    Args:
        template_id (int): id of the template to start
    Returns:
        job_id (int): id of the triggered job

    Note::
        there's no need to pass the configuration as a parameter. We are calling
        the tower-cli command that knows where to get its configuration.
        hint: it's from CONFIG_FILE
    """
    cmd = [which('tower-cli'),
           'job',
           'launch',
           '-e', extra_vars,
           '-J', str(template_id),
           '--format=json']
    tower = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # We can block here, it takes a split of a second to ask ansible tower to
    # start a specific job.
    tower.wait()
    job = json.load(tower.stdout)
    return job['id']


def _get_tower_job_url(job_id, config, output_format):
    """
    Returns the url
    """
    host = config.get('general', 'host')
    return 'https://{0}/api/v1/jobs/{1}/stdout/?format={2}'.format(host,
                                                                   job_id,
                                                                   output_format)


def job_id_status(job_id):
    """
    tower-cli job status 17571
    """
    cmd = [which('tower-cli'),
           'job',
           'status',
           str(job_id),
           '--format=json']
    tower = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # We can block here, it takes a split of a second to ask ansible tower to
    # start a specific job.
    tower.wait()
    try:
        return json.load(tower.stdout)
    except ValueError:
        msg = "Did not find {0} template".format(job_id)
        raise BadKarma(msg)


def _get_job_output(job_id, config, output_format):
    username = config.get('general', 'username')
    password = config.get('general', 'password')
    verify_ssl = True
    if config.has_option('general', 'verify_ssl'):
        verify_ssl = config.getboolean('general', 'verify_ssl')
    job_url = _get_tower_job_url(job_id, config, output_format)
    request = requests.get(job_url, auth=(username, password),
                           verify=verify_ssl, allow_redirects=True, stream=True)
    if not request.status_code == requests.codes.ok:
        msg = "Error getting {0} - return code: {1}".format(job_url,
                                                            request.status_code)
        raise BadKarma(msg)
    return request.text


def monitor(job_id, config, output_format):
    """
    Monitor the execution of job_id.
    it needs a configuration object because we need to authenticate on our
    ansible tower instance (kick_job - do not require authentication because it
    uses the tower-cli script and it can figure out by iself the right
    credentials.
    """

    # we usually don't have valid ssl certificates so we need to verify=False in
    # all the requests calls. Instead of hardcoding, let the configuration
    # decide if we need to verify=True or False.
    # nothing has been printed so far, prev_req is an empty utf-8 string.
    prev_output = u''
    # suppose the job is not complete
    complete = False
    result = None
    while not complete:
        # get the current status from the API point
        output = _get_job_output(job_id, config, output_format)
        # take a nap
        sleep(SLEEP_INTERVAL)
        # we just want to display the lines that have not been printed yet
        display_me = output.replace(prev_output, '')
        # now, for each line in the ouptut
        for line in display_me.split('\n'):
            # if the line is not empty,
            if line:
                # ... just print it
                print(line)
        # now all the new lines have been printed, set prev_req to output
        prev_output = output
        result = job_id_status(job_id)
        complete = result['status'] in ('successful', 'canceled', 'failed')

    # print some other information
    download_url = _get_tower_job_url(job_id, config, 'txt_download')
    print('you can download the full output from: {0}'.format(download_url))
    # check if the job was successful
    result = job_id_status(job_id)
    if result['failed']:
        msg = 'job id {0}: ended with errors'.format(job_id)
        raise BadKarma(msg)


def is_debug_mode():
    return 'DEBUG_MODE' in os.environ


def debug_me():
    cmd = [which('tower-cli'), 'version', ]
    tower = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    tower.wait()
    for line in tower.stdout:
        line = line.strip()
        if line:
            print(line)
    print()
    print('virtualenvironment info:')
    cmd = [which('pip'), 'freeze']
    pip = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    pip.wait()
    for line in pip.stdout:
        line = line.strip()
        if line:
            print(line)


@click.command()
@click.option('--template-name', help='Job template name', required=True)
@click.option('--extra-vars', help='Extra variables', type=str, default='')
def cli_kick(template_name, extra_vars):
    """
    Start an ansible tower job from the command line
    """
    try:
        # verify configuration
        get_config()
        _validate_extra_vars(extra_vars)
        template_id = get_template_id_from_name(template_name)
        job_id = kick(template_id=template_id, extra_vars=extra_vars)
        print('Started job: {0}'.format(job_id))
    except BadKarma as error:
        msg = 'Error kicking job tempate: {0} - {1}'.format(template_name,
                                                            error)
        print(msg)
        sys.exit(1)


@click.command()
@click.option('--job-id', help='Job id to monitor', required=True)
@click.option('--output-format',
              type=click.Choice(['ansi', 'txt']),
              default='ansi',
              help='output format')
def cli_monitor(job_id, output_format):
    """
    Monitor the execution of an ansible tower job
    """
    try:
        # verify configuration
        config = get_config()
        monitor(job_id, config, output_format=output_format)
    except BadKarma as error:
        msg = 'Error monitoring job id: {0} - {1}'.format(job_id, error)
        print(msg)
        sys.exit(1)


@click.command()
@click.option('--template-name', help='Job template name', required=True)
@click.option('--extra-vars', help='Extra variables', type=str, default='')
@click.option('--output-format',
              type=click.Choice(['ansi', 'txt']),
              default='ansi',
              help='output format')
def cli_kick_and_monitor(template_name, extra_vars, output_format):
    """
    Trigger an ansible tower job and monitor its execution.
    In case of error it returns a bad exit code.
    """
    try:
        config = get_config()
        _validate_extra_vars(extra_vars)
        template_id = get_template_id_from_name(template_name)
        job_id = kick(template_id=template_id, extra_vars=extra_vars)
        print('job id: {0}'.format(job_id))
        success = monitor(job_id, config, output_format=output_format)
        if not success:
            sys.exit(1)
    except BadKarma as error:
        print("Execution Error: {0}".format(error))
        sys.exit(1)


if __name__ == '__main__':
    pass
