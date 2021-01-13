# -*- coding: utf-8 -*-
#
# Command line root test
#

from etherware.exec.cli import cli


def test_cli_help(cli_runner):
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
