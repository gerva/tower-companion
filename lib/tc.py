#!/usr/bin/env python
"""
Start and monitor ansilbe tower jobs from the command line, in real time.
Grab your pop corns.
"""
from __future__ import print_function, absolute_import
import json
from time import sleep
from .api import APIv1, APIError

# some constants
SLEEP_INTERVAL = 1.0  # sleep interval


class GuardError(Exception):
    """
    Generic Guard Error
    """
    pass


class Guard(object):
    """
    Your belowed tower house keeper. It just need a configuration object
    and it will do all the dirty job for you.
    """
    def __init__(self, config, sleep_interval=SLEEP_INTERVAL):
        self.config = config
        self.sleep_interval = sleep_interval
        try:
            self.api = APIv1(config)
        except APIError as error:
            raise GuardError(error)

    def get_template_id(self, template_name):
        """
        Returns a template id from a template name
        Args:
            template_name (str): the name of template

        Retruns:
            (int): template id if found

        Raises:
            GuardError
        """
        api = self.api
        try:
            data = api.template_data(template_name)
            return data['results'][0]['id']
        except APIError as error:
            raise GuardError(error)

    def get_role_id(self, template_name, permission):
        """
        Returns a role id from a template permission combination
        Args:
            template_id (int): the id of the template
            permission (str): permission for the role

        Retruns:
            (int): role id if found

        Raises:
            GuardError
        """
        api = self.api
        try:
            data = api.role_data()
            # now iterate through all roles and search for the right combination of template id and permission
            for role in data['results']:
                role_type = role['name'].lower()
                resource_type = role['summary_fields'].get('resource_type')
                resource_name = role['summary_fields'].get('resource_name')
                if ((resource_type) and
                    (resource_name) and
                    (role_type.lower() == permission.lower()) and
                    (resource_type.lower() == 'job template') and
                    (resource_name.lower() == template_name.lower())):
                    return role['id']
            # if we are here, we didnt find any suitable role
            msg = "No role found for template '{0}' ".format(template_name)
            msg = "{0}with permissions {1}. ".format(msg, permission)
            msg = "{0}Please make sure that a suitable role exists".format(msg)
            raise GuardError(msg)
        except APIError as error:
            raise GuardError(error)

    def get_user_id(self, username):
        """
        Returns a user id from a username
        Args:
            username (str): the name of the user

        Retruns:
            (int): user id if found

        Raises:
            GuardError
        """
        api = self.api
        try:
            data = api.user_data(username)
            if data['count'] == 0:
                msg = "No user '{0}' found".format(username)
                raise GuardError(msg)
            return data['results'][0]['id']
        except APIError as error:
            raise GuardError(error)

    def get_project_id(self, project_name):
        """
        Returns a project id from a project name
        Args:
            project_name (str): the name of project

        Retruns:
            (str): project id if found

        Raises:
            GuardError
        """
        api = self.api
        try:
            data = api.project_data(project_name)
            return data['results'][0]['id']
        except (IndexError, KeyError):
            raise GuardError('no such project')
        except APIError as error:
            raise GuardError(error)

    def update_project(self, project_id):
        """
        Updateds a project in ansible tower
        Args:
            project_id (int): id of the project to update
        Returns:
            job_id (int): id of the triggered job
        Raises:
            GuardError
        """
        try:
            return self.api.update_project_id(project_id)
        except APIError as error:
            raise GuardError(error)

    def kick(self, template_id, extra_vars, limit):
        """
        Starts a job in ansible tower
        Args:
            template_id (int): id of the template to start
        Returns:
            job_id (int): id of the triggered job
        Raises:
            GuardError
        """
        try:
            return self.api.launch_template_id(template_id, extra_vars, limit)
        except APIError as error:
            raise GuardError(error)

    def download_url(self, job_id, output_format):
        """
        Returns the url
        """
        host = self.config.get('host')
        return 'https://{0}/api/v1/jobs/{1}/stdout/?format={2}'.format(
            host, job_id, output_format)

    def ad_hoc_url(self, job_id, output_format):
        """
        Returns the url
        """
        host = self.config.get('host')
        return 'https://{0}/api/v1/ad_hoc_commands/{1}/stdout/?format={2}'.format(
            host, job_id, output_format)

    def monitor(self, job_url, output_format):
        """
        Monitor the execution of a job stdout endpoint
        Args:
            job_url (str): job url
            output_format (str): text, ansi, ...
        Raises:
            GuardError
        """
        # a good old empty string
        prev_output = u''
        # suppose the job is not complete
        result = None
        complete = False
        api = self.api
        try:
            while not complete:
                complete = api.job_finished(job_url)
                # get the current status from the API point
                output = api.job_stdout(job_url, output_format)
                # take a nap
                sleep(self.sleep_interval)
                # we just want to display the lines that have not been printed
                # yet
                print_me = output.replace(prev_output, '').strip()
                # do not print empty lines
                if print_me:
                    print(print_me)
                # now all the new lines have been printed, set prev_req to output
                prev_output = output
            result = api.job_status(job_url)
        except APIError as error:
            raise GuardError(error)

        # print some other information
        # download_url = self.download_url(job_id, 'txt_download')
        # print('you can download the full output from: {0}'.format(download_url))
        # check if the job was successful
        if result == 'failed':
            msg = 'job id {0}: ended with errors'.format(job_url)
            raise GuardError(msg)

    def kick_and_monitor(self, template_name, extra_vars, limit, output_format):
        """
        Starts a job and monitors its execution

        Args:
            template_name (str): Name of the template
            extra_vars (list|tuple): extra variables
            output_format (str): output format
            limit (str): limit to the following hosts
        Raises:
            GuardError
        """
        try:
            template_id = self.get_template_id(template_name)
            job = self.kick(template_id, extra_vars, limit)
            job_url = self.launch_data_to_url(job)
            self.monitor(job_url, output_format)
        except APIError as error:
            raise GuardError(error)

    def launch_data_to_url(self, job_data):
        """
        Did you just execute a job? pass the json file you just got back from
        the api to this method and get its url

        Args:
            job_data (dict): whatever a kick job returned to you

        Returns:
            url (str): url of the job

        Raises:
            GuardError
        """
        api = self.api
        try:
            return api.launch_data_to_url(job_data)
        except APIError as error:
            raise GuardError(error)

    def user_role(self, user_id, role_id):
        """
        Adds a role to a user in ansible tower

        Args:
            user_id (int): id of the user which should be granted permissions
            role_id (int): id of the role to set for this user

        Returns:
            job_id (int): id of the triggered job
        """
        api = self.api
        try:
            return api.update_user_role(user_id, role_id)
        except APIError as error:
            raise GuardError(error)

    def ad_hoc(self, ad_hoc):
        """
        Starts a ad hoc job in ansible tower
        Args:
            ad_hoc (AdHoc): Inventory to run on
        Returns:
            job_id (int): id of the triggered job
        """
        api = self.api
        try:
            result = api.launch_ad_hoc(ad_hoc)
            return json.loads(result.text)
        except APIError as error:
            raise GuardError(error)

    def wait_for_job_to_start(self, job_id):
        """
        Ad hoc jobs to not start immediatly, we need to call the api few times
        before the job gets started. This method blocks the execution of monitor
        until the ad hoc command is started.

        Args:
            job_id (AdHoc): ad hoc object
        """
        api = self.api
        started = False
        try:
            job_url = api.job_url(job_id)
            while not started:
                sleep(self.sleep_interval)
                started = api.job_started(job_url)
        except APIError as error:
            raise GuardError(error)

    def ad_hoc_and_monitor(self, ad_hoc, output_format):
        """
        Starts an ad hoc job and outputs the job output on stdout

        Args:
            ad_hoc (AdHoc): ad hoc object
            output_format (str): output format, it can be ansi or txt
        Raises:
            GuardError
        """
        job = self.ad_hoc(ad_hoc)
        job_url = self.launch_data_to_url(job)
        job_id = job['id']
        # wait for job to be started
        self.wait_for_job_to_start(job_id)
        self.monitor(job_url, output_format=output_format)

    def job_url(self, job_id):
        """
        transforms a job id into a job_url, using fireworks and some magic
        tricks. Do not try this at home!

        Args:
            job_id (int|str): job id

        Returns:
            (str): url of the job

        Raises:
            GuardError
        """
        api = self.api
        try:
            return api.job_url(job_id)
        except APIError as error:
            raise GuardError(error)
