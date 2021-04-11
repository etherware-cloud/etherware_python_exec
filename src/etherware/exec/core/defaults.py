# -*- coding: utf-8 -*-
#
# Default values.
#
from etherware.exec.core.environment import Environment

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
