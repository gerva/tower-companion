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
    def __init__(self, config):
        self.config = config
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
            (str): template id if found

        Raises:
            GuardError
        """
        api = self.api
        try:
            data = api.template_data(template_name)
            return data['results'][0]['id']
        except APIError as error:
            raise GuardError(error)

    def kick(self, template_id, extra_vars):
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
            return self.api.launch_template_id(template_id, extra_vars)
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

    def monitor(self, job_url, output_format, sleep_interval=SLEEP_INTERVAL):
        """
        Monitor the execution of a job stdout endpoint
        Args:
            job_url (str): job url
            output_format (str): text, ansi, ...
            sleep_interval (float): number of seconds between two consecutive
                calls to stdout endpoint
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
                sleep(sleep_interval)
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

    def kick_and_monitor(self, template_name, extra_vars, output_format,
                         sleep_interval=SLEEP_INTERVAL):
        """
        Starts a job and monitors its execution

        Args:
            template_name (str): Name of the template
            extra_vars (list|tuple): extra variables
            output_format (str): output format
        Raises:
            GuardError
        """
        api = self.api
        try:
            template_id = api.template_id(template_name)
            job = self.kick(template_id, extra_vars)
            job_url = self.launch_data_to_url(job)
            self.monitor(job_url, output_format, sleep_interval)
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

    def wait_for_job_to_start(self, job_id, sleep_interval=SLEEP_INTERVAL):
        """
        Ad hoc jobs to not start immediatly, we need to call the api few times
        before the job gets started. This method blocks the execution of monitor
        until the ad hoc command is started.

        Args:
            job_id (AdHoc): ad hoc object
            sleep_interval (float): how long to wait before calling the api
                again and get any new output text
        """
        api = self.api
        started = False
        try:
            while not started:
                sleep(sleep_interval)
                started = api.job_info(job_id) is not None
        except APIError as error:
            raise GuardError(error)

    def ad_hoc_and_monitor(self, ad_hoc, sleep_interval=SLEEP_INTERVAL):
        """
        Starts an ad hoc job and outputs the job output on stdout

        Args:
            ad_hoc (AdHoc): ad hoc object
            sleep_interval (float): how long to wait before calling the api
                again and get any new output text
        Raises:
            GuardError
        """
        try:
            job = self.ad_hoc(ad_hoc)
            job_url = self.launch_data_to_url(job)
            job_id = job['id']
            # wait for job to be started
            self.wait_for_job_to_start(job_id, sleep_interval)
            self.monitor(job_url, output_format='text')
        except APIError as error:
            raise GuardError(error)

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
            raise GuardError(APIError)
