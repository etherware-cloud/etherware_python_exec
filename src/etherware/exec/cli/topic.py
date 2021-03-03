# -*- coding: utf-8 -*-
#
# Topic commad line operations.
#

import click
from .root import cli

from ..lib.witness import Witness


@cli.group()
def topic():
    click.echo("Topics commands")
    pass


@topic.command()
@click.option("-t", "--timeout", default=5)
def list(timeout):
    click.echo("List local topics")
    w = Witness()

    click.echo("Searching for topics...")
    w.start()
    ts = w.list_topics(timeout=timeout)
    w.stop()

    click.echo("Topics found:")
    for t in ts:
        click.echo(f"Topic : {t}")


@topic.command()
def read():
    click.echo("Read topic")
    pass


@topic.command()
def write():
    click.echo("Write topic")
    pass
