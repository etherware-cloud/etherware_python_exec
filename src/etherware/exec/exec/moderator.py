# -*- coding: utf-8 -*-
#
# Moderator.
#

from etherware.exec.logging import logger
from aiohttp import web
from zeroconf import ServiceInfo, Zeroconf
import socket


class Moderator(object):
    def __init__(self):
        self.listener_topics = {}
        self.available_ports = list(range(8080, 8888))
        self.listeners = {}
        self.zc = None

    def start(self):
        logger.info("Starting Moderator")
        self.zc = Zeroconf()

    def stop(self, loop):
        logger.info("Stop Moderator")
        self.zc.close()

        for topic_name, (site, _, _, _) in self.listeners.items():
            logger.info(f"Stopping {topic_name} listener")
            loop.create_task(site.stop())

        logger.info("Stopped Moderator")

    def publish_topic(self, topic_name, port, properties=None):
        logger.info(f"Registering {topic_name} consumer")
        info = ServiceInfo(
            "_http._tcp.local.",
            f"{topic_name}._http._tcp.local.",
            addresses=[socket.inet_aton("127.0.0.1")],
            port=port,
            properties={
                "etherware": True
            },  # dict(etherware=True, **(properties or {}))
        )
        self.zc.register_service(info)

    def app_factory(self, handler):
        app = web.Application()
        app.add_routes([web.get("/", handler)])
        return app

    async def start_listener(self, topic_name, handler):
        if topic_name in self.listeners:
            return self.listeners[topic_name]

        logger.info(f"Start listening for {topic_name} topic")

        port = self.available_ports.pop()
        app = self.app_factory(handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", port)
        await site.start()

        self.publish_topic(topic_name, port)
        self.listeners[topic_name] = (site, app, port, handler)

        return self.listeners[topic_name]
