# -*- coding: utf-8 -*-
#
# Root entrypoint for etherware.exec package.
#

import click
from .root import cli
from etherware.exec.core.defaults import DEFAULT_ENVIRONMENT
from etherware.exec.core.mainloop import ExecutorMainLoop
from etherware.exec.core.witness import Witness
from os.path import expanduser


@cli.command()
@click.option("-E", "--environment", default=DEFAULT_ENVIRONMENT)
@click.option("-p", "--pid-file", default=None)
@click.option("-o", "--stdout", default="~/out.txt")
@click.option("-e", "--stderr", default="~/err.txt")
def start(environment, pid_file, stdout, stderr):
    click.echo(f"Starting on environment {environment}.")
    click.echo(
        f"PID file {expanduser(pid_file)}" if pid_file else "Not using pid-file"
    )
    click.echo(
        f"Redirecting stdout to: {expanduser(stdout)}"
        if stdout
        else "Nulling stdout"
    )
    click.echo(
        f"Redirecting stderr to {expanduser(stderr)}"
        if stdout
        else "Nulling stderr"
    )
    mainloop = ExecutorMainLoop(
        pidfile=expanduser(pid_file) if pid_file else None,
        stdin=None,
        stdout=expanduser(stdout),
        stderr=expanduser(stderr),
    )
    mainloop.start()
    pass


@cli.command()
def stop():
    click.echo("Stop executor")
    mainloop = ExecutorMainLoop()
    mainloop.stop()
    pass


@cli.command()
def restart():
    click.echo("Restart executor")
    mainloop = ExecutorMainLoop()
    mainloop.restart()
    pass


@cli.command()
def status():
    click.echo("Executor status")
    mainloop = ExecutorMainLoop()
    mainloop.status()
    w = Witness()
    w.start()
    for s in w.list_topics():
        print(s)
    w.stop()

    pass
