from asyncio.selector_events import BaseSelectorEventLoop
from pathlib import Path
from typing import Optional, NewType, List, Union, Tuple, Dict, Any, AnyStr

NullablePath = Optional[Path]
EventLoop = NewType("EventLoop", BaseSelectorEventLoop)
TopicDict = Dict[str, Any]

__all__ = ["NullablePath", "EventLoop", "Optional", "List", "Union", "Tuple", "TopicDict", "AnyStr"]
