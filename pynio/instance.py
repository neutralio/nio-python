from .rest import REST, Request
from .block import Block
from .service import Service
from .progress import ProgressBar


class Instance(REST):
    """ Interface for a running nio instance.
    """
    print_function = print

    def __init__(self, host='127.0.0.1', port=8181, creds=None):
        super().__init__(host, port, creds)
        self.reset()

    def reset(self):
        self.blocks = self._get_blocks()
        self.droplog = print
        self.blocks_types, self.blocks = self._get_blocks()
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
        blocks_types = {}
        for btype, template in self._get('blocks_types').items():
            b = Block(btype, btype, instance=self)
            b._load_template(btype, template)
            blocks_types[btype] = b

        blocks = {}
        for bname, config in self._get('blocks').items():
            btype = config['type']
            b = blocks_types[btype].copy('', instance=self)
            b.config = config
            blocks[bname] = b

        return blocks_types, blocks

    def _get_services(self):
        services = {}
        resp = self._get('services')
        for s in resp:
            services[s] = Service(resp[s].get('name'),
                                  config=resp[s],
                                  instance=self)
        return services

    def create_block(self, name, type, config=None):
        '''Convenience function to create a block and add it to instance'''
        return Block(name, type, config, instance=self)

    def create_service(self, name, type=None, config=None):
        '''Convenience function to create a service and add it to instance'''
        if type is None:
            return Service(name, config=config, instance=self)
        else:
            return Service(name, type, config=config, instance=self)

    def start(self, services):
        '''Start an iterator of services. This is designed to ensure that
        services start as quickly as possible, even under heavy loads'''
        for s in ProgressBar('Starting:', print=self.print_function)(services):
            Request(s, s.start).complete('started')

    def stop(self, services):
        '''Stop an iterator of services as fast as possible'''
        for s in ProgressBar('Stopping:', print=self.print_function)(services):
            s.stop()

    def DELETE_ALL(self):
        '''Deletes all blocks and services from an instance
        regardless of whether or not they can be loaded. Does a reset after
        '''
        blocks, services = self._get('blocks'), self._get('services')
        for b in ProgressBar("Deleting Blocks", print=self.print_function)(
                blocks):
            self._delete('blocks/{}'.format(b))
        for s in ProgressBar("Deleting Services", print=self.print_function)(
                services):
            self._get('services/{}/stop'.format(s))
            self._delete('services/{}'.format(s))
        self.reset()
