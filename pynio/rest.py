import requests
import json
import time
import logging
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
        for _ in range(retry + 1):
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


class RequestError(Exception):
    pass


class Request(object):
    '''Given a REST object, make a request of nio with a bunch of
    error checking'''
    transition = {None, 'starting', 'stopping', 'configuring',
                  'configured'}
    transition_start = {'started', 'stopped'}

    def __init__(self, service, call, retry=5,
                 **kwargs):
        self.done = False
        self.service = service
        try:
            call(timeout=(3, 0.01))  # Connection Timeout, Request timeout
            self.done = True
        except requests.exceptions.Timeout:
            pass  # intended
        except requests.exceptions.ConnectTimeout:
            log.error("Connection failure in init of Response")
            time.sleep(0.5)
            call(timeout=1)

    def complete(self, status,
                 transition=None, transition_start=None,
                 *args, **kwargs):
        '''Complete a request. Allows statuses to be in the transition_start
        until they are no longer in that set. Then it allows statuses
        to be in transition. If it falls outside of these, an error
        is raised'''
        if self.done:
            return True
        transition = transition if transition is not None else self.transition
        transition_start = (transition_start if transition_start is not None
                            else self.transition_start)
        starting = True
        while True:
            for _ in range(5):
                try:
                    s = self.service.status  # ; print('Status:', s)
                    break
                except Exception as E:
                    log.warning("Unhandled exception while getting status:\n",
                                exc_info=True)
                    exc = E
                    time.sleep(1)
                    continue
            else:
                raise exc
            if s == status:
                return True  # got expected status
            elif starting and s in transition_start:
                pass  # object is still starting
            elif s in transition:
                starting = False  # request has been received, in transition
            else:
                raise RequestError("Invalid status: {}, want: {}".
                                   format(s, status))
            time.sleep(0.5)
