# -*- coding: utf-8 -*-
#
# Environment class definition
#

from os import mkdir
from os.path import exists, expanduser
from dataclasses import dataclass
from typing import Optional


@dataclass
class Environment:
    """
    Configuration environment class.

    working_directory: Working directory path.
    pid_file: PID storage file.
    group_name: System group name in which daemon should run.
    """
    working_directory: str
    pid_file: str
    group_name: Optional[str] = None

    def __post_init__(self) -> None:
        self.working_directory = expanduser(self.working_directory)
        self.pid_file = expanduser(self.pid_file)

    def setup(self) -> None:
        if not exists(self.working_directory):
            mkdir(self.working_directory)
