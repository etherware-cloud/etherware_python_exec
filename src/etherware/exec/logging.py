# -*- coding: utf-8 -*-
#
# Logger setup.
#

import logging
import inspect
from typing import Union, Coroutine, Callable

# create logger
logger = logging.getLogger("etherware.python.exec")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()

# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

F = Union[Callable, Coroutine]


def debug(f: F) -> F:
    """
    Decorator which enable debugging info on start and end of functions.
    """
    def inner(self, *args, **kwargs):
        debug_prefix = (
            f"{self.__class__.__name__}[0x{id(self):x}]"
            f":S:{{action}}{f.__name__}"
        )
        logger.debug(
            debug_prefix.format(action="<") + f":args={args} kwargs={kwargs}"
        )
        result = None
        try:
            result = f(self, *args, **kwargs)
        except Exception as e:
            logger.exception(debug_prefix.format(action=">") + f":{e}")
            raise e
        finally:
            logger.debug(debug_prefix.format(action=">") + f":{result}")
        return result

    async def async_inner(self, *args, **kwargs):
        debug_prefix = (
            f"{self.__class__.__name__}[0x{id(self):x}]"
            f":A:{{action}}{f.__name__}"
        )
        logger.debug(
            debug_prefix.format(action="<") + f":args={args} kwargs={kwargs}"
        )
        result = None
        try:
            result = await f(self, *args, **kwargs)
        except Exception as e:
            logger.exception(debug_prefix.format(action=">") + f":{e}")
            raise e
        finally:
            logger.debug(debug_prefix.format(action=">") + f":{result}")
        return result

    if inspect.iscoroutinefunction(f):
        return async_inner
    else:
        return inner
