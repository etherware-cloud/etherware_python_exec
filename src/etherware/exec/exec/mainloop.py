# -*- coding: utf-8 -*-
#
# Mainloop.
#

from etherware.exec.logging import logger
from .daemon import Daemon
from .defaults import ENVIRONMENTS, DEFAULT_ENVIRONMENT
from .moderator import Moderator
from aiohttp import web

import asyncio


class ExecutorMainLoop(Daemon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.moderator = Moderator()
        self.clean = False

    async def handle(self, request):
        logger.info("Start connection")

        name = request.match_info.get("name", "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    def setup(self):
        self.moderator.start()

    def cleanup(self, loop):
        logger.info("Cleaning Loop")
        self.moderator.stop(loop)

    async def run(self):
        logger.info("Factoring executor")

        await self.moderator.start_listener("executable", self.handle)
        await self.moderator.start_listener("deployment", self.handle)
        await self.moderator.start_listener("command", self.handle)

        logger.info("Continue for ever Loop")
