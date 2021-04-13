from typing import Optional, NewType, List, Union, Tuple, Dict, Any, AnyStr, TypeVar, Generic, Type
from types import TracebackType

from asyncio.selector_events import BaseSelectorEventLoop
from asyncio.queues import Queue
from pathlib import Path
from .topic_queue import TopicQueue

NullablePath = Optional[Path]
EventLoop = NewType("EventLoop", BaseSelectorEventLoop)
TopicType = Union[Queue, TopicQueue]
TopicDict = Dict[str, TopicType]

__all__ = ["NullablePath", "EventLoop", "Optional", "List", "TypeVar", "Generic", "Type",
           "Union", "Tuple", "TopicDict", "Any", "AnyStr", "TopicType", "TracebackType"]
