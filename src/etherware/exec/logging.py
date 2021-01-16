# -*- coding: utf-8 -*-
#
# Logger setup.
#

import logging
import inspect

# create logger
logger = logging.getLogger("etherware.python.exec")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
#ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


def debug(f):
    def inner(self, *args, **kwargs):
        debug_prefix = (
            f"{self.__class__.__name__}[0x{id(self):x}]"
            f":S:{{action}}{f.__name__}"
        )
        logger.debug(
            debug_prefix.format(action="<") + f":args={args} kwargs={kwargs}"
        )
        try:
            result = f(self, *args, **kwargs)
            return result
        except Exception as e:
            logger.exception(debug_prefix.format(action=">") + f":{e}")
            raise e
        else:
            logger.debug(debug_prefix.format(action=">") + f":{result}")

    async def async_inner(self, *args, **kwargs):
        debug_prefix = (
            f"{self.__class__.__name__}[0x{id(self):x}]"
            f":A:{{action}}{f.__name__}"
        )
        logger.debug(
            debug_prefix.format(action="<") + f":args={args} kwargs={kwargs}"
        )
        try:
            result = await f(self, *args, **kwargs)
            return result
        except Exception as e:
            logger.exception(debug_prefix.format(action=">") + f":{e}")
            raise e
        else:
            logger.debug(debug_prefix.format(action=">") + f":{result}")

    if inspect.iscoroutinefunction(f):
        return async_inner
    else:
        return inner
