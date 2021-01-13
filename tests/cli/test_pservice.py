# -*- coding: utf-8 -*-
#
# Command line p-service test
#

from etherware.exec.cli import cli


def test_cli_pservice_help(cli_runner):
    result = cli_runner.invoke(cli, ["pservice", "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
