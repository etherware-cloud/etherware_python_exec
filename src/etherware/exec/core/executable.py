from collections import ChainMap
from types import ModuleType
from multiprocessing import Process


class Executable:
    def __init__(self, topics, mainloop, optimization, parameters, object):
        self._topics = topics
        self._mainloop_name = mainloop
        self._optimization = optimization or 0
        self._parameters = parameters
        self._object = object
        self._module = ModuleType("executable")
        self._mainloop = None
        self._process = None

    def compile(self):
        self._compiled = compile(
            self._object,
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
        self._mainloop = getattr(self._module, self._mainloop_name)

        return self

    def start(self, **parameters):
        self._process = Process(
            target=self._module.main,
            args=self._topics,
            kwargs=ChainMap(parameters, self._parameters),
        )
        self._process.start()

    def cancel(self):
        self._process.terminate()

    def wait(self):
        self._process.join()
        self._process.close()

    def stop(self):
        self.cancel()
        self.wait()
