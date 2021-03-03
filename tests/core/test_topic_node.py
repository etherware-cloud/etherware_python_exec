import pytest
import asyncio
from etherware.exec.logging import logger
from etherware.exec.core.storage import SqliteStorage
from etherware.exec.core.witness import Witness
from etherware.exec.core.moderator import Moderator
from etherware.exec.core.topic_node import TopicNode


@pytest.mark.asyncio
async def test_basic_node():
    with Witness() as witness:
        with Moderator() as moderator:
            node = TopicNode(moderator, SqliteStorage)
            node.add_topic("test 1")
            await node.start()

            assert "test 1" in witness.list_topics()

            await node.stop()
            await node.del_topic("test 1")

        assert witness.list_topics() == []
