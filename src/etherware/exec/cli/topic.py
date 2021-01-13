# -*- coding: utf-8 -*-
#
# Topic commad line operations.
#

import click
from .root import cli


@cli.group()
def topic():
    click.echo("Topics commands")
    pass


@topic.command()
def read():
    click.echo("Read topic")
    pass


@topic.command()
def write():
    click.echo("Write topic")
    pass


