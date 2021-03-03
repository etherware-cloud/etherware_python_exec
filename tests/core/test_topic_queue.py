import logging
import pytest
import asyncio
from etherware.exec.core.topic_queue import TopicQueue
from etherware.exec.core.storage import MemoryStorage


@pytest.mark.asyncio
async def test_consumer_first(caplog, sync):
    with caplog.at_level(logging.DEBUG):
        messages = ["Hello", "my", "word"]
        tq = TopicQueue(MemoryStorage())

        @sync.producer
        async def producer(c):
            async with c:
                for msg in messages:
                    await tq.put(msg)

        @sync.consumer
        async def consumer(c):
            async with c:
                for m in messages:
                    data = await tq.get()
                    assert data == m

        await asyncio.gather(producer(), consumer())


@pytest.mark.asyncio
async def test_producer_first(caplog, sync):
    with caplog.at_level(logging.DEBUG):
        messages = ["Hello", "my", "word"]
        tq = TopicQueue(MemoryStorage())

        for msg in messages:
            await tq.put(msg)

        @sync.producer
        async def producer(c):
            async with c:
                for msg in messages:
                    await tq.put(msg)

        @sync.consumer
        async def consumer(c):
            async with c:
                for m in messages:
                    logging.debug(f"------ {tq} -----")
                    e = await tq.get()
                    logging.debug(f"------ {e} {m} -----")
                    assert e == m

        await asyncio.gather(producer(), consumer())


@pytest.mark.asyncio
async def test_two_groups(caplog, sync):
    with caplog.at_level(logging.DEBUG):
        messages = ["Hello", "my", "word"]
        tq = TopicQueue(MemoryStorage())

        @sync.producer
        async def producer(c):
            async with c:
                for msg in messages:
                    await tq.put(msg)

        @sync.consumer
        async def consumer(c, group):
            async with c:
                for m in messages:
                    assert await tq.get(group) == m

        await asyncio.gather(producer(), consumer("a"), consumer("b"))
