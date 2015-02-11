import requests
import json


class REST(object):
    def __init__(self, host='127.0.0.1', port=8181, creds=None):
        self._host = host
        self._port = port
        self._creds = creds or ('User', 'User')
        self._url = 'http://{}:{}/{}'.format(host, port, '{}')

    def _get(self, endpoint, timeout=None):
        r = requests.get(self._url.format(endpoint),
                         auth=self._creds,
                         timeout=timeout)
        return r.json()

    def _put(self, endpoint, config=None, timeout=None):
        config = config or {}
        r = requests.put(self._url.format(endpoint),
                         auth=self._creds,
                         data=json.dumps(config),
                         timeout=timeout)

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        print('Create a new Instance if you want a new host.')
        pass

    @property
    def port(self):
        return self._port
