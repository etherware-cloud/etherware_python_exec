import pytest
from time import sleep
from etherware.exec.core import Executable
from etherware.exec.core import Moderator
from etherware.exec.core.storage import SqliteStorage
from etherware.exec.core.topic_node import TopicNode


@pytest.fixture
async def topic_node():
    with Moderator() as moderator:
        node = TopicNode(moderator, SqliteStorage)
        async with node as n:
            return n


@pytest.mark.asyncio
async def test_simple_producer_consumer(topic_node):
    topic_node.add_topic("testing")
    topic_node.add_topic("exception")
    await topic_node.start("testing")
    await topic_node.start("exception")

    source_consumer = """
import asyncio
from itertools import count

async def loop(test_topic):
    for i in count(start=1):
        test_topic.get(i)

def main(test_topic):
    asyncio.run(loop(test_topic))
    """
    executable_consumer = Executable(
        {"test_topic": topic_node.get_readable("testing")},
        topic_node.get_readable("exception"),
        "main",
        0,
        {},
        source_consumer
    )
    executable_consumer.compile().setup()

    source_producer = """
import asyncio
from itertools import count

async def loop(test_topic):
    for i in count(start=1):
        test_topic.put(i)

def main(test_topic):
    asyncio.run(loop(test_topic))
    """
    executable_producer = Executable(
        {"test_topic": topic_node.get_writeable("testing")},
        topic_node.get_readable("exception"),
        "main",
        0,
        {},
        source_producer
    )
    executable_producer.compile().setup()

    executable_consumer.start()
    executable_producer.start()

    sleep(5)

    executable_consumer.stop()
    executable_producer.stop()

    # What do you expect from this test?
