from unittest.mock import MagicMock
from pynio import properties


def mock_instance(types):
    instance = MagicMock(spec=[
        'config', 'blocks_types', 'droplog', 'blocks'])
    instance = MagicMock(spec=[
        'config', 'blocks_types', 'droplog', 'blocks'])
    instance.droplog = MagicMock()
    instance.blocks = {}
    instance.blocks_types = {
        'type': properties.TypedDict({'template':
                                        {'type': 'type',
                                        'name': '',
                                        'key': 'std'}})
    }
    return instance
