from copy import deepcopy
import unittest
from unittest.mock import MagicMock
from pynio.service import Service, Block
from .mock import mock_instance, config, template


class TestBlock():
    def __init__(self, name):
        self.name = name
        self._name = name


class TestService(unittest.TestCase):
    def test_service(self):
        s = Service('name', 'type')
        self.assertEqual(s.name, 'name')
        self.assertEqual(s.type, 'type')

    def test_noname(self):
        with self.assertRaises(ValueError):
            Service('')

    def test_connect(self):
        s = Service('name', 'type')
        s.connect(TestBlock('one'), TestBlock('two'))
        self.assertDictEqual(
            s.config['execution'][1],
            {
                'name': 'one',
                'receivers': ['two']
            }
        )

    def test_connect_one(self):
        s = Service('name', 'type')
        s.connect(TestBlock('one'))
        self.assertEqual(
            s.config['execution'],
            [{'receivers': [], 'name': 'one'}]
        )

    def test_create_block(self):
        s = Service('name', 'type')
        blk = s.create_block('one', 'blk')
        self.assertEqual(
            s.config['execution'],
            [{'receivers': [], 'name': 'one'}]
        )
        self.assertIsInstance(blk, Block)

    def test_create_block_instance(self):
        '''Test create block when there is an instance'''
        instance = mock_instance()
        c = deepcopy(config)
        c['name'] = 'one'
        s = Service('name', instance=instance)
        blk = s.create_block('one', 'type')
        self.assertEqual(
            s.config['execution'],
            [{'receivers': [], 'name': 'one'}]
        )
        self.assertFalse(instance.droplog.called)
        self.assertDictEqual(c, blk.json())
        self.assertIsInstance(blk, Block)
        self.assertIn(blk.name, instance.blocks)
        self.assertIn(blk, instance.blocks.values())

    def test_blocks_property(self):
        instance = mock_instance()
        s = Service('name')
        blk = s.create_block('one', 'type')
        with self.assertRaises(TypeError):
            s.blocks
        instance.add_service(s)
        instance.add_block(blk)
        self.assertIn(blk, s.blocks)
        self.assertNotIn(instance.create_block('two', 'type'), s.blocks)

    def test_connect_one_to_two(self):
        s = Service('name', 'type')
        s.connect(TestBlock('one'), TestBlock('two'))
        s.connect(TestBlock('one'), TestBlock('three'))
        self.assertDictEqual(
            s.config['execution'][1],
            {
                'name': 'one',
                'receivers': ['two', 'three']
            },
        )

    def test_connect_two_to_one(self):
        s = Service('name', 'type')
        s.connect(TestBlock('one'), TestBlock('three'))
        s.connect(TestBlock('two'), TestBlock('three'))
        self.assertDictEqual(
            s.config['execution'][1],
            {
                'name': 'one',
                'receivers': ['three']
            }
        )
        self.assertDictEqual(
            s.config['execution'][2],
            {
                'name': 'two',
                'receivers': ['three']
            }
        )

    def test_connect_one_to_one_to_one(self):
        s = Service('name', 'type')
        s.connect(TestBlock('one'), TestBlock('two'))
        s.connect(TestBlock('two'), TestBlock('three'))
        self.assertDictEqual(
            s.config['execution'][1],
            {
                'name': 'one',
                'receivers': ['two']
            }
        )
        self.assertDictEqual(
            s.config['execution'][0],
            {
                'name': 'two',
                'receivers': ['three']
            }
        )

    def test_command(self):
        s = Service('name', 'type')
        blk = TestBlock('one')
        s.connect(blk, TestBlock('two'))
        s._instance = lambda: None
        mm = MagicMock()
        s._instance._get = mm

        s.command('foo')
        self.assertTrue(mm.called)
        self.assertEqual(mm.call_args[0][0],
                         'services/{}/{}'.format('name', 'foo'))

        mm.called = 0
        s.command('bar', blk)
        self.assertTrue(mm.called)
        self.assertEqual(mm.call_args[0][0],
                         'services/{}/{}/{}'.format('name', 'one', 'bar'))

    def test_remove_block(self):
        s = Service('name')
        blk = TestBlock('one')
        s.connect(blk, TestBlock('two'))
        s.remove_block(blk)
        execution = s.config['execution']
        self.assertListEqual(execution, [
            {'name': 'two', 'receivers': []}
        ])

    def test_str(self):
        ins = mock_instance()
        s = ins.create_service('name')
        b1 = s.create_block('b1', 'type')
        b2 = s.create_block('b2', 'type')
        b3 = s.create_block('b3', 'type')
        s.create_block('b4', 'type')
        s.connect(b1, b2)
        s.connect(b1, b3)
        s.connect(b2, b3)
        str(s)  # verify no error is raised
