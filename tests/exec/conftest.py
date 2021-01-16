import logging
import pytest
import asyncio
from urllib.parse import urljoin
from etherware.exec.exec.storage import MemoryStorage
from etherware.exec.exec.topic import (
    WriteableTopicClient,
    WriteableTopicServer,
    RedeableTopicClient,
    RedeableTopicServer,
)


@pytest.fixture
def topic_connector():
    def connector_inner(connector):
        def inner(topic=None, address=None, group=None):
            address = address or "http://localhost:8080"
            if group:
                address = urljoin(address, f"/{group}")
            return connector(MemoryStorage(), topic or "test", address)

        return inner

    return connector_inner


@pytest.fixture
def redeable_topic_server(topic_connector):
    return topic_connector(RedeableTopicServer)


@pytest.fixture
def writeable_topic_server(topic_connector):
    return topic_connector(WriteableTopicServer)


@pytest.fixture
def redeable_topic_client(topic_connector):
    return topic_connector(RedeableTopicClient)


@pytest.fixture
def writeable_topic_client(topic_connector):
    return topic_connector(WriteableTopicClient)


class ProducerContext:
    def __init__(self, pc):
        self.pc = pc

    async def __aenter__(self):
        logging.info(f"<aenter:producer: {self.pc.status()}")
        await self.pc.ready.wait()
        logging.info(f">aenter:producer: {self.pc.status()}")

    async def __aexit__(self, exc_type, exc, tb):
        logging.info(f"<aexit:producer: {self.pc.status()}")
        self.pc.production_completed.set()
        await self.pc.consuming_completed.wait()
        logging.info(f">aexit:producer: {self.pc.status()}")


class ConsumerContext:
    def __init__(self, pc):
        self.pc = pc

    async def __aenter__(self):
        logging.info(f"<aenter:consumer: {self.pc.status()}")
        self.pc.ready.set()
        logging.info(f">aenter:consumer: {self.pc.status()}")

    async def __aexit__(self, exc_type, exc, tb):
        logging.info(f"<aexit:consumer: {self.pc.status()}")
        self.pc.consuming_completed.set()
        await self.pc.production_completed.wait()
        logging.info(f">aexit:consumer: {self.pc.status()}")


class ProducerConsumer:
    def __init__(self):
        self.ready = asyncio.Event()
        self.production_completed = asyncio.Event()
        self.consuming_completed = asyncio.Event()

    def status(self):
        return {'ready': self.ready.is_set(),
                'production_completed': self.production_completed.is_set(),
                'consuming_completed': self.consuming_completed.is_set()}

    def producer(self, f):
        async def inner(*args, **kwargs):
            logging.info("<producer")
            try:
                return await f(ProducerContext(self), *args, **kwargs)
            finally:
                logging.info(">producer")

        return inner

    def consumer(self, f):
        async def inner(*args, **kwargs):
            logging.info("<consumer")
            try:
                return await f(ConsumerContext(self), *args, **kwargs)
            finally:
                logging.info(">consumer")

        return inner


@pytest.fixture
def sync():
    return ProducerConsumer()
