from .rest import REST
from .block import Block
from .service import Service
from .progress import ProgressBar


class Instance(REST):
    """ Interface for a running nio instance.
    """

    def __init__(self, host='127.0.0.1', port=8181, creds=None):
        super().__init__(host, port, creds)
        self.reset()

    def reset(self):
        self.blocks = self._get_blocks()
        self.services = self._get_services()

    def nio(self):
        """ Returns nio version info.

        """
        return self._get('nio')

    def add_block(self, block):
        block._instance = self
        block.save()

    def add_service(self, service):
        service._instance = self
        service.save()

    def _get_blocks(self):
        blks = {}
        resp = self._get('blocks')
        for blk in resp:
            blks[blk] = Block(resp[blk].get('name'),
                              resp[blk].get('type'),
                              resp[blk],
                              instance=self)
        return blks

    def _get_services(self):
        services = {}
        resp = self._get('services')
        for s in resp:
            services[s] = Service(resp[s].get('name'),
                                  config=resp[s],
                                  instance=self)
        return services

    def start(self, services):
        '''Start an iterator of services as fast as possible'''
        for s in ProgressBar('Starting:')(services):
            s.start()

    def stop(self, services):
        '''Stop an iterator of services as fast as possible'''
        for s in ProgressBar('Stopping:')(services):
            s.stop()

    def DELETE_ALL(self):
        '''Deletes all blocks and services from an instance
        regardless of whether or not they can be loaded and does
        a reset'''
        blocks, services = self._get('blocks'), self._get('services')
        for b in blocks:
            self._delete('blocks/{}'.format(b))
        for s in services:
            self._get('services/{}/stop'.format(s))
            self._delete('services/{}'.format(s))
        self.reset()
