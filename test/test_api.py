from __future__ import print_function
import os
import json
import pytest
from lib.adhoc import AdHoc, AdHocError
from lib.api import APIv1, APIError
from lib.configuration import Config


USERNAME = 'my_username'
PASSWORD = 'secret_password'
HOST = 'example.com'

CURRENT_FILE = __file__
CURRENT_DIR = os.path.abspath(os.path.dirname(CURRENT_FILE))


class MockRequest(object):
    def __init__(self, *args, **kwargs):
        self.status_code = None
        self.text = None
        self.json = None


def basic_api():
    config = Config(None)
    config.update('username', USERNAME)
    config.update('password', PASSWORD)
    config.update('host', HOST)
    config.update('verify_ssl', "True")
    return APIv1(config)


def test_api():
    api = basic_api()
    assert api._authentication() == (USERNAME, PASSWORD)


def test_verify_ssl():
    api = basic_api()
    # test for any possible valid value of verify_ssl
    api.config.update('verify_ssl', 'True')
    assert api._verify_ssl() == True

    api.config.update('verify_ssl', 'true')
    assert api._verify_ssl() == True

    api.config.update('verify_ssl', 'yes')
    assert api._verify_ssl() == True

    api.config.update('verify_ssl', 'False')
    assert api._verify_ssl() == False

    api.config.update('verify_ssl', 'false')
    assert api._verify_ssl() == False

    api.config.update('verify_ssl', 'no')
    assert api._verify_ssl() == False


def test_get(monkeypatch):
    api = basic_api()

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.status_code = 200
        return mock

    monkeypatch.setattr('requests.get', mockreturn)
    api._get(url='', params='', data='')


def test_get_error(monkeypatch):
    api = basic_api()

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.status_code = 'test'
        mock.reason = 'test'
        return mock

    monkeypatch.setattr('requests.get', mockreturn)
    with pytest.raises(APIError):
        api._get(url='', params='', data='')


def test_post(monkeypatch):
    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.status_code = 200
        return mock

    monkeypatch.setattr('requests.post', mockreturn)
    api = basic_api()
    api._post(url='', params={}, data={})


def test_post_error(monkeypatch):
    api = basic_api()

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.status_code = 'test'
        mock.reason = 'test'
        return mock

    monkeypatch.setattr('requests.post', mockreturn)
    with pytest.raises(APIError):
        api._post(url='', params='', data='')


def test_get_json(monkeypatch):
    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = '{"id": "123"}'
        mock.reason = 'test'
        mock.status_code = 200
        return mock

    monkeypatch.setattr('requests.get', mockreturn)
    api = basic_api()
    api._get_json(url='', params={}, data=None)


def test_get_json_error(monkeypatch):
    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = '{"id": "123" -BROKEN" json}'
        mock.reason = 'test'
        mock.status_code = 200
        return mock

    monkeypatch.setattr('requests.get', mockreturn)
    api = basic_api()
    with pytest.raises(APIError):
        api._get_json(url='', params={}, data={})

def test_less_configuration():
    config = Config(None)
    with pytest.raises(APIError):
        api = APIv1(config)

    config.update('host', HOST)
    api = APIv1(config)
    with pytest.raises(APIError):
        api._authentication()

    config.update('username', USERNAME)
    api = APIv1(config)
    with pytest.raises(APIError):
        api._authentication()

    config.update('password', PASSWORD)
    api = APIv1(config)
    with pytest.raises(APIError):
        api._verify_ssl()

def test_job_params(monkeypatch):
    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = '{"id": "123"}'
        mock.reason = 'test'
        mock.status_code = 200
        return mock

    monkeypatch.setattr('requests.get', mockreturn)
    api = basic_api()
    api.job_info(job_id='1')
    api.job_info(job_id=1)


def test_get_ids(monkeypatch):
    expected_id = "123"
    count = 1
    fake_text = json.dumps({'results': [{'id': expected_id}], 'count': count})

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = fake_text
        mock.status_code = 200
        return mock

    monkeypatch.setattr('requests.get', mockreturn)
    api = basic_api()
    assert api.inventory_id(name='') == expected_id
    assert api.credential_id(name='') == expected_id


def test_get_ids_zero_results(monkeypatch):
    api = basic_api()
    expected_id = "123"
    for count in (0, 123):
        fake_text = json.dumps({'results': [{'id': expected_id}],
                                'count': count})

        def mockreturn(*args, **kwargs):
            mock = MockRequest()
            mock.text = fake_text
            mock.status_code = 200
            return mock

        monkeypatch.setattr('requests.get', mockreturn)
        with pytest.raises(APIError):
            api.inventory_id(name='')

        with pytest.raises(APIError):
            api.credential_id(name='')


def test_launch_template_id(monkeypatch):
    expected_id = 123
    fake_text = json.dumps({'results': [{'id': expected_id}]})

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = fake_text
        mock.status_code = 200
        return mock

    def mockerror(*args, **kwargs):
        raise APIError

    api = basic_api()
    monkeypatch.setattr('requests.post', mockreturn)
    api = basic_api()
    result = api.launch_template_id(template_id='', extra_vars=['version=123',])
    assert result == json.loads(fake_text)

    result = api.launch_template_id(template_id='', extra_vars='')
    assert result == json.loads(fake_text)

    monkeypatch.setattr('requests.post', mockerror)
    with pytest.raises(APIError):
        api.launch_template_id(template_id='', extra_vars='')


