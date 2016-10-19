"""
This module manages the interaction with the remote service. Just ask, we will
do our best to satisfy your request
"""
import os
import yaml

VALID_AD_HOC_MODULES = ('command', 'shell', 'yum', 'apt', 'apt_key',
                        'apt_repository', 'apt_rpm', 'service', 'group',
                        'user', 'mount', 'ping', 'selinux', 'setup',
                        'win_ping', 'win_updates', 'win_group', 'win_user')


def extra_var(var):
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
    if var.startswith('@'):
        # yes, it's a file, let's check this file exists..
        # partition all the way! If you think the next line of code is
        # unreadealbe, you're probably right, but regex won't make it any better
        # Let's delegate the validation of the yml file to tower-cli.
        return os.path.isfile(var.partition('@')[2].strip())

    # extra_vars is not pointing to a file, let's try to load it..
    try:
        yaml.safe_load(var)
    except yaml.YAMLError:
        return False
    return True


def ad_hoc_job_type(job_type):
    """
    Validates an ad hoc job_type

    Args:
        job_type (str): job type

    Returns:
        boolean
    """
    return job_type in ('run', 'Run', 'check', 'Check')


def module_name(name):
    """
    Validates an ad hoc module name

    Args:
        job_type (str): job type

    Returns:
        boolean
    """
    if not name:
        return False
    return name in VALID_AD_HOC_MODULES
