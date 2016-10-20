"""
Testing tower companion CLI
"""
import os
from click.testing import CliRunner
from lib.tc import GuardError
from lib.cli import cli_kick, cli_monitor, DEFAULT_CONFIGURATION, config_file
from lib.cli import cli_kick_and_monitor, cli_ad_hoc_and_monitor, cli_ad_hoc


def mock_config_file(*args, **kwargs):
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, 'configuration.cfg')


def test_config_file(monkeypatch):

    monkeypatch.setattr('os.environ', {})
    assert config_file() == DEFAULT_CONFIGURATION

    monkeypatch.setattr('os.environ', {'TC_CONFIG': __file__})
    assert config_file() == __file__


def test_cli_kick(monkeypatch):

    def mockerror(*args, **kwargs):
        raise GuardError

    def mockreturn(*args, **kwargs):
        return 'just a test'

    monkeypatch.setattr('lib.tc.Guard.get_template_id', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.kick', mockreturn)
    monkeypatch.setattr('lib.tc.Guard.launch_data_to_url', mockreturn)
    monkeypatch.setattr('lib.cli.config_file', mock_config_file)

    runner = CliRunner()
    # clean execution
    result = runner.invoke(cli_kick, ['--template-name', 'test',
                                      '--extra-vars', 'version=1.0'])
    assert result.exit_code == 0

    # whooops! error
    monkeypatch.setattr('lib.tc.Guard.get_template_id', mockerror)
    result = runner.invoke(cli_kick, ['--template-name', 'test',
                                      '--extra-vars', 'version=1.0'])
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


def test_cli_ad_hoc_and_monitor(monkeypatch):

    def mockerror(*args, **kwargs):
        raise GuardError

    def mockreturn(*args, **kwargs):
        return 'just a test'

    monkeypatch.setattr('lib.tc.Guard.ad_hoc_and_monitor', mockreturn)
    monkeypatch.setattr('lib.cli.config_file', mock_config_file)

    runner = CliRunner()
    args = ['--inventory', 'test',
            '--machine-credential', 'test',
            '--module-name', 'test',
            '--module-args', 'test1 test2']
    # clean execution
    result = runner.invoke(cli_ad_hoc_and_monitor, args)
    assert result.exit_code == 0

    # error!
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
