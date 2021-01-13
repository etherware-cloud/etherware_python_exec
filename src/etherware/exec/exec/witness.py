# -*- coding: utf-8 -*-
#
# Moderator.
#

from zeroconf import (
    IPVersion,
    Zeroconf,
    ServiceBrowser,
    ServiceStateChange,
)
from typing import cast
from time import sleep


class Witness(object):
    def __init__(self):
        self.zc = None
        self.topics = {}

    def start(self):
        self.zc = Zeroconf(ip_version=IPVersion.All)

    def stop(self):
        self.zc.close()

    def on_service_state_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                addresses = [
                    "%s:%d" % (addr, cast(int, info.port))
                    for addr in info.parsed_addresses()
                ]

                if info.properties and info.properties.get(b"etherware"):
                    self.topics[name] = {"address": addresses}
        if state_change is ServiceStateChange.Removed:
            if name in self.topics:
                del self.topics[name]

    def list_topics(self, timeout=5):
        services = ["_http._tcp.local."]

        ServiceBrowser(
            self.zc, services, handlers=[self.on_service_state_change]
        )

        sleep(timeout)

        return [self.topics]
