import unittest
from unittest.mock import MagicMock
from ..pynio.service import Service


class TestBlock():
    def __init__(self, name):
        self.name = name
        self._name = name


class TestService(unittest.TestCase):
    def test_service(self):
        s = Service('name', 'type')
        self.assertEqual(s.name, 'name')
        self.assertEqual(s.type, 'type')

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
        s.create_block('one', 'blk')
        self.assertEqual(
            s.config['execution'],
            [{'receivers': [], 'name': 'one'}]
        )

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
