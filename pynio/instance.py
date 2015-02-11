from pynio.api_rest import REST
from pynio.block import Block
from pynio.service import Service


class Instance(REST):
    """ Interface for a running nio instance.

    """

    def __init__(self, host='127.0.0.1', port=8181, creds=None):
        super().__init__(host, port, creds)

        self.blocks = self._get_blocks()
        self.services = self._get_services()

    def nio(self):
        """ Returns nio version info.

        """
        return self._get('nio')

    def add_block(self, block):
        block.save(self)
        # TODO: update self.blocks to include the block

    def add_service(self, service):
        service.save(self)
        # TODO: update self.services to include the service

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
