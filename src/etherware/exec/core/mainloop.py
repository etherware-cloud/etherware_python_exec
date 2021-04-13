# -*- coding: utf-8 -*-
#
# Mainloop.
#

from etherware.exec.core.typing import List, Tuple
from etherware.exec.logging import logger
from .daemon import Daemon
from .moderator import Moderator
from .witness import Witness, NotTopicAvailableError
from .executable import Executable
from aiohttp import web
from functools import partial
from .topic_processor import WriteableTopicClient, ReadableTopicClient
from .storage import MemoryStorage
from .topic_queue import TopicQueue

import asyncio


class IncompleteTopicsToExecuteError(Exception):
    pass


class TopicWrapper:
    TOPIC_ROLE_MAP = {
        'producer': WriteableTopicClient,
        'consumer': ReadableTopicClient,
    }

    def __init__(self, storage_class=None, witness=None, timeout=60):
        self._topics = {}
        self._storage_class = storage_class or MemoryStorage
        self._witness = witness or Witness()
        self._timeout = timeout

    def connect_to_topic_servers(self, topics: List[Tuple[str, Tuple[str, str]]]):
        for topic_alias, (topic_role, topic_name) in topics:
            with self._witness as w:
                try:
                    address = w[topic_name]
                except NotTopicAvailableError:
                    raise IncompleteTopicsToExecuteError
                self._topics[topic_alias] = \
                    self.TOPIC_ROLE_MAP[topic_role](self._storage_class(), topic_alias, address)

    def topics(self):
        return self._topics


async def deployer(
    query_topic: TopicQueue,
    status_topic: TopicQueue,
    exception_topic: TopicQueue,
):
    executables = []

    async for (
        c_id,
        c_verb,
        c_parameters,
        d_topics,
        d_mainloop,
        d_optimization,
        d_parameters,
        e_id,
        e_object,
    ) in query_topic:

        put_status = partial(
            status_topic.put, command_id=c_id, received=c_verb, over=e_id
        )
        # exception_shell =
        # TopicQueueShell(exception_topic, default_data=dict(command_id=c_id, received=c_verb, over=e_id))

        await put_status(message="Assigning Topics")

        topics = TopicWrapper()

        topics.connect_to_topic_servers(d_topics)

        await put_status(message="Building Executables")

        deployed = Executable(topics.topics(), exception_topic, d_mainloop, d_optimization, d_parameters, e_object)
        executables.append(deployed)

        await put_status(message="Starting")
        deployed.start()


class ExecutorMainLoop(Daemon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.moderator = Moderator()
        self.clean = False
        self._connections = 0

    async def handle(self, request):
        # TODO: Share information with requester.
        logger.info("Start connection")
        self._connections += 1

        name = request.match_info.get("name", "Anonymous")
        text = "Hello, " + name
        return web.Response(text=text)

    def setup(self):
        self.moderator.start()

    def cleanup(self, loop):
        logger.info("Cleaning Loop")
        self.moderator.stop()

    async def run(self):
        logger.info("Factoring executor")

        executable_topic = self.moderator.new_consumer_topic("executable")
        deployment_topic = self.moderator.new_consumer_topic("deployment")
        command_topic = self.moderator.new_consumer_topic("command")
        status_topic = self.moderator.new_producer_topic("status")
        exception_topic = self.moderator.new_producer_topic("exception")

        query_topic = self.moderator.new_consumer_query(
            "SELECT command.id, command.verb, deployment.topics,"
            "   deployment.mainloop, executable.id, executable.object"
            " FROM command C"
            " LEFT JOIN deployment D ON D.id = C.deployment_id"
            " LEFT JOIN executable E ON E.id = D.executable_id"
            " WHERE command.id = ?"
            " GROUP BY C.id, D.id, E.id"
            " HAVING MAX(C._timestamp) AND"
            "        MAX(D._timestamp) AND"
            "        MAX(E._timestamp)",
            {
                "executable": executable_topic,
                "deployment": deployment_topic,
                "command": command_topic,
            },
        )

        executor_task = asyncio.create_task(
            deployer(
                query_topic,
                status_topic,
                exception_topic,
            )
        )

        await executor_task

        logger.info("Continue for ever Loop")
