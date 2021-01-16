import logging
import pytest
import asyncio
import socket


@pytest.mark.asyncio
async def test_RedeableTopicServer(caplog, redeable_topic_server):
    with caplog.at_level(logging.DEBUG):
        rts = redeable_topic_server()

        await rts.start()

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

        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result_of_check = a_socket.connect_ex(("localhost", 8080))
        assert result_of_check == 0

        await wts.stop()

        result_of_check = a_socket.connect_ex(("localhost", 8080))
        assert result_of_check != 0


@pytest.mark.asyncio
async def test_WriteableTopicClient_one_message(
    caplog, redeable_topic_server, writeable_topic_client, sync
):
    expected = "hello"
    with caplog.at_level(logging.DEBUG):
        rts = redeable_topic_server()
        wtc = writeable_topic_client()

        await rts.start()

        @sync.producer
        async def producer(c):
            await wtc.start()
            async with c:
                await wtc.put(expected)
            await wtc.stop()
            return expected

        @sync.consumer
        async def consumer(c):
            async with c:
                return await rts.get()

        pc_result = await asyncio.gather(producer(), consumer())
        assert pc_result[0] == pc_result[1]

        await rts.stop()


@pytest.mark.asyncio
async def test_WriteableTopicClient_many_messages(
    caplog, redeable_topic_server, writeable_topic_client, sync
):
    to_send = ["hello", "my", "word"]
    with caplog.at_level(logging.INFO):
        rts = redeable_topic_server()
        wtc = writeable_topic_client()

        await rts.start()

        @sync.producer
        async def producer(c):
            await wtc.start()
            async with c:
                for w in to_send:
                    await wtc.put(w)
            await wtc.stop()
            return to_send

        @sync.consumer
        async def consumer(c):
            async with c:
                return [await rts.get() for _ in to_send]

        pc_result = await asyncio.gather(producer(), consumer())
        logging.info(f"Result: {pc_result}")
        assert pc_result[0] == pc_result[1]

        await rts.stop()


@pytest.mark.asyncio
async def test_WriteableTopicServer_one_message(
    caplog, writeable_topic_server, redeable_topic_client, sync
):
    expected = "hello"
    with caplog.at_level(logging.DEBUG):
        rtc = redeable_topic_client()
        wts = writeable_topic_server()

        await wts.start()

        @sync.producer
        async def producer(c):
            async with c:
                await wts.put(expected)
            return expected

        @sync.consumer
        async def consumer(c):
            await rtc.start()
            async with c:
                result = await rtc.get()
            await rtc.stop()
            return result

        pc_result = await asyncio.gather(producer(), consumer())
        assert pc_result[0] == pc_result[1]

        await wts.stop()


@pytest.mark.asyncio
async def test_WriteableTopicServer_many_messages(
    caplog, writeable_topic_server, redeable_topic_client, sync
):
    to_send = ["hello", "my", "word"]
    with caplog.at_level(logging.DEBUG):
        rtc = redeable_topic_client()
        wts = writeable_topic_server()

        await wts.start()

        @sync.producer
        async def producer(c):
            async with c:
                for w in to_send:
                    await wts.put(w)
            return to_send

        @sync.consumer
        async def consumer(c):
            await rtc.start()
            async with c:
                result = [await rtc.get() for _ in to_send]
            await rtc.stop()
            return result

        pc_result = await asyncio.gather(producer(), consumer())

        logging.info(f"-------------------- {pc_result} ---------------")

        assert pc_result[0] == pc_result[1]

        await wts.stop()


@pytest.mark.asyncio
async def test_one_to_many_same_group(
    caplog, writeable_topic_server, redeable_topic_client, sync
):
    to_send = ["hello", "my", "word", "you", "are", "beatiful"]
    with caplog.at_level(logging.DEBUG):
        wts = writeable_topic_server()
        client_count = 3
        clients = [redeable_topic_client("A") for _ in range(client_count)]

        await wts.start()

        @sync.producer
        async def producer(c):
            async with c:
                for w in to_send:
                    await wts.put(w)
            return to_send

        @sync.consumer
        async def consumer(c, rtc):
            await rtc.start()
            async with c:
                result = []
                for i in range(len(to_send) / client_count):
                    result.append(await rtc.get())
                    logging.info(f"------------- {result} -------------")
            await rtc.stop()
            return result

        pc_result = await asyncio.gather(
            producer(), *[consumer(rtc) for rtc in clients]
        )

        logging.info(f"-------------------- {pc_result} ---------------")

        c_result = [i for l in pc_result[1:] for i in l]
        assert len(pc_result[0]) == len(c_result)
        assert set(pc_result[0]) == set(c_result)

        await wts.stop()


@pytest.mark.asyncio
async def test_many_to_one_same_group(
    caplog, writeable_topic_client, redeable_topic_server, sync
):
    to_send = ["hello", "my", "word", "you", "are", "beatiful"]
    with caplog.at_level(logging.DEBUG):
        rts = redeable_topic_server()
        client_count = 3
        clients = [
            writeable_topic_client(group="A") for _ in range(client_count)
        ]

        await rts.start()

        @sync.producer
        async def producer(c, wtc):
            await wtc.start()
            async with c:
                for w in to_send:
                    await wtc.put(w)
            await wtc.stop()
            return to_send

        @sync.consumer
        async def consumer(c):
            async with c:
                result = []
                for e in to_send * 3:
                    item = await rts.get()
                    result.append(item)
                    logging.info(f"------------- {result} -------------")
            return result

        pc_result = await asyncio.gather(
            *[producer(wtc) for wtc in clients],
            consumer(),
        )

        logging.info(f"-------------------- {pc_result} ---------------")

        p_result = sorted([i for l in pc_result[:client_count] for i in l])
        c_result = sorted(pc_result[-1])

        assert p_result == c_result

        await rts.stop()


@pytest.mark.asyncio
async def test_one_to_many_diff_group(
    caplog, writeable_topic_server, redeable_topic_client, sync
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

        @sync.producer
        async def producer(c):
            await asyncio.sleep(1)
            async with c:
                for w in to_send:
                    await wts.put(w)
            return to_send

        @sync.consumer
        async def consumer(c, rtc):
            await rtc.start()
            async with c:
                result = []
                for i in range(len(to_send)):
                    result.append(await rtc.get())
                    logging.info(f"------------- {result} -------------")
            await rtc.stop()
            return result

        pc_result = await asyncio.gather(
            producer(), *[consumer(rtc) for rtc in clients]
        )

        logging.info(f"-------------------- {pc_result} ---------------")

        await wts.stop()
