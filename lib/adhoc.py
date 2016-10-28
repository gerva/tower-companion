"""
This module manages the interaction with the remote service. Just ask, we will
do our best to satisfy your request
"""
from __future__ import absolute_import
import lib.validate as validate


class AdHocError(Exception):
    """
    Your ad hoc command does not look great
    """
    pass


class AdHoc(object):
    """
    AdHoc job
    """
    JOB_TYPE = 'run'
    JOB_EXPLANATION = 'Ad Hoc job run by tower-companion'
    # pylint: disable=too-many-instance-attributes
    # those are the parameters we need to send to the api to kick off an ad hoc
    # job.
    def __init__(self):
        self.inventory_id = None
        self.credential_id = None
        self.module_name = None
        self.module_args = None
        self.become = None
        self.limit = None
        self.job_type = self.JOB_TYPE
        self.job_explanation = self.JOB_EXPLANATION

    def is_valid(self):
        """
        Validates AdHoc

        Raises:
            AdHocError
        """
        self._is_valid_module_name()
        self._is_valid_job_type()

        if self.inventory_id is None:
            raise AdHocError('inventory_id cannot be None')

        if self.credential_id is None:
            raise AdHocError('credential_id cannot be None')

    def _is_valid_module_name(self):
        """
        Checks if provided module name is valid. Valid options, are apt, yum,
        command, shell and many more. A full list of valid options is defined
        in the validate module.

        Raises: AdHocError
        """
        if not validate.module_name(name=self.module_name):
            msg = "{0}: is not a valid module name".format(self.module_name)
            raise AdHocError(msg)

    def _is_valid_job_type(self):
        """
        Checks if provided job type is valid. Valid options are 'run' and
        'check' and their capitalize() versions.

        Raises: AdHocError
        """
        if not validate.ad_hoc_job_type(job_type=self.job_type):
            msg = "{0}: is not a valid job type".format(self.job_type)
            raise AdHocError(msg)

    def data(self):
        """
        Transforms the ad hoc command into a data structure that can be used by
        _get* and _post* calls

        Returns:
            (dict)

        Raises:
            AdHocError
        """
        self.is_valid()
        data = {'inventory': self.inventory_id,
                'credential': self.credential_id,
                'module_name': self.module_name,
                'module_args': self.module_args,
                'become_enabled': self.become,
                'limit': self.limit,
                'job_type': self.job_type,
                'job_explanation': self.job_explanation}

        return data
