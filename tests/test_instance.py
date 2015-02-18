import unittest
from ..pynio import Instance
from unittest.mock import MagicMock, patch


class TestInstance(unittest.TestCase):

        @patch.object(Instance, '_get_services')
        @patch.object(Instance, '_get_blocks')
        def test_instance(self, blks, servs):
            blks.return_value = (None, None)
            i = Instance()
            self.assertEqual(i.host, '127.0.0.1')
            self.assertEqual(i.port, 8181)

        # TODO: Create a test that loads system settings