def test_update_project_id(monkeypatch):
    expected_id = 123
    fake_text = json.dumps({'results': [{'id': expected_id}]})

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = fake_text
        mock.status_code = 200
        return mock

    def mockerror(*args, **kwargs):
        raise APIError

    api = basic_api()
    monkeypatch.setattr('requests.post', mockreturn)
    api = basic_api()
    result = api.update_project_id(project_id='')
    assert result == json.loads(fake_text)

    monkeypatch.setattr('requests.post', mockerror)
    with pytest.raises(APIError):
        api.update_project_id(project_id='')

def test_launch_data_to_url():
    api = basic_api()
    url = '123'
    data = {'url': url}
    assert url in api.launch_data_to_url(data)


def test_job_stdout(monkeypatch):
    text = 'some serious ansible stuff is running, hold on'

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = text
        mock.status_code = 200
        return mock

    api = basic_api()
    monkeypatch.setattr('requests.get', mockreturn)
    assert text in api.job_stdout(url='', output_format='')


def test_job_status(monkeypatch):
    status = 'my fancy test'
    text = json.dumps({'status': status})

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = text
        mock.status_code = 200
        return mock
    api = basic_api()
    monkeypatch.setattr('requests.get', mockreturn)
    assert api.job_status(job_url='') == status


def test_job_finished(monkeypatch):
    for status in ('successful', 'canceled', 'failed'):
        text = json.dumps({'status': status})

        def mockreturn(*args, **kwargs):
            mock = MockRequest()
            mock.text = text
            mock.status_code = 200
            return mock
        api = basic_api()
        monkeypatch.setattr('requests.get', mockreturn)
        assert api.job_finished(job_url='') == True

    for status in ('error', 'still running', 'failed-'):
        text = json.dumps({'status': status})

        def mockreturn(*args, **kwargs):
            mock = MockRequest()
            mock.text = text
            mock.status_code = 200
            return mock
        api = basic_api()
        monkeypatch.setattr('requests.get', mockreturn)
        assert api.job_finished(job_url='') == False


def test_job_started(monkeypatch):

    api = basic_api()
    text = json.dumps({'started': None})

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = text
        mock.status_code = 200
        return mock

    monkeypatch.setattr('requests.get', mockreturn)
    assert api.job_started(job_url='') == False

    text = json.dumps({'started': '2016-01-01'})

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = text
        mock.status_code = 200
        return mock
    assert api.job_started(job_url='') == True


def test_get_data(monkeypatch):
    api = basic_api()
    expected_id = "123"
    fake_text = json.dumps({'results': [{'id': expected_id}]})

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = fake_text
        mock.status_code = 200
        return mock

    monkeypatch.setattr('requests.get', mockreturn)
    assert api.template_data(name='') == json.loads(fake_text)
    assert api.project_data(name='') == json.loads(fake_text)
    assert api.inventory_data(name='') == json.loads(fake_text)
    assert api.credentials_data(name='') == json.loads(fake_text)


def test_ad_hoc_to_api(monkeypatch):
    api = basic_api()
    # standard call
    ad_hoc = AdHoc()
    ad_hoc.module_name = 'command'
    ad_hoc.inventory_id = 1
    ad_hoc.credential_id = 2
    ad_hoc.extra_vars = []
    ad_hoc.job_type = 'run'
    data = api.adhoc_to_api(ad_hoc)
    assert data['inventory'] == ad_hoc.inventory_id
    assert data['credential'] == ad_hoc.credential_id

    def mockreturn(*args, **kwargs):
        raise AdHocError

    monkeypatch.setattr('lib.adhoc.AdHoc.data', mockreturn)
    with pytest.raises(APIError):
        api.adhoc_to_api(ad_hoc)


def test_launch_ad_hoc_job(monkeypatch):
    api = basic_api()
    expected_id = 123
    fake_text = json.dumps({'results': [{'id': expected_id}]})

    def mockreturn(*args, **kwargs):
        mock = MockRequest()
        mock.text = fake_text
        mock.status_code = 200
        return mock

    def mockerror(*args, **kwargs):
        raise APIError

    def mock_get_id(*args, **kwargs):
        return expected_id

    api = basic_api()
    monkeypatch.setattr('requests.post', mockreturn)
    monkeypatch.setattr('requests.get', mockreturn)
    monkeypatch.setattr('lib.api.APIv1._get_id', mock_get_id)

    # standard call
    ad_hoc = AdHoc()
    ad_hoc.module_name = 'command'
    ad_hoc.inventory_id = ''
    ad_hoc.credential_id = ''
    ad_hoc.extra_vars = []
    ad_hoc.job_type = 'run'
    api.launch_ad_hoc(ad_hoc)

    # post fails
    monkeypatch.setattr('requests.post', mockerror)
    with pytest.raises(APIError):
        api.launch_ad_hoc(ad_hoc)

    # wrong module name
    monkeypatch.setattr('requests.post', mockreturn)
    monkeypatch.setattr('lib.validate.module_name', mockerror)
    with pytest.raises(APIError):
        api.launch_ad_hoc(ad_hoc)


def test_job_url(monkeypatch):

    expected_url = 'my fancy url'

    def mockreturn(*args, **kwargs):
        return {'results': [{'url': expected_url}]}

    api = basic_api()
    monkeypatch.setattr('lib.api.APIv1.job_info', mockreturn)
    assert expected_url in api.job_url(job_id='')
