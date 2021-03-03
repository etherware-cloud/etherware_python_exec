# -*- coding: utf-8 -*-
#
# Default values.
#

from os import mkdir
from os.path import exists, expanduser
from dataclasses import dataclass


@dataclass
class Environment:
    working_directory: str
    pid_file: str
    group_name: str = None

    def __post_init__(self):
        self.working_directory = expanduser(self.working_directory)
        self.pid_file = expanduser(self.pid_file)

    def setup(self):
        if not exists(self.working_directory):
            mkdir(self.working_directory)


ENVIRONMENTS = {
    "prod": Environment(
        working_directory="/var/lib/etherware.cloud",
        pid_file="/var/run/etherware.cloud.pid",
        group_name="etherware.cloud",
    ),
    "devel": Environment(
        working_directory="~/.local/lib/etherware.cloud",
        pid_file="~/.local/etherware.cloud.pid",
    ),
}

DEFAULT_ENVIRONMENT = "devel"
