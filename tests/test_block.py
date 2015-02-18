import unittest
from ..pynio import Block
from unittest.mock import MagicMock, patch

class TestBlock(unittest.TestCase):

        def test_block(self):
            b = Block('name', 'type')
            self.assertEqual(b.name, 'name')
            self.assertEqual(b.type, 'type')

        def test_save(self):
            b = Block('name', 'type')
            b.config = {'key': 'val'}
            b._instance = MagicMock() # Associate with instance but not for real
            b._put = MagicMock()
            b.save()
            self.assertTrue(b._put.called)
            self.assertEqual(b._put.call_args[0][0], 'blocks/name')
            self.assertDictEqual(b._put.call_args[0][1],
                                 {'name': 'name',
                                  'type': 'type',
                                  'key': 'val'})

        def test_save_with_no_instance(self):
            b = Block('name', 'type')
            b.config = {'key': 'val'}
            b._put = MagicMock()
            with self.assertRaises(Exception) as context:
                b.save()
            self.assertTrue('Block is not associated with an instance' in
                            context.exception.args[0])
            self.assertFalse(b._put.called)
