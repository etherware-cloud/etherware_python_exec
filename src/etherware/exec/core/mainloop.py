# -*- coding: utf-8 -*-
#
# Mainloop.
#

from etherware.exec.logging import logger
from pathlib import Path
from .daemon import Daemon
from .defaults import ENVIRONMENTS, DEFAULT_ENVIRONMENT
from .moderator import Moderator
from .storage import SqliteStorage
from .executable import Executable
from aiohttp import web
from functools import partial

import asyncio


async def deployer(
    query_topic,
    status_topic,
    exception_topic,
):
    executables = []

    for (
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
        put_exception = partial(
            exception_topic.put, command_id=c_id, received=c_verb, over=e_id
        )

        put_status(message="Asigning Topics")
        moderator = Moderator()

        topics = {
            topic_alias: moderator.get_topic(topic_role, topic_name)
            for topic_alias, (topic_role, topic_name) in d_topics
        }

        put_status(message="Building Executables")

        executables.append(Executable(topics, "deployer", None, {}, deployer))

        put_status(message="Starting")

        exec.start()


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

        executable_topic = self.moderator.new_consumer_topic("executable")
        deployment_topic = self.moderator.new_consumer_topic("deployment")
        command_topic = self.moderator.new_consumer_topic("command")
        status_topic = self.moderator.new_producer_topic("status")
        exception_topic = self.moderator.new_producer_topic("exception")

        query_topic = self.moderator.new_consumer_query(
            "SELECT command.id, command.verb, deployment.topics, deployment.mainloop, executable.id, executable.object"
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
            executor(
                query_topic,
                status_topic,
                exception_topic,
            )
        )

        await executor_task

        logger.info("Continue for ever Loop")
