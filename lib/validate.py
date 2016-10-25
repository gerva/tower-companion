"""
This module manages the interaction with the remote service. Just ask, we will
do our best to satisfy your request
"""

VALID_AD_HOC_MODULES = ('command', 'shell', 'yum', 'apt', 'apt_key',
                        'apt_repository', 'apt_rpm', 'service', 'group',
                        'user', 'mount', 'ping', 'selinux', 'setup',
                        'win_ping', 'win_updates', 'win_group', 'win_user')


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
