"""
This module manages the interaction with the remote service. Just ask, we will
do our best to satisfy your request
"""
from __future__ import absolute_import
import copy
import json
import requests
from lib.adhoc import AdHocError
from lib.configuration import ConfigError


class APIError(Exception):
    """
    Error interacting with API
    """
    pass


class APIv1(object):
    """
    APIv1
    """
    # pylint: disable=E1101
    # disables:
    # E: Instance of 'LookupDict' has no 'ok' member (no-member)
    # E: Instance of 'LookupDict' has no 'created' member (no-member)
    def __init__(self, config):
        self.config = config
        try:
            self.host = config.get('host')
        except ConfigError as error:
            msg = "Missing key from configuration, {0}.".format(error)
            msg = "{0} Please check your configuration.".format(msg)
            raise APIError(msg)

        self.api_url = "https://{0}/api/v1".format(self.host)

    def _authentication(self):
        """
        get the authentication from configuration, returns a tuple ready for
        requests calls
        Returns:
            (tuple) username, password
        """
        config = self.config
        try:
            return (config.get('username'), config.get('password'))
        except ConfigError as error:
            msg = "Missing key from configuration, {0}.".format(error)
            msg = "{0} Please check your configuration.".format(msg)
            raise APIError(msg)

    def _verify_ssl(self):
        """
        Gets the value of verify_ssl from the actual configuraion
        """
        config = self.config
        try:
            return config.getboolean('verify_ssl')
        except ConfigError as error:
            msg = "Missing key from configuration, {0}.".format(error)
            msg = "{0} Please check your configuration.".format(msg)
            raise APIError(msg)


    def _get(self, url, params, data):
        auth = self._authentication()
        verify = self._verify_ssl()
        request = requests.get(url, auth=auth, verify=verify, params=params,
                               data=data)
        if request.status_code == requests.codes.ok:
            return request
        else:
            msg = "Failed to get {0} - {1}".format(url, request.reason)
            raise APIError(msg)

    def _post(self, url, params, data):
        auth = self._authentication()
        verify = self._verify_ssl()
        headers = {'Content-type': 'application/json'}
        request = requests.post(url, auth=auth, verify=verify, params=params,
                                data=json.dumps(data), headers=headers)
        if request.status_code in (requests.codes.ok, requests.codes.created):
            return request
        else:
            msg = "Failed to post {0} - {1}".format(url, request.reason)
            raise APIError(msg)

    def _get_json(self, url, params, data=None):
        """
        Gets a remote json from url

        Args:
            url (str): url to query
            parms (dict): url encoded paramters
            data (dict): any data to pass as request body

        Returns:
            (json object): response from remote service

        Raises:
            APIError
        """
        params['format'] = 'json'
        request = self._get(url, params=params, data=data)
        try:
            return json.loads(request.text)
        except ValueError as error:
            msg = "Failed to get {0} - {1}".format(url, error)
            raise APIError(msg)

    def job_info(self, job_id):
        """
        returns a lot of data (json format) about job_is

        Args:
            job_id (str): job_id

        Returns:
            (json object): response from remote service

        Raises:
            APIError
        """
        url = "{0}/unified_jobs/".format(self.api_url)
        params = {'id': job_id}
        request = self._get_json(url, params=params)
        return request

    def _get_id(self, name, endpoint):
        result = self._get_data(name=name, endpoint=endpoint)
        count = result['count']
        if result['count'] == 1:
            return result['results'][0]['id']

        # no results or too many results are returned by the previous call
        msg = 'Could not find any id related to "{0}"'.format(name)
        if count > 0:
            msg = 'Multiple id related to "{0}"'.format(name)
        raise APIError(msg)

    def _get_data(self, name, endpoint):
        """
        Returns a json object with data about name

        Args:
            name (str): name of the template

        Returns:
            (json object)

        Raises:
            APIError
        """
        url = "{0}/{1}/".format(self.api_url, endpoint)
        params = {'name': name}
        return self._get_json(url, params=params)

    def template_data(self, name):
        """
        Returns a json object with data about name

        Args:
            name (str): name of the template

        Returns:
            (json object)

        Raises:
            APIError
        """
        return self._get_data(name=name, endpoint='job_templates')

    def template_id(self, name):
        """
        Returns a template id from a name

        Args:
            name (str): name of the template

        Returns:
            (str): id of the template name

        Raises:
            APIError
        """
        return self._get_id(name=name, endpoint='job_templates')

    def launch_template_id(self, template_id, extra_vars):
        """
        Launch a template job

        Params:
            tempate_id (str): tempate_id
            extra_vars (list): a list of extra variables

        Returns:
            (str): id of the started job

        Raises:
            APIError
        """
        url = "{0}/job_templates/{1}/launch/".format(self.api_url,
                                                     template_id)
        extra_vars = {'extra_vars': extra_vars}
        request = self._post(url, params={}, data=extra_vars)
        return json.loads(request.text)

    def adhoc_to_api(self, adhoc):
        """
        transforms human ad hoc request (names) to api (ids)
        returns a data in a format that is usable by _post() requests

        Args:
            adhoc (AdHoc):
        Returns
            dict: data ready to be used in api calls
        Raises:
           APIError
        """
        data = copy.deepcopy(adhoc)
        try:
            int(data.inventory_id)
        except ValueError:
            data.inventory_id = self.inventory_id(data.inventory_id)

        try:
            int(data.credential_id)
        except ValueError:
            data.credential_id = self.credential_id(data.credential_id)
        try:
            return data.data()
        except AdHocError as error:
            raise APIError(error)

    def launch_ad_hoc(self, ad_hoc):
        """
        Launch an ad hoc job

        Args:
            ad_hoc (AdHoc): your ad hoc command

        Raises:
            APIError
        """
        # adhoc can be either in human (names) or api format (ids)
        try:
            ad_hoc.is_valid()
        except AdHocError as error:
            raise APIError(error)
        data = self.adhoc_to_api(ad_hoc)
        url = "{0}/ad_hoc_commands/".format(self.api_url)
        return self._post(url=url, params=[], data=data)

    def launch_data_to_url(self, data):
        """
        Gets the job url from a job that has been just triggered

        Args:
            data (json): data as returned by any launch_* jobs
        Returns:
            (str): url of the launched job
        """
        return "https://{0}/{1}".format(self.host, data['url'])

    def job_stdout(self, url, output_format):
        """
        Get the current job stdout

        Args:
            url (str): a stdout url
            output_format (str): can be text, ansi
        Returns:
            (str): output of the job
        Raises:
            APIError
        """
        url = "{0}/stdout".format(url)
        params = {'format': output_format}
        result = self._get(url, params=params, data={})
        return result.text

    def job_status(self, job_url):
        """
        Returns the job status string from the job_url
        Args:
            job_url (str): job url
        Returns:
            (bool): job running status
        """
        result = self._get_json(job_url, params={}, data={})
        return result['status']

    def job_finished(self, job_url):
        """
        Returns True if the job is not running anymore. This method do not care
        about the final state, it just reports that the excution is complete.

        Args:
            job_url (str): job url
        Returns:
            (bool): job running complete
        """
        return self.job_status(job_url) in ('successful', 'canceled', 'failed')

    def job_started(self, job_url):
        """
        Returns True if the job is started

        Args:
            job_url (str): job url
        Returns:
            (bool): job running complete
        """
        result = self._get_json(job_url, params={}, data={})
        return result['started'] is not None

    def inventory_data(self, name):
        """
        Returns the inventory id of a given name

        Args:
            name (str): name of the inventory

        Returns:
            (str): id of the inventory

        Raises:
            APIError
        """
        return self._get_data(name=name, endpoint='inventories')

    def inventory_id(self, name):
        """
        Returns the inventory id of a given name

        Args:
            name (str): name of the inventory

        Returns:
            (str): id of the inventory
        """
        return self._get_id(name=name, endpoint='inventories')

    def credentials_data(self, name):
        """
        Returns the inventory id of a given name

        Args:
            name (str): name of the inventory

        Returns:
            (str): id of the inventory

        Raises:
            APIError
        """
        return self._get_data(name=name, endpoint='credentials')

    def credential_id(self, name):
        """
        Returns the inventory id of a given name

        Args:
            name (str): name of the inventory

        Returns:
            (str): id of the inventory
        """
        return self._get_id(name=name, endpoint='credentials')

    def job_url(self, job_id):
        """
        Returns a job url from a job_id

        Args:
            job_id (int|str): job id
        Returns:
            job_url (str)
        """
        url = self.job_info(job_id)['results'][0]['url']
        return "https://{0}/{1}".format(self.host, url)
