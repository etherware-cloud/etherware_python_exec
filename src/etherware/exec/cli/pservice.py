# -*- coding: utf-8 -*-
#
# P-service commad line operations.
#

import click
from .root import cli


@cli.group()
def pservice():
    click.echo("P-service commands")
    pass


@pservice.command()
def list():
    click.echo("List p-services")
    pass


@pservice.command()
def deploy():
    click.echo("Deploy p-service")
    pass


@pservice.command()
def kill():
    click.echo("Stop p-service")
    pass
