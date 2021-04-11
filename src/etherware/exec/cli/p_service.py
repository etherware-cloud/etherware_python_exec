# -*- coding: utf-8 -*-
#
# P-service command line operations.
#

import click
from .root import cli


@cli.group()
def p_service():
    click.echo("P-service commands")
    pass


@p_service.command("list")
def list_p_services():
    click.echo("List p-services")
    pass


@p_service.command()
def deploy():
    click.echo("Deploy p-service")
    pass


@p_service.command()
def kill():
    click.echo("Stop p-service")
    pass
