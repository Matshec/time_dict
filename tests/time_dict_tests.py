import unittest
import time
from time_dictionary.time_dict import TimeDict
from unittest.mock import Mock


class TimeDictTests(unittest.TestCase):

    TIMEOUT = 1.7
    ACTION_TIME = 1

    def setUp(self) -> None:
        self.dic = TimeDict(action_time=self.ACTION_TIME, poll_time=0.5)

        self.key = 'test_key'
        self.value = 'test_value'

    def tearDown(self) -> None:
        self.dic.destroy()

    def test_add(self):
        self.dic[self.key] = self.value
        self.assertIn(self.key, self.dic)
        time.sleep(self.ACTION_TIME/2)
        self.assertIn(self.key, self.dic)

    def test_in(self):
        self.dic[self.key] = self.value
        self.assertTrue(self.key in self.dic)

    def test_timeout(self):
        # default action is delete on timeout
        self.dic[self.key] = self.value
        time.sleep(self.TIMEOUT)
        self.assertNotIn(self.key, self.dic)

    def test_timeout_multiple(self):
        self.dic[self.key] = self.value
        self.dic['key2'] = 2
        time.sleep(self.TIMEOUT)
        self.dic['key3'] = 3
        self.assertEqual(1, len(self.dic))
        self.assertIn('key3', self.dic)

    def _action(self, a, b):
        self.done = True

    def test_custom_action(self):
        self.done = False
        self.dic = TimeDict(action_time=1, poll_time=0.2, action=self._action)
        self.dic[self.key] = self.value
        time.sleep(self.TIMEOUT)
        self.assertTrue(self.done)
        self.assertNotIn(self.key, self.dic)
        del self.done

    def test_get(self):
        self.dic[self.key] = self.value
        v = self.dic[self.key]
        self.assertEqual(v, self.value)
        time.sleep(self.TIMEOUT)
        with self.assertRaises(KeyError):
            self.dic['nosuchkey']

    def test_user_delete(self):
        self.dic[self.key] = self.value
        del self.dic[self.key]
        self.assertNotIn(self.key, self.dic)

    def test_clear(self):
        self.dic[self.key] = self.value
        self.dic.clear()
        self.assertEqual(0, len(self.dic))

    def test_flush(self):
        fn = Mock()
        self.dic = TimeDict(action_time=2, poll_time=0.5, action=fn)
        self.dic[self.key] = self.value
        self.dic['key1'] = 1
        self.dic.flush()
        self.assertEqual(2, fn.call_count)
        self.assertEqual(2, len(self.dic))

    def _action_raise(self, a, b):
        raise ValueError

    def test_updater_fail(self):
        self.dic = TimeDict(action_time=1, poll_time=0.2, action=self._action_raise)
        self.dic[self.key] = self.value
        time.sleep(self.TIMEOUT)
        with self.assertRaises(ValueError):
            self.dic['key1'] = 1

