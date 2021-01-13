import logging
import pytest
import asyncio
import socket
from urllib.parse import urljoin
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
            return connector(
                topic or "test",
                address
            )

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


@pytest.mark.asyncio
async def test_RedeableTopicServer(caplog, redeable_topic_server):
    with caplog.at_level(logging.DEBUG):
        rts = redeable_topic_server()

        await rts.start()

        await asyncio.sleep(1)

        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result_of_check = a_socket.connect_ex(("localhost", 8080))
        assert result_of_check == 0

        await rts.stop()

        result_of_check = a_socket.connect_ex(("localhost", 8080))
        assert result_of_check != 0


@pytest.mark.asyncio
async def test_WriteableTopicServer(caplog, writeable_topic_server):
    with caplog.at_level(logging.DEBUG):
        wts = writeable_topic_server()

        await wts.start()

        await asyncio.sleep(1)

        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result_of_check = a_socket.connect_ex(("localhost", 8080))
        assert result_of_check == 0

        await wts.stop()

        result_of_check = a_socket.connect_ex(("localhost", 8080))
        assert result_of_check != 0


@pytest.mark.asyncio
async def test_WriteableTopicClient_one_message(
    caplog, redeable_topic_server, writeable_topic_client
):
    with caplog.at_level(logging.DEBUG):
        rts = redeable_topic_server()
        wtc = writeable_topic_client()

        await rts.start()
        await wtc.start()

        await wtc.put("hello")
        data = await rts.get()
        assert data == "hello"

        await wtc.stop()
        await rts.stop()


@pytest.mark.asyncio
async def test_WriteableTopicClient_many_messages(
    caplog, redeable_topic_server, writeable_topic_client
):
    to_send = ["hello", "my", "word"]
    with caplog.at_level(logging.DEBUG):
        rts = redeable_topic_server()
        wtc = writeable_topic_client()

        await rts.start()
        await wtc.start()

        for w in to_send:
            logging.info(f"Testing {w} start")
            await wtc.put(w)
            data = await rts.get()
            assert data == w
            logging.info(f"Testing {w} done")

        await wtc.stop()
        await rts.stop()


@pytest.mark.asyncio
async def test_WriteableTopicClient_many_messages_burst(
    caplog, redeable_topic_server, writeable_topic_client
):
    to_send = ["hello", "my", "word"]
    with caplog.at_level(logging.DEBUG):
        rts = redeable_topic_server()
        wtc = writeable_topic_client()

        await rts.start()
        await wtc.start()

        for w in to_send:
            logging.info(f"Testing {w} start")
            await wtc.put(w)

        for e in to_send:
            data = await rts.get()
            assert data == e
            logging.info(f"Testing {e} done")

        await wtc.stop()
        await rts.stop()


@pytest.mark.asyncio
async def test_WriteableTopicServer_one_message(
    caplog, writeable_topic_server, redeable_topic_client
):
    with caplog.at_level(logging.DEBUG):
        rtc = redeable_topic_client()
        wts = writeable_topic_server()

        await wts.start()
        await rtc.start()

        await wts.put("hello")
        data = await rtc.get()
        assert data == "hello"

        await rtc.stop()
        await wts.stop()


@pytest.mark.asyncio
async def test_WriteableTopicServer_many_messages(
    caplog, writeable_topic_server, redeable_topic_client
):
    to_send = ["hello", "my", "word"]
    with caplog.at_level(logging.DEBUG):
        rtc = redeable_topic_client()
        wts = writeable_topic_server()

        await wts.start()
        await rtc.start()

        for w in to_send:
            logging.info(f"Testing {w} start")
            await wts.put(w)
            data = await rtc.get()
            assert data == w
            logging.info(f"Testing {w} done")

        await rtc.stop()
        await wts.stop()


@pytest.mark.asyncio
async def test_WriteableTopicServer_many_messages_burst(
    caplog, writeable_topic_server, redeable_topic_client
):
    to_send = ["hello", "my", "word"]
    with caplog.at_level(logging.DEBUG):
        rtc = redeable_topic_client()
        wts = writeable_topic_server()

        await wts.start()
        await rtc.start()

        for w in to_send:
            logging.info(f"Testing {w} start")
            await wts.put(w)

        for e in to_send:
            data = await rtc.get()
            assert data == e
            logging.info(f"Testing {e} done")

        await rtc.stop()
        await wts.stop()


@pytest.mark.asyncio
async def test_one_to_many_same_group(
    caplog, writeable_topic_server, redeable_topic_client
):
    to_send = ["hello", "my", "word", "you", "are", "beatiful"]
    with caplog.at_level(logging.DEBUG):
        wts = writeable_topic_server()
        client_count = 3
        clients = [redeable_topic_client() for _ in range(client_count)]

        await wts.start()
        for client in clients:
            await client.start()

        for w in to_send:
            logging.info(f"Testing {w} start")
            await wts.put(w)

        for client_id, client in enumerate(clients):
            for e in to_send[client_id::client_count]:
                data = await client.get()
                assert data == e
                logging.info(f"Testing {e} done by client {client_id}")

        for client in clients:
            await client.stop()
        await wts.stop()


@pytest.mark.asyncio
async def test_many_to_one_same_group(
    caplog, writeable_topic_client, redeable_topic_server
):
    to_send = ["hello", "my", "word", "you", "are", "beatiful"]
    with caplog.at_level(logging.DEBUG):
        rts = redeable_topic_server()
        client_count = 3
        clients = [writeable_topic_client() for _ in range(client_count)]

        await rts.start()
        for client in clients:
            await client.start()

        for client_id, client in enumerate(clients):
            for w in to_send[client_id::client_count]:
                logging.info(f"Testing {w} start from {client_id}")
                data = await client.put(w)

        data = []
        for e in to_send:
            item = await rts.get()
            logging.info(f"Testing {item} stop")
            data.append(item)

        assert sorted(data) == sorted(to_send)

        for client_id, client in enumerate(clients):
            logging.debug(f"Stopping client: {client_id}")
            await client.stop()
            logging.debug(f"Stopped client: {client_id}")

        for task in asyncio.all_tasks():
            logging.debug(f"Task: {task} :")

        await rts.stop()


@pytest.mark.asyncio
async def _test_one_to_many_diff_group(
    caplog, writeable_topic_server, redeable_topic_client
):
    to_send = ["hello", "my", "word", "you", "are", "beatiful"]
    with caplog.at_level(logging.DEBUG):
        wts = writeable_topic_server()
        client_count = 3
        clients = [
            redeable_topic_client(group=f"group_{i}")
            for i in range(client_count)
        ]

        await wts.start()
        for client in clients:
            await client.start()

        for w in to_send:
            logging.info(f"Testing {w} start")
            await wts.put(w)

        for client_id, client in enumerate(clients):
            for e in to_send:
                data = await client.get()
                assert data == e
                logging.info(f"Testing {e} done by client {client_id}")

        for client in clients:
            await client.stop()
        await wts.stop()
