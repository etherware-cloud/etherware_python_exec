# -*- coding: utf-8 -*-
#
# Daemon deployment testing
#
import os
from etherware.exec.core.daemon import Daemon


def test_set_and_recover_process_id_by_file(tmp_path):
    daemon = Daemon(pid_file=tmp_path / "pid_file.txt")
    daemon._set_process_id_by_file()
    pid = daemon._get_process_id_by_file()
    assert int(pid) == os.getpid()


def test_set_and_recover_process_id_by_list():
    daemon = Daemon()
    process = daemon._get_process_id_by_process_list()
    assert process == []
