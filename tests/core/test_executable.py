import time
from multiprocessing import Queue
from etherware.exec.core.executable import Executable


def test_executable_simple():
    t = Queue()
    e = Executable(
        {"a": t},
        "main",
        0,
        {},
        """
def main(a):
    a.put(1)
""",
    )
    e.compile()
    e.setup()
    e.start()
    e.wait()

    assert t.get() == 1


def test_executable_raise_exception():
    e_q = Queue()
    t = Queue()
    e = Executable(
        {"a": t, "__exception_topic__": e_q},
        "main",
        0,
        {},
        """
def main(a):
    a.put(1)
    y = x
""",
    )
    e.compile()
    e.setup()
    e.start()
    e.wait()

    assert t.get() == 1
    assert isinstance(e_q.get(), NameError)


def test_executable_simple_parameter():
    t = Queue()
    e = Executable(
        {"a": t},
        "main",
        0,
        {"r": 2},
        """
def main(a, r=1):
    a.put(r)
""",
    )
    e.compile()
    e.setup()
    e.start(r=2)
    e.wait()

    assert t.get() == 2


def test_executable_overwrite_parameter():
    t = Queue()
    e = Executable(
        {"a": t},
        "main",
        0,
        {"r": 2},
        """
def main(a, r=1):
    a.put(r)
""",
    )
    e.compile()
    e.setup()
    e.start(r=3)
    e.wait()

    assert t.get() == 3


def test_executable_infinite_loop():
    t = Queue()
    e = Executable(
        {"a": t},
        "main",
        0,
        {},
        """
import asyncio as asy

async def loop(a):
    c = 0
    while True:
        a.put(c)
        c += 1

def main(a):
    asy.run(loop(a))
""",
    )
    e.compile()
    e.setup()
    e.start()
    time.sleep(0.5)
    e.stop()

    r = []
    while not t.empty():
        r.append(t.get())

    assert min(r) == 0
    assert max(r) > 0
