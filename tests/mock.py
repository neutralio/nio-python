from unittest.mock import MagicMock
from pynio import properties

template = {
    'name': 'template',
    'properties': {
        'name': {
            'type': 'str',
            'title': None,
        },
        'type': {
            "type": "str",
            "title": None
        },
        'value': {
            'type': 'int',
            'title': 'Value',
            'default': 0
        }
    }
}

config = {
    'name': 'name',
    'type': 'type',
    'value': 0
}


def mock_instance(type=template):
    instance = MagicMock(spec=[
        'config', 'droplog',
        'blocks', 'blocks_types', 'services',
        '_put'])
    instance.droplog = MagicMock()
    instance._put = MagicMock()
    instance.blocks = {}
    instance.blocks_types = {
        'type': properties.load_block(type)
    }
    return instance
