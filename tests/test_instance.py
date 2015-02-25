import unittest
from copy import deepcopy

from pynio import Instance, Block, Service
from unittest.mock import MagicMock, patch
from .mock import mock_service, mock_instance, config, template

def assertInstanceEqual(self, in1, in2):
    ser1 = {sname: s.config for (sname, s) in in1.services.items()}
    ser2 = {sname: s.config for (sname, s) in in2.services.items()}
    self.assertDictEqual(ser1, ser2)
    blks1 = {bname: b.json() for (bname, b) in in1.blocks.items()}
    blks2 = {bname: b.json() for (bname, b) in in2.blocks.items()}
    self.assertDictEqual(blks1, blks2)


def assertInstanceNotEqual(self, in1, in2):
    ser1 = {sname: s.config for (sname, s) in in1.services.items()}
    ser2 = {sname: s.config for (sname, s) in in2.services.items()}
    blks1 = {bname: b.json() for (bname, b) in in1.blocks.items()}
    blks2 = {bname: b.json() for (bname, b) in in2.blocks.items()}
    if ser1 == ser2 and blks1 == blks2:
        self.fail()

class MockInstance(Instance):

    def __init__(self, host='127.0.0.1', port=8181, creds=None):
        self._get_blocks = MagicMock()
        self._get_blocks.return_value = {}, {}
        self._get_services = MagicMock()
        self._get_services.return_value = {}
        super().__init__(host, port, creds)


class TestInstance(unittest.TestCase):

    def test_instance(self):
        i = MockInstance()
        self.assertEqual(i.host, '127.0.0.1')
        self.assertEqual(i.port, 8181)

    def test_add_block(self):
        i = MockInstance()
        i.blocks_types = MagicMock()
        i._put = MagicMock()
        name = 'name'
        self.assertTrue(name not in i.blocks)
        i.add_block(Block(name, 'type'))
        self.assertTrue(name in i.blocks)

    def test_add_service(self):
        i = MockInstance()
        i._put = MagicMock()
        name = 'name'
        self.assertTrue(name not in i.services)
        i.add_service(Service(name))
        self.assertTrue(name in i.services)

    def test_delete_all(self, *args):
        names = ['one', 'two', 'three']
        i = MockInstance()
        i._get = MagicMock()
        i._get.return_value = names
        i._delete = MagicMock()

        i.DELETE_ALL()

        delete = ['blocks/{}'.format(n) for n in names]
        delete.extend('services/{}'.format(n) for n in names)
        get = ['blocks', 'services']
        get.extend('services/{}/stop'.format(n) for n in names)

        get_list = i._get.call_args_list
        get_called = [get_list[n][0][0] for n in range(len(get_list))]
        delete_list = i._delete.call_args_list
        delete_called = [delete_list[n][0][0] for
                            n in range(len(delete_list))]

        self.assertEqual(i._get.call_count, 2 + len(names))
        self.assertEqual(i._delete.call_count, len(names) * 2)
        self.assertEqual(get_called, get)
        self.assertEqual(delete_called, delete)

    def test_create_block(self):
        instance = mock_instance()
        blk = instance.create_block('name', 'type')
        self.assertFalse(instance.droplog.called)
        self.assertDictEqual(config, blk.json())
        self.assertIsInstance(blk, Block)
        self.assertIn(blk.name, instance.blocks)
        self.assertIn(blk, instance.blocks.values())

    def test_create_service(self):
        instance = mock_instance()
        service = instance.create_service('name')
        self.assertIsInstance(service, Service)
        self.assertIn(service.name, instance.services)
        self.assertIn(service, instance.services.values())

    def test_clean(self):
        instance = mock_instance()
        s1 = instance.create_service('foo')
        s2 = instance.create_service('bar')

        # make some services, some connected blocks, some non
        bused1 = s1.create_block('bused1', 'type')
        bused2 = s1.create_block('bused2', 'type')
        bused3 = s2.create_block('bused3', 'type')
        s2.connect(bused2, bused3)
        expected = deepcopy(instance)

        # make some non-connected blocks
        notused = []
        for n in range(10):
            notused.append(instance.create_block('bnotused{}'.format(n),
                                                 'type'))
        assertInstanceNotEqual(self, instance, expected)
        instance.clean()
        assertInstanceEqual(self, instance, expected)
