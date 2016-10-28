"""
Testing tower companion CLI
"""
import os
import pytest
from click.testing import CliRunner
from lib.tc import GuardError
from lib.cli import cli_kick, cli_monitor, DEFAULT_CONFIGURATION, config_file
from lib.cli import cli_kick_and_monitor, cli_ad_hoc_and_monitor, cli_ad_hoc
from lib.cli import cli_update_project
from lib.cli import extra_var_to_dict, CLIError


CURRENT_DIR = os.path.dirname(__file__)
TEST_YAML = os.path.join(CURRENT_DIR, 'extra_var.yml')


def mock_config_file(*args, **kwargs):
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, 'configuration.cfg')


def test_extra_var_to_dict():
    extra_var = 'version=1'
    # bad extra var
    with pytest.raises(CLIError):
        extra_var_to_dict(extra_var)

    extra_var = '@notexisitngfile'
    # bad extra var
    with pytest.raises(CLIError):
        extra_var_to_dict(extra_var)

    key = 'version'
    value = '1'
    extra_var = '{0}: {1}'.format(key, value)
    extra_var_file = '@{0}'.format(TEST_YAML)
    for e_var in (extra_var, extra_var_file):
        result = extra_var_to_dict(e_var)
        assert isinstance(result, dict)
        assert key in result
        assert str(result[key]) == value


def test_config_file(monkeypatch):

    monkeypatch.setattr('os.environ', {})
    assert config_file() == DEFAULT_CONFIGURATION

    monkeypatch.setattr('os.environ', {'TC_CONFIG': __file__})
    assert config_file() == __file__


def test_cli_kick(monkeypatch):

    def mockerror(*args, **kwargs):
        raise GuardError

    def mock_cli_error(*args, **kwargs):
        raise CLIError

    def mockreturn(*args, **kwargs):
        return 'just a test'

    monkeypatch.setattr('lib.tc.Guard.get_template_id', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.kick', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.launch_data_to_url', mockreturn)
    monkeypatch.setattr('lib.cli.config_file', mock_config_file)

    runner = CliRunner()
    # clean execution
    result = runner.invoke(cli_kick, ['--template-name', 'test',
                                      '--extra-vars', 'version: 1.0'])
    assert result.exit_code == 0

    monkeypatch.setattr('lib.cli.extra_var_to_dict', mock_cli_error)
    result = runner.invoke(cli_kick, ['--template-name', 'test',
                                      '--extra-vars', 'version: 1.0'])
    assert result.exit_code == 1
    # whooops! error
    monkeypatch.setattr('lib.tc.Guard.get_template_id', mockerror)
    result = runner.invoke(cli_kick, ['--template-name', 'test',
                                      '--extra-vars', 'version: 1.0'])
    assert result.exit_code == 1

def test_cli_update_project(monkeypatch):

    def mockerror(*args, **kwargs):
        raise GuardError

    def mock_cli_error(*args, **kwargs):
        raise CLIError

    def mockreturn(*args, **kwargs):
        return 'just a test'

    monkeypatch.setattr('lib.tc.Guard.get_project_id', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.update_project', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.launch_data_to_url', mockreturn)
    monkeypatch.setattr('lib.cli.config_file', mock_config_file)

    runner = CliRunner()
    # clean execution
    result = runner.invoke(cli_update_project, ['--project-name', 'test'])
    assert result.exit_code == 0

    # whooops! error
    monkeypatch.setattr('lib.tc.Guard.get_project_id', mockerror)
    result = runner.invoke(cli_update_project, ['--project-name', 'test'])
    assert result.exit_code == 1

def test_cli_monitor(monkeypatch):

    def mockerror(*args, **kwargs):
        raise GuardError

    def mockreturn(*args, **kwargs):
        return 'just a test'

    monkeypatch.setattr('lib.tc.Guard.monitor', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.job_url', mockreturn)
    monkeypatch.setattr('lib.cli.config_file', mock_config_file)

    runner = CliRunner()
    # clean execution
    result = runner.invoke(cli_monitor, ['--job-id', '1'])
    assert result.exit_code == 0

    # error!
    monkeypatch.setattr('lib.tc.Guard.monitor', mockerror)
    result = runner.invoke(cli_monitor, ['--job-id', '1'])
    assert result.exit_code == 1


def test_cli_kick_and_monitor(monkeypatch):

    def mockerror(*args, **kwargs):
        raise GuardError

    def mock_cli_error(*args, **kwargs):
        raise CLIError

    def mockreturn(*args, **kwargs):
        return 'just a test'

    monkeypatch.setattr('lib.tc.Guard.kick_and_monitor', mockreturn)
    monkeypatch.setattr('lib.cli.config_file', mock_config_file)

    runner = CliRunner()
    # clean execution
    result = runner.invoke(cli_kick_and_monitor, ['--template-name', 'test'])
    assert result.exit_code == 0

    # error!
    monkeypatch.setattr('lib.tc.Guard.kick_and_monitor', mockerror)
    result = runner.invoke(cli_kick_and_monitor, ['--template-name', 'test'])
    assert result.exit_code == 1

    monkeypatch.setattr('lib.cli.extra_var_to_dict', mock_cli_error)
    result = runner.invoke(cli_kick_and_monitor, ['--template-name', 'test',
                           '--extra-vars', 'version: 1.0'])
    assert result.exit_code == 1


def test_cli_ad_hoc_and_monitor(monkeypatch):

    def mockerror(*args, **kwargs):
        raise GuardError

    def mock_cli_error(*args, **kwargs):
        raise CLIError

    def mockreturn(*args, **kwargs):
        return 'just a test'

    monkeypatch.setattr('lib.tc.Guard.ad_hoc_and_monitor', mockreturn)
    monkeypatch.setattr('lib.cli.config_file', mock_config_file)

    runner = CliRunner()
    args = ['--inventory', 'test',
            '--machine-credential', 'test',
            '--module-name', 'test',
            '--module-args', 'test1 test2', ]
    # clean execution
    result = runner.invoke(cli_ad_hoc_and_monitor, args)
    assert result.exit_code == 0

    # error
    monkeypatch.setattr('lib.tc.Guard.ad_hoc_and_monitor', mockerror)
    result = runner.invoke(cli_ad_hoc_and_monitor, args)
    assert result.exit_code == 1


def test_cli_ad_hoc(monkeypatch):

    def mockerror(*args, **kwargs):
        raise GuardError

    def mockreturn(*args, **kwargs):
        return {'results': [], 'url': 'test', 'id': 'test'}

    def mock_job_url(*args, **kwargs):
        return 'test'

    monkeypatch.setattr('lib.tc.Guard.ad_hoc', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.job_url', mock_job_url)
    monkeypatch.setattr('lib.cli.config_file', mock_config_file)

    runner = CliRunner()
    args = ['--inventory', 'test',
            '--machine-credential', 'test',
            '--module-name', 'test',
            '--module-args', 'test1 test2']
    # clean execution
    result = runner.invoke(cli_ad_hoc, args)
    assert result.exit_code == 0

    # error!
    monkeypatch.setattr('lib.tc.Guard.ad_hoc', mockerror)
    monkeypatch.setattr('lib.api.APIv1.launch_ad_hoc', mockerror)
    result = runner.invoke(cli_ad_hoc, args)
    assert result.exit_code == 1
