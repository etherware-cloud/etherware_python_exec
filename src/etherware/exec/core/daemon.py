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
from pathlib import Path
from etherware.exec.logging import logger
from etherware.exec.core.types import NullablePath, EventLoop, Union, List


NULL_DEVICE = Path("/dev/null")


class Daemon(object):
    def __init__(
        self,
        working_directory: NullablePath = None,
        pid_file: NullablePath = None,
        stdin: NullablePath = None,
        stdout: NullablePath = None,
        stderr: NullablePath = None,
    ) -> None:
        self.ver = "0.1"  # version
        self.pauseRunLoop = 0
        self.restartPause = 1
        self.waitToHardKill = 3

        self.isReloadSignal = False
        self.processName = os.path.basename(sys.argv[0])
        self.working_directory = working_directory or os.getcwd()
        self.stdin = stdin or NULL_DEVICE
        self.stdout = stdout or NULL_DEVICE
        self.stderr = stderr or NULL_DEVICE
        self.pid_file = pid_file

        self.loop = None

    def _sigterm_handler(self, signum: int, loop: EventLoop) -> None:
        logger.info(f"Terminal signal: {signum}!!!")
        self.cleanup(loop)
        loop.stop()

    def _reload_handler(self, signum, _loop: EventLoop) -> None:
        logger.info(f"Reload handler signal: {signum}!!!")
        self.isReloadSignal = True

    @staticmethod
    def echo(m):
        logger.info(m)

    def _parent_fork(self, n: int) -> None:
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            self.echo(f"fork #{n} failed: {e.errno} ({e.strerror})\n")
            sys.exit(1)

    def _make_daemon(self) -> None:
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

    def _set_process_id_by_file(self) -> None:
        if self.pid_file:
            pid = str(os.getpid())
            with open(self.pid_file, "w+") as pf:
                pf.write(f"{pid}\n")

    def _get_process_id_by_file(self) -> Union[int, None]:
        try:
            with open(self.pid_file, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
        return pid

    def _get_process_id_by_process_list(self) -> List[psutil.Process]:
        ignore_list = ["strace", "stop"]
        processes = []

        for p in psutil.process_iter():
            if self.processName in [
                part.split("/")[-1] for part in p.cmdline()
            ]:
                # Skip  the current process
                if p.pid != os.getpid() and not any(
                    ign in p.cmdline() for ign in ignore_list
                ):
                    processes.append(p)

        return processes

    def _get_process_id(self) -> List[psutil.Process]:
        if self.pid_file:
            pid = self._get_process_id_by_file()
            return [psutil.Process(pid)] if pid else []
        else:
            return self._get_process_id_by_process_list()

    def _pid_list(self, separator: str = ',') -> str:
        processes = self._get_process_id()
        return separator.join([str(p) for p in processes]) if processes else None

    async def setup_signal_handler(self) -> None:
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

    def setup(self) -> None:
        raise NotImplementedError

    def start(self) -> None:
        """
        Start daemon.
        """
        # Check if the daemon is already running.
        processes = self._pid_list()

        if processes:
            self.echo(
                f"Find a previous daemon processes with PIDs {processes}. "
                "Is not already the daemon running?"
            )
            sys.exit(1)
        else:
            self.echo(f"Start the daemon version {self.ver}")

        # Daemonize the main process
        self._make_daemon()
        # Save PID if pid_file is defined
        self._set_process_id_by_file()
        # Setup loop
        self.setup()
        # Start loop
        loop = asyncio.get_event_loop()
        loop.create_task(self.setup_signal_handler())
        loop.create_task(self.run())
        loop.run_forever()

    async def run(self) -> None:
        """
        Main run async execution.
        This method have to being override.
        """
        raise NotImplementedError

    def version(self) -> None:
        """
        Returns daemon version
        """
        self.echo(f"The daemon version {self.ver}")

    def status(self) -> None:
        """
        Print daemon status.
        """
        process_list = self._pid_list()

        if process_list:
            self.echo(f"The daemon is running with PID {process_list}.")
        else:
            self.echo("The daemon is not running!")

    def reload(self) -> None:
        """
        Reload the daemon.
        """

        processes = self._get_process_id()

        if processes:
            for p in processes:
                os.kill(p.pid, signal.SIGHUP)
                self.echo(
                    f"Send SIGHUP signal into"
                    " the daemon process with PID {p.pid}."
                )
        else:
            self.echo("The daemon is not running!")

    def stop(self) -> None:
        """
        Stop the daemon.
        """

        processes = self._get_process_id()

        def on_terminate(process):
            self.echo(
                f"The daemon process with PID {process.pid}"
                " has ended correctly."
            )

        if processes:
            for p in processes:
                p.terminate()

            gone, alive = psutil.wait_procs(
                processes, timeout=self.waitToHardKill, callback=on_terminate
            )

            for p in alive:
                self.echo(
                    f"The daemon process with PID {p.pid}"
                    " was killed with SIGTERM!"
                )
                p.kill()
        else:
            self.echo("Cannot find some daemon process, I will do nothing.")

    def restart(self) -> None:
        """
        Restart the daemon.
        """
        self.stop()

        if self.restartPause:
            time.sleep(self.restartPause)

        self.start()

    def cleanup(self, loop: EventLoop):
        pass
