# -*- coding: utf-8 -*-
#
# Daemon.
#

import sys
import os
import time
import signal
import psutil
import asyncio
import functools
from etherware.exec.logging import logger


NULL_DEVICE = "/dev/null"


class Daemon(object):
    def __init__(
        self,
        pidfile=None,
        stdin=None,
        stdout=None,
        stderr=None,
    ):
        self.ver = 0.1  # version
        self.pauseRunLoop = 0
        self.restartPause = 1
        self.waitToHardKill = 3

        self.isReloadSignal = False
        self.processName = os.path.basename(sys.argv[0])
        self.stdin = stdin or NULL_DEVICE
        self.stdout = stdout or NULL_DEVICE
        self.stderr = stderr or NULL_DEVICE
        self.pidfile = pidfile

        self.loop = None

    def _sigterm_handler(self, signum, loop):
        logger.info(f"Terminal signal: {signum}!!!")
        self.cleanup(loop)
        #if loop.is_running():
        #    logger.info("Still running!!!")
        loop.stop()

    def _reload_handler(self, signum, loop):
        logger.info(f"Reload handler signal: {signum}!!!")
        self.isReloadSignal = True

    @staticmethod
    def echo(m):
        logger.info(m)

    def _parent_fork(self, n):
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            self.echo(f"fork #{n} failed: {e.errno} ({e.strerror})\n")
            sys.exit(1)

    def _makeDaemon(self):
        """
        Make a daemon, do double-fork magic.
        """

        # Do first fork.
        self._parent_fork(1)

        # Decouple from the parent environment.
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # Do second fork.
        self._parent_fork(1)

        m = "The daemon process is going to background."
        self.echo(m)

        # Redirect standard file descriptors.
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, "r")
        so = open(self.stdout, "a+")
        se = open(self.stderr, "a+")
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def _setProcessIdByFile(self):
        if self.pidfile:
            pid = str(os.getpid())
            with open(self.pidfile, "w+") as pf:
                pf.write(f"{pid}\n")

    def _getProcessIdByFile(self):
        try:
            with open(self.pidfile, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
        return pid

    def _getProcessIdByProcessList(self):
        ignore_list = ["strace", "stop"]
        procs = []

        for p in psutil.process_iter():
            if self.processName in [
                part.split("/")[-1] for part in p.cmdline()
            ]:
                # Skip  the current process
                if p.pid != os.getpid() and not any(
                    ign in p.cmdline() for ign in ignore_list
                ):
                    procs.append(p)

        return procs

    def _getProcessId(self):
        if self.pidfile:
            return [self._getProcessIdByFile()]
        else:
            return self._getProcessIdByProcessList()

    async def setup_signal_handler(self):
        loop = asyncio.get_running_loop()

        # Handle signals
        loop.add_signal_handler(
            signal.SIGINT,
            functools.partial(self._sigterm_handler, signal.SIGINT, loop),
        )
        loop.add_signal_handler(
            signal.SIGTERM,
            functools.partial(self._sigterm_handler, signal.SIGTERM, loop),
        )
        loop.add_signal_handler(
            signal.SIGHUP,
            functools.partial(self._reload_handler, signal.SIGHUP, loop),
        )

    def start(self):
        """
        Start daemon.
        """
        # Check if the daemon is already running.
        procs = self._getProcessId()

        if procs:
            pids = ",".join([str(p.pid) for p in procs])
            self.echo(
                f"Find a previous daemon processes with PIDs {pids}. "
                "Is not already the daemon running?"
            )
            sys.exit(1)
        else:
            self.echo(f"Start the daemon version {self.ver}")

        # Daemonize the main process
        self._makeDaemon()
        # Save PID if pidfile is defined
        self._setProcessIdByFile()
        # Setup loop
        self.setup()
        # Start loop
        loop = asyncio.get_event_loop()
        loop.create_task(self.setup_signal_handler())
        loop.create_task(self.run())
        loop.run_forever()

    # this method you have to override
    async def run(self):
        pass

    def version(self):
        self.echo(f"The daemon version {self.ver}")

    def status(self):
        """
        Get status of the daemon.
        """

        procs = self._getProcessId()

        if procs:
            pids = ",".join([str(p.pid) for p in procs])
            self.echo(f"The daemon is running with PID {pids}.")
        else:
            self.echo("The daemon is not running!")

    def reload(self):
        """
        Reload the daemon.
        """

        procs = self._getProcessID()

        if procs:
            for p in procs:
                os.kill(p.pid, signal.SIGHUP)
                self.echo(
                    f"Send SIGHUP signal into"
                    " the daemon process with PID {p.pid}."
                )
        else:
            self.echo("The daemon is not running!")

    def stop(self):
        """
        Stop the daemon.
        """

        procs = self._getProcessId()

        def on_terminate(process):
            self.echo(
                f"The daemon process with PID {process.pid}"
                " has ended correctly."
            )

        if procs:
            for p in procs:
                p.terminate()

            gone, alive = psutil.wait_procs(
                procs, timeout=self.waitToHardKill, callback=on_terminate
            )

            for p in alive:
                self.echo(
                    f"The daemon process with PID {p.pid}"
                    " was killed with SIGTERM!"
                )
                p.kill()
        else:
            self.echo("Cannot find some daemon process, I will do nothing.")

    def restart(self):
        """
        Restart the daemon.
        """
        self.stop()

        if self.restartPause:
            time.sleep(self.restartPause)

        self.start()
