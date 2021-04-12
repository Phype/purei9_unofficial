import sys
import logging

LOGGER = logging.getLogger(__name__)

def log(lvl, msg):
    global LOGGER
    
    if lvl in ["!"]:
        LOGGER.error(lvl + " " + msg)
    else:
        LOGGER.debug(lvl + " " + msg)
