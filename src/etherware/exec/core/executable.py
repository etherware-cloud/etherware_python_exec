from etherware.exec.core.types import TopicDict, AnyStr
from collections import ChainMap
from types import ModuleType
from multiprocessing import Process


class NotMainModuleFoundError(Exception):
    pass


class Executable:
    def __init__(self,
                 topics: TopicDict,
                 mainloop_name: str,
                 optimization: int,
                 parameters: dict,
                 object_code: AnyStr):
        self._topics = topics
        self._optimization = optimization or 0
        self._mainloop_name = mainloop_name
        self._parameters = parameters
        self._object = object_code
        self._module = ModuleType("executable")
        self._mainloop = None
        self._process = None
        self._compiled = None

    def compile(self):
        self._compiled = compile(
            f"""
{self._object}

def __main__(*args, __exception_topic__=None, **kwargs):
    try:
        {self._mainloop_name}(*args, **kwargs)
    except Exception as e:
        __exception_topic__.put(e)
            """,
            "<string>",
            "exec",
            dont_inherit=True,
            optimize=self._optimization,
        )
        return self

    def setup(self):
        # Retrieve local instances
        exec(self._compiled, {}, self._module.__dict__)
        # Convert local instances to global instances
        exec(self._compiled, self._module.__dict__, self._module.__dict__)
        # Retrieve main loop
        self._mainloop = getattr(self._module, "__main__")

        return self

    def start(self, **parameters) -> None:
        main = getattr(self._module, "__main__")
        if main:
            self._process = Process(
                target=main,
                kwargs=ChainMap(self._topics, parameters, self._parameters),
            )
            self._process.start()
        else:
            raise NotMainModuleFoundError

    def cancel(self) -> None:
        self._process.terminate()

    def wait(self) -> None:
        self._process.join()
        self._process.close()

    def stop(self) -> None:
        self.cancel()
        self.wait()
