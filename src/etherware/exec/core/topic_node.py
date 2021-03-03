from .net import get_ip_address
from .storage import SqliteStorage
from .topic_processor import WriteableTopicServer, RedeableTopicServer


class TopicNode:
    def __init__(self, moderator, storage):
        self._moderator = moderator
        self._storage = storage
        self._topics = {}
        self._topic_counter = {}

    async def loop(self, redeable, writeable):
        while True:
            data = await redeable.get()
            await writeable.put(data)

    def _get_topics(self, topic_name=None):
        return (topic_name and [topic_name]) or self._topics.keys()

    async def start(self, topic_name=None):
        topic_names = self._get_topics(topic_name)

        for topic_name in topic_names:
            await self._topics[topic_name][0].start()
            await self._topics[topic_name][1].start()

    async def stop(self, topic_name=None):
        topic_names = self._get_topics(topic_name)

        for topic_name in topic_names:
            await self._topics[topic_name][0].stop()
            await self._topics[topic_name][1].stop()

    def add_topic(self, topic_name, iface=None):
        if topic_name in self._topics:
            self._topic_counter[topic_name] += 1
            return False

        address = f"http://{get_ip_address(iface or 'lo')}:0"
        storage = self._storage()
        redeable = RedeableTopicServer(storage, topic_name, address)
        writeable = WriteableTopicServer(storage, topic_name,  address)

        self._moderator.publish_topic(
            topic_name,
            redeable.get_address(),
            properties={"role": "producer"},
        )
        self._moderator.publish_topic(
            topic_name,
            writeable.get_address(),
            properties={"role": "consumer"},
        )

        self._topics[topic_name] = (redeable, writeable)
        self._topic_counter[topic_name] = 1
        return True

    async def del_topic(self, topic_name):
        counter = self._topic_counter.get(topic_name, 0)
        if counter > 1:
            self._topic_counter[topic_name] -= 1
            return True
        elif counter == 1:
            self._moderator.unpublish_topic(topic_name)
            await self.stop(topic_name)
            del self._topics[topic_name]
            self._topic_counter[topic_name] = 0
            return True
        else:
            return False

    def sync_topic(self, topic_name):
        raise NotImplementedError

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, type, value, traceback):
        await self.stop()
