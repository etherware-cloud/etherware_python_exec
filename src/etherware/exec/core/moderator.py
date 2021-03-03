# -*- coding: utf-8 -*-
#
# Moderator.
#

from etherware.exec.logging import logger
from zeroconf import ServiceInfo, Zeroconf
import socket
from urllib.parse import urlparse


class Moderator(object):
    def __init__(self):
        self.zc = None
        self._topic_info = {}

    def start(self):
        self.zc = Zeroconf()

    def stop(self):
        self.zc.unregister_all_services()
        self.zc.close()

    def is_published(self, topic_name):
        return topic_name in self._topic_info

    def publish_topic(self, topic_name, address, properties=None):
        logger.info(f"Registering topic {topic_name}")
        if self.is_published(topic_name):
            return False

        o = urlparse(address)
        hostip = socket.gethostbyname(o.hostname or socket.gethostname())
        info = ServiceInfo(
            "_http._tcp.local.",
            f"{topic_name}._http._tcp.local.",
            addresses=[socket.inet_aton(hostip)],
            port=int(o.port),
            properties=dict(etherware=True, **(properties or {})),
        )

        self._topic_info[topic_name] = info
        self.zc.register_service(info)

    def unpublish_topic(self, topic_name):
        logger.info(f"Unregistering topic {topic_name}")
        if not self.is_published(topic_name):
            return False

        self.zc.unregister_service(self._topic_info[topic_name])
        del self._topic_info[topic_name]

    def unpublish_topics(self):
        for topic in self._topic_info.keys():
            self.unpublish_topic(topic)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()
