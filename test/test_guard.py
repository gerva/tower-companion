from __future__ import absolute_import
import os
import json
import pytest
from lib.api import APIError
from lib.configuration import Config
from lib.adhoc import AdHoc
from lib.tc import Guard, GuardError


USERNAME = 'my_username'
PASSWORD = 'secret_password'
HOST = 'example.com'

CURRENT_DIR = os.path.dirname(__file__)
BASIC_JSON_DATA = {'id': '123'}
BASIC_JSON_FILE = os.path.join(CURRENT_DIR, 'basic.json')


def setup_module(module):
    with open(BASIC_JSON_FILE, 'w') as json_out:
        json.dump(BASIC_JSON_DATA, json_out)


def teardown_module(module):
    for filename in (BASIC_JSON_FILE, ):
        try:
            os.remove(filename)
        except OSError:
            # filename does not exist
            pass


def basic_guard():
    config = Config(None)
    config.update('username', USERNAME)
    config.update('password', PASSWORD)
    config.update('host', HOST)
    config.update('verify_ssl', "True")
    return Guard(config)


class ApiMock(object):
    def __init__(self):
        pass

    def template_name(self):
        return BASIC_JSON_DATA['id']

    def get_template_id(self):
        return json.load(BASIC_JSON_DATA)


class MockRequest(object):
    def __init__(self, *args, **kwargs):
        self.status_code = None
        self.text = None
        self.json = None


def test_guard_bad_configuration(monkeypatch):
    def mockreturn(*args, **kwargs):
        raise APIError
    monkeypatch.setattr('lib.api.APIv1.__init__', mockreturn)
    with pytest.raises(GuardError):
        guard = Guard('')


def test_get_template_id(monkeypatch):
    guard = basic_guard()

    expected_id = '1'
    fake_result = {'results': [{'id': expected_id}]}
    def mockreturn(self, template_name):
        return fake_result
    monkeypatch.setattr('lib.api.APIv1.template_data', mockreturn)
    assert guard.get_template_id('') == expected_id

    def mockreturn(self, template_name):
        raise APIError

    monkeypatch.setattr('lib.api.APIv1.template_data', mockreturn)
    with pytest.raises(GuardError):
        guard.get_template_id(template_name='')


def test_kick(monkeypatch):
    # quite a lot of changes, this test has to be updated
    guard = basic_guard()
    expected_value = 'kick'

    def mockreturn(*args, **kwargs):
        return expected_value

    monkeypatch.setattr('lib.api.APIv1.launch_template_id', mockreturn)

    def mockreturn(*args, **kwargs):
        raise APIError

    monkeypatch.setattr('lib.api.APIv1.launch_template_id', mockreturn)
    with pytest.raises(GuardError):
        guard.kick(template_id='', extra_vars='')


def test_download_url():
    guard = basic_guard()
    job_id = 10
    for output_format in ('json', 'other', 'text'):
        download_url = guard.download_url(job_id=job_id,
                                          output_format=output_format)
        assert str(job_id) in download_url
        assert output_format in download_url


def test_ad_hoc_url():
    guard = basic_guard()
    job_id = 10
    for output_format in ('json', 'other', 'text'):
        download_url = guard.ad_hoc_url(job_id=job_id,
                                        output_format=output_format)
        assert str(job_id) in download_url
        assert output_format in download_url


def test_monitor(monkeypatch):
    output = "an output string\n\nstring\nstring"

    def mock_stdout(self, job_url, output_format):
        return output

    def mock_finished(*args, **kwargs):
        return True

    def mock_status_ok(*args, **kwargs):
        return 'successful'

    def mock_status_failed(*args, **kwargs):
        return 'failed'

    def mockerror(*args, **kwargs):
        raise APIError

    # monkeypatch.setattr('lib.api.SLEEP_INTERVAL', 0.0)
    monkeypatch.setattr('lib.api.APIv1.job_finished', mock_finished)
    monkeypatch.setattr('lib.api.APIv1.job_stdout', mock_stdout)
    monkeypatch.setattr('lib.api.APIv1.job_status', mock_status_ok)

    guard = basic_guard()
    guard.monitor(job_url='', output_format='', sleep_interval=0.0)

    # simulate an error received from the API
    monkeypatch.setattr('lib.api.APIv1.job_finished', mockerror)
    with pytest.raises(GuardError):
        guard.monitor(job_url='', output_format='', sleep_interval=0.0)

    # job finished with errors
    monkeypatch.setattr('lib.api.APIv1.job_finished', mock_finished)
    monkeypatch.setattr('lib.api.APIv1.job_status', mock_status_failed)
    with pytest.raises(GuardError):
        guard.monitor(job_url='', output_format='', sleep_interval=0.0)


