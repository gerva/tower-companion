"""
Start and monitor ansilbe tower jobs from the command line, in real time.
Grab your pop corns.
"""
from __future__ import print_function, absolute_import
import os
import sys
import click
import yaml
from .configuration import Config
from .tc import Guard, GuardError
from .adhoc import AdHoc

# default tower-cli configuration file
DEFAULT_CONFIGURATION = os.path.expanduser('~/.tower_cli.cfg')


class CLIError(Exception):
    """
    There's something wrong with this command...
    """
    pass


def config_file():
    """
    Returns the path to the configuration file.
    If TC_CONFIG in the environment, it uses if.
    If TC_CONFIG is not defined, it uses tower-cli DEFAULT_CONFIGURATION
    """
    if 'TC_CONFIG' in os.environ:
        return os.environ['TC_CONFIG']
    else:
        return DEFAULT_CONFIGURATION


def extra_var_to_dict(extra_var):
    """
    Extra variable parser.
    Takes extra_var and returns a dictionary

    1. if the extra_var points to a file, read the file and send the content
    to the yaml parser

    2. if extra_var is a string, send it to the yaml parser

    3. return parsed file/string as a dictionary

    In case of error (yaml load does not return a dictionary) , raise a CLIError

    Args:
        extra_var (str): extra var as received from the command line
    Returns:
        (dict)
    Raise:
        CLIError
    """
    value = {}
    if extra_var.startswith('@'):
        filename = extra_var.partition('@')[2]
        if not os.path.isfile(filename):
            msg = '{0} does not exist'.format(filename)
            raise CLIError(msg)
        with open(filename, 'r') as var_in:
            value = yaml.load(var_in)
    else:
        value = yaml.load(extra_var)

    if not isinstance(value, dict):
        raise CLIError('Failed to validate extra var: {0}'.format(extra_var))

    return value


@click.command()
@click.option('--template-name', help='Job template name', required=True)
@click.option('--extra-vars', help='Extra variables', type=str, default='',
              multiple=True)
def cli_kick(template_name, extra_vars):
    """
    Start an ansible tower job from the command line
    """
    try:
        # verify configuration
        config = Config(config_file())
        guard = Guard(config)
        template_id = guard.get_template_id(template_name)
        extra_v = {}
        for extra_var in extra_vars:
            extra_v.update(extra_var_to_dict(extra_var))
        job = guard.kick(template_id=template_id, extra_vars=extra_v)
        job_url = guard.launch_data_to_url(job)
        print('Started job: {0}'.format(job_url))
    except CLIError as error:
        print(error)
        sys.exit(1)
    except GuardError as error:
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
        config = Config(config_file())
        guard = Guard(config)
        guard.monitor(job_url=guard.job_url(job_id),
                      output_format=output_format,
                      sleep_interval=1.0)
    except GuardError as error:
        msg = 'Error monitoring job id: {0} - {1}'.format(job_id, error)
        print(msg)
        sys.exit(1)


@click.command()
@click.option('--template-name', help='Job template name', required=True)
@click.option('--extra-vars', help='Extra variables', type=str, default='',
              multiple=True)
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
        config = Config(config_file())
        guard = Guard(config)
        extra_v = {}
        for extra_var in extra_vars:
            extra_v.update(extra_var_to_dict(extra_var))
        guard.kick_and_monitor(template_name=template_name,
                               extra_vars=extra_v,
                               output_format=output_format,
                               sleep_interval=1.0)
    except CLIError as error:
        print(error)
        sys.exit(1)
    except GuardError as error:
        print("Execution Error: {0}".format(error))
        sys.exit(1)


@click.command()
@click.option('--inventory', help='Inventory to run on', required=True)
@click.option('--machine-credential', help='SSH credentials name',
              required=True)
@click.option('--module-name', help='Ansible module to run', required=True)
@click.option('--job-type', type=click.Choice(['run', 'check']),
              help='Type of job so execute', default='run')
@click.option('--module-args', help='Arguments for the selected module',
              type=str, default='')
@click.option('--limit', help='Limit to hosts', type=str, default='')
@click.option('--job-explanation', help='Job description', type=str, default='')
@click.option('--become', help='Become root', is_flag=True)
@click.option('--output-format',
              type=click.Choice(['ansi', 'txt']),
              default='ansi',
              help='output format')
def cli_ad_hoc_and_monitor(inventory, machine_credential, module_name,
                           module_args, job_type, limit, job_explanation,
                           become, output_format):
    """
    Trigger an ansible tower ad hoc job and monitor its execution.
    In case of error it returns a bad exit code.
    """
    try:
        adhoc = AdHoc()
        adhoc.inventory_id = inventory
        adhoc.credential_id = machine_credential
        adhoc.module_name = module_name
        adhoc.module_args = module_args
        adhoc.job_type = job_type
        adhoc.limit = limit
        adhoc.job_explanation = job_explanation
        adhoc.become = become
        # extra vars are not passed from the command line, extend this in a
        # future version
        adhoc.extra_vars = []
        config = Config(config_file())
        guard = Guard(config)
        guard.ad_hoc_and_monitor(adhoc, output_format=output_format,
                                 sleep_interval=1.0)
    except GuardError as error:
        print("Execution Error: {0}".format(error))
        sys.exit(1)


@click.command()
@click.option('--inventory', help='Inventory to run on', required=True)
@click.option('--machine-credential', help='SSH credentials name', required=True)
@click.option('--module-name', help='Ansible module to run', required=True)
@click.option('--job-type', type=click.Choice(['run', 'check']),
              help='Type of job so execute', default='run')
@click.option('--module-args', help='Arguments for the selected module', type=str, default='')
@click.option('--limit', help='Limit to hosts', type=str, default='')
@click.option('--job-explanation', help='Job description', type=str, default='')
@click.option('--verbose', help='Verbose mode', is_flag=True)
@click.option('--become', help='Become root', is_flag=True)
def cli_ad_hoc(inventory, machine_credential, module_name, job_type,
               module_args, limit, job_explanation, verbose, become):
    """
    Trigger an ansible tower ad hoc job and monitor its execution.
    In case of error it returns a bad exit code.
    """
    try:
        adhoc = AdHoc()
        adhoc.inventory_id = inventory
        adhoc.credential_id = machine_credential
        adhoc.module_name = module_name
        adhoc.module_args = module_args
        adhoc.job_type = job_type
        adhoc.limit = limit
        adhoc.job_explanation = job_explanation
        adhoc.become = become
        # extra vars are not passed from the command line, extend this in a
        # future version
        adhoc.extra_vars = []
        config = Config(config_file())
        guard = Guard(config)
        result = guard.ad_hoc(adhoc)
        print('job url: {0}'.format(guard.job_url(result['id'])))
    except GuardError as error:
        print("Execution Error: {0}".format(error))
        sys.exit(1)
