# -*- coding: utf-8 -*-
#
# Topic classes.
#

from urllib.parse import urlparse
from etherware.exec.logging import logger
import asyncio
import aiohttp
from aiohttp import web


class TopicConnection:
    def __init__(self, websocket_response, group):
        self.ws = websocket_response
        self.group = group


class TopicProcessor:
    def __init__(self, topic_name):
        self.topic_name = topic_name

    async def connection(self, tc: TopicConnection):
        raise NotImplementedError

    async def processing(self, tc: TopicConnection, msg):
        raise NotImplementedError

    async def disconnection(self, tc: TopicConnection):
        raise NotImplementedError


class WriteableTopic(TopicProcessor):
    def __init__(self, topic_name):
        super().__init__(topic_name)
        self.queue = asyncio.Queue()

    async def connection(self, ws):
        logger.debug(f"Connected to writeable of {self.topic_name}")
        answer = await self.queue.get()
        await ws.send_str(answer)

    async def processing(self, ws, msg):
        if msg.data == "close":
            return False
        elif msg.data == "ready":
            while True:
                try:
                    answer = await asyncio.wait_for(
                        self.queue.get(), timeout=0.2
                    )
                except asyncio.TimeoutError:
                    if ws.closed:
                        return False
                else:
                    await ws.send_str(answer)
                    return True

    async def disconnection(self, ws):
        logger.debug(f"Disconnected from writeable of {self.topic_name}")

    async def put(self, message):
        await self.queue.put(message)


class RedeableTopic(TopicProcessor):
    def __init__(self, topic_name):
        super().__init__(topic_name)
        self.queue = asyncio.Queue()

    async def connection(self, ws):
        logger.debug(f"Connected to readeable of {self.topic_name}.")

    async def processing(self, ws, msg):
        if msg.type == aiohttp.WSMsgType.TEXT:
            await self.queue.put(msg.data)
            await ws.send_str("ready")
            return True
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(
                f"topic {self.topic_name} connection closed"
                f" raised with exception {ws.exception()}"
            )
            return False

    async def disconnection(self, ws):
        logger.debug(f"Disconnected readeable of {self.topic_name}")
        if not ws.closed:
            await ws.send_str("close")

    async def get(self):
        return await self.queue.get()


class TopicConnection:
    def __init__(self, address):
        self.address = address

    async def start(self):
        raise NotImplementedError

    async def stop(self):
        logger.info("Trying to stop, but not implemented")


class TopicClient(TopicConnection):
    def __init_(self, address):
        super().__init__(address)
        self.task = None
        self.ws = None

    async def connect(self):
        logger.debug(
            f"Connecting as client of {self.topic_name} to {self.address}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.address) as ws:

                self.ws = ws
                await self.connection(ws)

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

                await self.disconnection(ws)

    async def start(self):
        logger.debug(f"Starting client to {self.address}")
        self.task = asyncio.create_task(self.connect())

    async def stop(self):
        logger.debug(f"Stopping client to {self.address}")
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self.task:
            await self.task
            self.task = None
        logger.debug(f"Stopped client to {self.address}")


class TopicServer(TopicConnection):
    def __init_(self, address):
        super().__init__(address)
        self.site = None

    async def start(self):
        logger.debug(f"Starting server on {self.address}")
        o = urlparse(self.address)
        app = web.Application()
        app.add_routes(
            [web.get("/", self.handler), web.get("/{group}", self.handler)]
        )
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, o.hostname, o.port)
        await self.site.start()

    async def stop(self):
        logger.debug(f"Stopping server on {self.address}")
        await self.site.stop()

    async def handler(self, request):
        logger.debug(f"Connecting to server on {self.address} from {request}")

        group = request.match_info.get('group')
        logger.debug(f"Group: {group or 'ROOT'}")

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        await self.connection(ws)

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if not await self.processing(ws, msg):
                    await ws.close()
                    break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(
                    f"Topic connection closed with exception {ws.exception()}"
                )

        await self.disconnection(ws)
        return ws


class WriteableTopicClient(WriteableTopic, TopicClient):
    def __init__(self, topic, address):
        WriteableTopic.__init__(self, topic)
        TopicClient.__init__(self, address)


class WriteableTopicServer(WriteableTopic, TopicServer):
    def __init__(self, topic, address):
        WriteableTopic.__init__(self, topic)
        TopicServer.__init__(self, address)


class RedeableTopicClient(RedeableTopic, TopicClient):
    def __init__(self, topic, address):
        RedeableTopic.__init__(self, topic)
        TopicClient.__init__(self, address)


class RedeableTopicServer(RedeableTopic, TopicServer):
    def __init__(self, topic, address):
        RedeableTopic.__init__(self, topic)
        TopicServer.__init__(self, address)
