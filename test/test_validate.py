from __future__ import print_function
import yaml
import lib.validate as validate


def test_job_name():
    for job in ('run', 'Run', 'check', 'Check'):
        assert validate.ad_hoc_job_type(job) == True

    for job in (' run', 'RUN', None, '{}'):
        assert validate.ad_hoc_job_type(job) == False


def test_module_name():
    assert validate.module_name('command') == True
    assert validate.module_name(' command') == False
