import unittest
from ..pynio import Instance
from unittest.mock import MagicMock, patch

class TestInstance(unittest.TestCase):

        @patch.object(Instance, '_get_blocks')
        @patch.object(Instance, '_get_services')
        def test_instance(self, blks, srvs):
            i = Instance()
            self.assertEqual(i.host, '127.0.0.1')
            self.assertEqual(i.port, 8181)
