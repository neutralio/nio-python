import unittest
from unittest.mock import MagicMock
from copy import deepcopy

from pynio import Block
from .mock import mock_instance, config, template


class TestBlock(unittest.TestCase):

    def test_block(self):
        b = Block('name', 'type')
        self.assertEqual(b.name, 'name')
        self.assertEqual(b.type, 'type')

    def test_noname(self):
        with self.assertRaises(ValueError):
            Block('', 'type')

    def test_save(self):
        b = Block('name', 'type', config)
        b._instance = mock_instance()
        b._put = MagicMock()
        b.save()
        self.assertTrue(b._put.called)
        self.assertEqual(b._put.call_args[0][0], 'blocks/name')
        self.assertDictEqual(b._put.call_args[0][1],
                                {'name': 'name',
                                'type': 'type',
                                'value': 0})

    def test_copy(self):
        b = Block('name', 'type', {'key': 'value'})
        bcopy = b.copy('newname')
        self.assertDictEqual({
            'name': 'newname',
            'type': 'type',
            'key': 'value'
        }, bcopy.config)
        self.assertDictEqual({
            'name': 'name',
            'type': 'type',
            'key': 'value'
        }, b.config)

        with self.assertRaises(ValueError):
            b.copy('')

    def test_save_with_no_instance(self):
        b = Block('name', 'type')
        b._config = {'key': 'val'}
        b._put = MagicMock()
        with self.assertRaises(Exception) as context:
            b.save()
