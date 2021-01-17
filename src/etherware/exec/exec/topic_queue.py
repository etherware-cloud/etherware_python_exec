import asyncio
from etherware.exec.logging import logger


class TopicQueue:
    def __init__(self, storage, first=0):
        self._storage = storage
        self._first = first
        self._pointers = {}
        self._ready_cond = {}

    def setup(self, group=None):
        if group not in self._pointers:
            self._pointers[group] = len(self._storage)

    async def put(self, data):
        self._storage.append(data)

        for group, cond in self._ready_cond.items():
            async with cond:
                cond.notify_all()

    def wait_condition(self, local_top):
        def inner():
            next_pos = len(self._storage)
            logger.debug(f"wait_condition {self} {local_top}<{next_pos}")
            return local_top >= 0 and local_top < next_pos

        return inner

    async def get(self, group=None):
        if group not in self._pointers:
            self.setup(group)

        global_top = self._pointers[group]

        if group not in self._ready_cond:
            self._ready_cond[group] = asyncio.Condition()

        async with self._ready_cond[group]:
            await self._ready_cond[group].wait_for(
                self.wait_condition(global_top)
            )
        self._pointers[group] = global_top + 1
        return self._storage[global_top]

    def empty(self, group=None):
        try:
            global_top = self._pointers[group]
            return global_top >= len(self._storage)
        except KeyError:
            return True

    def __str__(self):
        return (
            f"<TopicQueue[0x{id(self):x}] "
            f"_storage={self._storage} "
            f"_first={self._first} "
            f"_pointers={self._pointers} "
            f"_ready_cond={self._ready_cond}>"
        )
