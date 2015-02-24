import unittest
from unittest.mock import MagicMock, patch

import requests

from pynio import rest


def mock_response():
    response = MagicMock(spec=['json', 'raise_for_status'])
    response.json = MagicMock()
    # response.raise_for_status = MagicMock()
    return response


class iter_raise:
    def __init__(self, error, times, return_val):
        self.error = error
        self.times = times
        self.count = 0
        self.return_val = return_val

    def __iter__(self):
        return self

    def __next__(self):
        if self.count < self.times:
            self.count += 1
            raise self.error
        return self.return_val


class TestREST(unittest.TestCase):
    @patch('requests.get')
    def test_get(self, get):
        response = mock_response()
        get.return_value = response
        r = rest.REST()
        r._get('end')
        self.assertTrue(get.called)
        self.assertTrue(response.json.called)
        self.assertTrue(response.raise_for_status.called)
        self.assertEqual(get.call_args[0][0], 'http://127.0.0.1:8181/end')

    @patch('time.sleep')
    @patch('requests.get')
    def test_get_retry(self, get, sleep):
        raise_count = 4
        raises = iter_raise(requests.exceptions.ConnectionError,
                            raise_count, None)
        response = mock_response()
        response.raise_for_status = lambda: next(raises)
        get.return_value = response
        r = rest.REST()
        r._get('end', retry=raise_count)
        self.assertTrue(get.called)
        self.assertTrue(response.json.called)
        self.assertEqual(get.call_args[0][0], 'http://127.0.0.1:8181/end')
        self.assertEqual(sleep.call_count, raise_count)

        # make sure it fails when we don't retry enough
        raises.count = 0
        with self.assertRaises(requests.exceptions.ConnectionError):
            r._get('end', retry=raise_count - 1)

    @patch('time.sleep')
    @patch('requests.get')
    def test_raise_wrong(self, get, sleep):
        raise_count = 1
        raises = iter_raise(ZeroDivisionError,
                            raise_count, None)
        response = mock_response()
        response.raise_for_status = lambda: next(raises)
        get.return_value = response
        r = rest.REST()
        with self.assertRaises(ZeroDivisionError):
            r._get('end', retry=raise_count)
