from copy import deepcopy

from .properties import load_block


class Block(object):
    '''SDK Access to nio Block objects.
    Blocks are units inside of services. They perform functions on incomming
    signals and put the signals out.
    '''

    def __init__(self, name, type, config=None, instance=None):
        if not name:
            raise ValueError("Name cannot be blank")
        self._name = name
        self._type = type
        self._template = None
        self._config = deepcopy(config) or {}
        self._instance = instance
        self._config['name'] = name
        if 'type' in self._config:
            if type != config['type']:
                raise ValueError("Types do not match: {} != {}".format(
                    type, config['type']))
        self._config['type'] = type

    def save(self):
        """ PUTs the block config to nio.

        Will create a new block if one does not exist by this name.
        Otherwise it will update the existing block config.
        """

        if not self._instance:
            raise Exception('Block is not associated with an instance')

        # setup config
        config = self.config
        config['name'] = self._name
        config['type'] = self._type
        # load template and then reload config
        self.template = self._instance.blocks_types[self._type].template
        self.config = config
        # put onto the web
        self._put('blocks/{}'.format(self._name), self.json())
        self._instance.blocks[self._name] = self

    def _put(self, endpoint, config):
        self._instance._put(endpoint, config)

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, value):
        # do type checking later
        self._template = value

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        if self._template is None:
            self._config = value
            return
        config = deepcopy(self._template)
        config.readonly = False
        config.update(value, drop_unknown=True,
                      drop_logger=self._instance.droplog)
        self._config = config

    def json(self):
        if hasattr(self._config, '__basic__'):
            return self._config.__basic__()
        else:
            return self._config

    def _load_template(self, type, value, instance=None):
        '''Set the template with a template gotten from nio'''
        if instance is not None:
            self._instance = instance
        if self._instance is None:
            raise TypeError("Block is not tied to an instance")

        template = load_block(value)
        template.type = type
        template.name = ''
        template.readonly = True
        self._template = template
        self.config = self._config  # reload own config with new template

    def delete(self):
        '''Delete self from instance and services'''
        self._instance._delete('blocks/{}'.format(self._name))
        for s in self._instance.services.values():
            s._remove(self)
        self._instance.blocks.pop(self._name)
        self._instance = None  # make sure it isn't used anymore

    def copy(self, name, instance=None):
        '''return a copy of self, but with a new name and not tied to
        any instance'''
        if not name:
            raise ValueError(name)
        out = deepcopy(self)
        out._instance = instance
        out._name = name
        out.config['name'] = name
        return out

    def in_use(self, instance=None):
        '''returns a dictionary of services that use this block

        If instance is None (default) uses it's own instance
        '''
        if instance is None:
            instance = self._instance

        name = self.name
        return {sname: service for (sname, service) in instance.services.items()
                if service.hasblock(name)}

