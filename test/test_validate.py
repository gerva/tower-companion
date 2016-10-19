from __future__ import print_function
import yaml
import lib.validate as validate


def test_extra_var(monkeypatch):
    extra_var = '@this_does_not_exist'
    assert validate.extra_var(extra_var) == False

    extra_var = '@{0}'.format(__file__)
    assert validate.extra_var(extra_var) == True

    extra_var = 'version=123 tasks:,:{}'
    assert validate.extra_var(extra_var) == True

    def mockreturn(*args, **kwargs):
        raise yaml.YAMLError

    monkeypatch.setattr('yaml.safe_load', mockreturn)
    assert validate.extra_var(extra_var) == False


def test_job_name():
    for job in ('run', 'Run', 'check', 'Check'):
        assert validate.ad_hoc_job_type(job) == True

    for job in (' run', 'RUN', None, '{}'):
        assert validate.ad_hoc_job_type(job) == False


def test_module_name():
    assert validate.module_name('command') == True
    assert validate.module_name(' command') == False
