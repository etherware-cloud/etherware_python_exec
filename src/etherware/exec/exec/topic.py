# -*- coding: utf-8 -*-
#
# Topic classes.
#

from urllib.parse import urlparse
from etherware.exec.logging import logger, debug
import asyncio
import aiohttp
import weakref
from aiohttp import web, WSCloseCode
from .topic_queue import TopicQueue


CLOSE_SIGNAL = "-close-"
READY_SIGNAL = "-ready-"


class TopicProcessor:
    @debug
    def __init__(self, storage, topic_name):
        self.topic_name = topic_name
        self.queue = TopicQueue(storage)

    async def connection(self, ws, group):
        raise NotImplementedError

    async def processing(self, ws, msg, group):
        raise NotImplementedError

    async def disconnection(self, ws):
        raise NotImplementedError

    @debug
    def setup(self):
        self.queue.setup()

    def __str__(self):
        return (
            f"<{self.__class__.__name__}[0x{id(self):x}] "
            f"topic_name={self.topic_name} "
            f"queue={self.queue} >"
        )


class WriteableTopic(TopicProcessor):
    @debug
    def __init__(self, *args, **kwargs):
        TopicProcessor.__init__(self, *args, **kwargs)
        self.setup()

    @debug
    async def connection(self, ws, group=None):
        pass

    @debug
    async def processing(self, ws, msg, group=None):
        if msg.data == CLOSE_SIGNAL:
            return False
        elif msg.data == READY_SIGNAL:
            while True:
                try:
                    answer = await asyncio.wait_for(
                        self.queue.get(group), timeout=1
                    )
                except asyncio.TimeoutError:
                    logger.info("Writeable TIMEOUT")
                    if ws.closed:
                        logger.info("Writeable Closed")
                        return False
                    logger.info("Writeable not closed is a server")
                else:
                    await ws.send_str(answer)
                    return True

    @debug
    async def disconnection(self, ws):
        pass

    @debug
    async def put(self, message):
        await self.queue.put(message)


class RedeableTopic(TopicProcessor):
    @debug
    def __init__(self, *args, **kwargs):
        TopicProcessor.__init__(self, *args, **kwargs)

    @debug
    async def connection(self, ws, group=None):
        await ws.send_str(READY_SIGNAL)
        logger.debug("Ready Signal sended")

    @debug
    async def processing(self, ws, msg, group=None):
        if msg.type == aiohttp.WSMsgType.TEXT:
            await self.queue.put(msg.data)
            await ws.send_str(READY_SIGNAL)
            return True
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(
                f"topic {self.topic_name} connection closed"
                f" raised with exception {ws.exception()}"
            )
            return False

    @debug
    async def disconnection(self, ws):
        if not ws.closed:
            await ws.send_str(CLOSE_SIGNAL)

    @debug
    async def get(self, group=None):
        data = await self.queue.get(group)
        return data


class TopicConnection:
    @debug
    def __init__(self, address):
        self.address = address

    async def start(self):
        raise NotImplementedError

    async def stop(self):
        logger.info("Trying to stop, but not implemented")


class TopicClient(TopicConnection):
    @debug
    def __init__(self, address):
        TopicConnection.__init__(self, address)
        self.task = None
        self.ws = None

    @debug
    async def connect(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.address) as ws:

                logger.debug("A")

                self.ws = ws
                await self.connection(ws)

                logger.debug("B")

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if not await self.processing(ws, msg):
                            await ws.close()
                            break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(
                            f"topic {self.topic_name} connection closed"
                            f" raised with exception {ws.exception()}"
                        )
                        break
                    else:
                        logger.debug(f"Ignored message {msg}")

                logger.debug("C")

                await self.disconnection(ws)

    @debug
    async def start(self):
        self.task = asyncio.create_task(self.connect())

    @debug
    async def stop(self):
        if self.ws:
            await self.disconnection(self.ws)
            await self.ws.close()
            self.ws = None
        if self.task:
            await self.task
            self.task = None


class TopicServer(TopicConnection):
    @debug
    def __init__(self, address):
        TopicConnection.__init__(self, address)
        self.site = None

    @debug
    async def on_shutdown(self, app):
        for ws in set(app["websockets"]):
            await ws.close(
                code=WSCloseCode.GOING_AWAY, message="Server Shutdown"
            )

    @debug
    async def start(self):
        o = urlparse(self.address)
        app = web.Application()
        app['websockets'] = weakref.WeakSet()
        app.add_routes(
            [web.get("/", self.handler), web.get("/{group}", self.handler)]
        )
        app.on_shutdown.append(self.on_shutdown)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, o.hostname, o.port)
        await self.site.start()

    @debug
    async def stop(self):
        logger.info("Stoping runner")
        await self.runner.cleanup()

    @debug
    async def handler(self, request):
        group = request.match_info.get("group")
        logger.debug(f"Group: {group or 'ROOT'}")

        ws = web.WebSocketResponse()
        await ws.prepare(request)
        request.app['websockets'].add(ws)

        await self.connection(ws, group)

        async for msg in ws:
            logger.debug(f"Server: {ws}")
            if msg.type == aiohttp.WSMsgType.TEXT:
                if not await self.processing(ws, msg, group):
                    logger.debug("Server: Close?")
                    await ws.close()
                    break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(
                    f"Topic connection closed with exception {ws.exception()}"
                )

        await self.disconnection(ws)
        return ws


class WriteableTopicClient(WriteableTopic, TopicClient):
    @debug
    def __init__(self, storage, topic, address):
        WriteableTopic.__init__(self, storage, topic)
        TopicClient.__init__(self, address)


class WriteableTopicServer(WriteableTopic, TopicServer):
    @debug
    def __init__(self, storage, topic, address):
        WriteableTopic.__init__(self, storage, topic)
        TopicServer.__init__(self, address)


class RedeableTopicClient(RedeableTopic, TopicClient):
    @debug
    def __init__(self, storage, topic, address):
        RedeableTopic.__init__(self, storage, topic)
        TopicClient.__init__(self, address)


class RedeableTopicServer(RedeableTopic, TopicServer):
    @debug
    def __init__(self, storage, topic, address):
        RedeableTopic.__init__(self, storage, topic)
        TopicServer.__init__(self, address)