def test_kick_and_monitor(monkeypatch):

    guard = basic_guard()

    def mockreturn(*args, **kwargs):
        return ''

    def mockerror(*args, **kwargs):
        raise APIError

    monkeypatch.setattr('lib.tc.Guard.kick', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.monitor', mockreturn)
    monkeypatch.setattr('lib.api.APIv1.template_id', mockreturn)
    monkeypatch.setattr('lib.api.APIv1.launch_data_to_url', mockreturn)

    guard.kick_and_monitor(template_name='', extra_vars=[], output_format='',
                           sleep_interval=0.0)

    monkeypatch.setattr('lib.api.APIv1.template_id', mockerror)
    with pytest.raises(GuardError):
        guard.kick_and_monitor(template_name='', extra_vars=[],
                               output_format='', sleep_interval=0.0)


def test_ad_hoc(monkeypatch):
    def mockreturn(*args, **kwargs):
        return ''

    def mockerror(*args, **kwargs):
        raise APIError

    def mock_ad_hoc_launch(*args, **kwargs):
        mock = MockRequest()
        mock.text = '{"id": "123"}'
        mock.reason = 'test'
        mock.status_code = 200
        return mock

    guard = basic_guard()
    ad_hoc = AdHoc()
    monkeypatch.setattr('lib.api.APIv1.inventory_id', mockerror)
    with pytest.raises(GuardError):
        guard.ad_hoc(ad_hoc)

    monkeypatch.setattr('lib.api.APIv1.inventory_id', mockreturn)
    monkeypatch.setattr('lib.api.APIv1.credential_id', mockreturn)
    monkeypatch.setattr('lib.api.APIv1.launch_ad_hoc', mock_ad_hoc_launch)
    guard.ad_hoc(ad_hoc)


def test_wait_for_job_to_start(monkeypatch):

    def mockreturn(*args, **kwargs):
        return ''

    def mockerror(*args, **kwargs):
        raise APIError

    monkeypatch.setattr('lib.api.APIv1.job_info', mockreturn)
    guard = basic_guard()
    guard.wait_for_job_to_start(job_id='', sleep_interval=0.0)

    monkeypatch.setattr('lib.api.APIv1.job_info', mockerror)
    with pytest.raises(GuardError):
        guard.wait_for_job_to_start(job_id='', sleep_interval=0.0)


def test_ad_hoc_and_monitor(monkeypatch):

    def mockreturn(*args, **kwargs):
        return ''

    def mock_launch(*args, **kwargs):
        return {'id': ''}

    def mock_guard_error(*args, **kwargs):
        raise GuardError

    def mock_api_error(*args, **kwargs):
        raise APIError

    monkeypatch.setattr('lib.tc.Guard.ad_hoc', mock_launch)
    monkeypatch.setattr('lib.tc.Guard.monitor', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.wait_for_job_to_start', mockreturn)
    monkeypatch.setattr('lib.api.APIv1.launch_data_to_url', mockreturn)

    guard = basic_guard()
    ad_hoc = AdHoc()
    ad_hoc.extra_vars = []
    guard.ad_hoc_and_monitor(ad_hoc, sleep_interval=0.0)

    monkeypatch.setattr('lib.tc.Guard.ad_hoc', mock_guard_error)
    with pytest.raises(GuardError):
        guard.ad_hoc_and_monitor(ad_hoc, sleep_interval=0.0)

    monkeypatch.setattr('lib.tc.Guard.ad_hoc', mock_launch)
    monkeypatch.setattr('lib.api.APIv1.launch_data_to_url', mock_api_error)
    with pytest.raises(GuardError):
        guard.ad_hoc_and_monitor(ad_hoc, sleep_interval=0.0)


def test_job_url(monkeypatch):

    expected_value = 'my fancy value'

    def mockerror(*args, **kwargs):
        raise APIError

    def mockreturn(*args, **kwargs):
        return expected_value

    guard = basic_guard()
    monkeypatch.setattr('lib.api.APIv1.job_url', mockreturn)
    assert guard.job_url(job_id='') == expected_value

    monkeypatch.setattr('lib.api.APIv1.job_url', mockerror)
    with pytest.raises(GuardError):
        guard.job_url(job_id='')
