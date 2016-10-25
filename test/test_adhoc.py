import pytest
from lib.adhoc import AdHoc, AdHocError


def mockreturn(*args, **kwargs):
    return True


def mockerror(*args, **kwargs):
    return False


def test_to_data(monkeypatch):

    adhoc = AdHoc()
    monkeypatch.setattr('lib.adhoc.AdHoc.is_valid', mockreturn)

    data = adhoc.data()
    for key in ('inventory', 'credential', 'module_name',
                'module_args', 'become_enabled',
                'limit', 'job_type', 'job_explanation'):
        assert key in data


def test_bad_module_name(monkeypatch):
    adhoc = AdHoc()
    with pytest.raises(AdHocError):
        adhoc.is_valid()


def test_bad_job_type(monkeypatch):
    adhoc = AdHoc()
    monkeypatch.setattr('lib.validate.module_name', mockreturn)
    monkeypatch.setattr('lib.validate.ad_hoc_job_type', mockerror)
    with pytest.raises(AdHocError):
        adhoc.is_valid()


def test_ids(monkeypatch):
    adhoc = AdHoc()
    adhoc.extra_vars = []
    monkeypatch.setattr('lib.validate.module_name', mockreturn)
    monkeypatch.setattr('lib.validate.ad_hoc_job_type', mockreturn)
    with pytest.raises(AdHocError):
        adhoc.is_valid()

    adhoc.inventory_id = ''
    with pytest.raises(AdHocError):
        adhoc.is_valid()
