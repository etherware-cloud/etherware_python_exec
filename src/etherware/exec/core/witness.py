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
from time import sleep, time_ns


LOCAL_SUFFIX = "_http._tcp.local."


class NotTopicAvailableError(Exception):
    pass


class Witness(object):
    def __init__(self, timeout=None, update_lapse=None):
        self._zc = None
        self._topics = {}
        self._next_update = None
        self._update_lapse = update_lapse or 5000
        self._timeout = (timeout or 2000)/1000

    def start(self):
        self._zc = Zeroconf(ip_version=IPVersion.All)

    def stop(self):
        self._zc.close()

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
                    "%s:%d" % (address, cast(int, info.port))
                    for address in info.parsed_addresses()
                ]

                if info.properties and info.properties.get(b"etherware"):
                    self._topics[name] = {"address": addresses}
        if state_change is ServiceStateChange.Removed:
            if name in self._topics:
                del self._topics[name]

    def _force_update_list_of_topics(self):
        services = [LOCAL_SUFFIX]

        ServiceBrowser(
            self._zc, services, handlers=[self.on_service_state_change]
        )

        sleep(self._timeout)

    def _update_list_of_topics(self):
        if self._next_update is None or self._next_update < time_ns():
            self._force_update_list_of_topics()
            self._next_update = time_ns() + self._update_lapse

    def list_topics(self):
        self._update_list_of_topics()
        return [t[:-len(LOCAL_SUFFIX)-1] for t in self._topics]

    def _getitem__(self, topic_name):
        self._update_list_of_topics()
        try:
            return self._topics[topic_name]
        except KeyError:
            raise NotTopicAvailableError

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()
