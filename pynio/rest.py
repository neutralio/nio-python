import logging
import json
import time

import requests

log = logging.getLogger(__name__)


class REST(object):
    '''Object for making it easier to communicate with a rest object.
    Stores host, port and credential information and uses it automatically.
    '''
    def __init__(self, host='127.0.0.1', port=8181, creds=None):
        self._host = host
        self._port = port
        self._creds = creds or ('User', 'User')
        self._url = 'http://{}:{}/{}'.format(host, port, '{}')

    def _get(self, endpoint, timeout=None, data=None, retry=0):
        '''Performs a get with some amounts of retrys'''
        if data is not None:
            data = json.dumps(data)
        for i in range(retry + 1):
            try:
                r = requests.get(self._url.format(endpoint),
                                 auth=self._creds,
                                 timeout=timeout,
                                 data=data)
                r.raise_for_status()
                break
            except requests.exceptions.ConnectionError as e:
                log.warning("Failure connecting in _get")
                E = e
                if i < retry:
                    time.sleep(1)
        else:
            raise E
        return r.json()

    def _put(self, endpoint, config=None, timeout=None):
        config = config or {}
        r = requests.put(self._url.format(endpoint),
                         auth=self._creds,
                         data=json.dumps(config),
                         timeout=timeout)
        r.raise_for_status()

    def _delete(self, endpoint, timeout=None):
        r = requests.delete(self._url.format(endpoint), auth=self._creds,
                            timeout=timeout)
        r.raise_for_status()
        return r

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        raise TypeError('Create a new Instance for a new host')

    @property
    def port(self):
        return self._port
