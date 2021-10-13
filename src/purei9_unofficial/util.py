import logging
import time

import requests
import requests.auth

logger = logging.getLogger(__name__)

def do_http(method, url, retries=2, **kwargs):
    try:
        logger.debug("HTTP " + method + " " + url)
        r = requests.request(method, url, timeout=10, **kwargs)
        
        # Hide access tokens from log
        if r.text:
            if "accessToken" in r.text:
                logger.debug("HTTP " + str(r.status_code) + " " + str(r) + " " + "(sensitive data not shown)")
            else:
                logger.debug("HTTP " + str(r.status_code) + " " + str(r) + " " + r.text)
        else:
            logger.debug("HTTP " + str(r.status_code) + " " + str(r) + " " + "-")
        r.raise_for_status()
        return r
    except Exception as r:
        if retries > 0:
            return do_http(method, url, retries-1, **kwargs)
        else:
            logger.error("Giving up due to no left retries. Wrong credentials?")
            raise r
        
class CachedData():
    
    def __init__(self, maxage=5):
        self._mark_changed()
        self._cache_maxage = maxage

    def _mark_changed(self):
        self._cache_data = None
        self._cache_time = time.time()
        
    def _getinfo(self):
        if self._cache_data != None and time.time() - self._cache_time < self._cache_maxage:
            return self._cache_data
        else:
            self._cache_data = self._getinfo_inner()
            self._cache_time = time.time()
            return self._cache_data
