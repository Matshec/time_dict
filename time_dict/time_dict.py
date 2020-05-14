import logging
import os
from threading import Lock
from datetime import timedelta, datetime
from collections import namedtuple
from typing import Callable, Any
from time_dict.updater import Updater

logger = logging.getLogger()
TimedKey = namedtuple('TimedKey', ['time', 'key'])


class TimeDict:
    """
    This class represents self-updating structure that is able to handle updating and removing object based on age.
    Objects added to this structure are assigned timestamp at insertion, then when age of object is exceeded optional
    action function is called and object is removed from the structure.

    NOTE: why you are using this structure you must explicitly delete it due to thread locking either by
    calling destroy() method or deleting it as del d  or the interpreter will hang at exit

    EXAMPLE USAGE:
        cache = TimeDict(action_time=2, poll_time=0.5)
        key = '1'
        cache[key] = 1
        key in cache
        del cache

    Main parameters are:
        action_time - which specifies age in second at which objects should be deleted - time when actions should
                      be performed and object will be deleted from structure
        poll_time - frequency in seconds of polling the objects for age timeout,
                    experimentally should be around 1/4 of the action_time or less. Please not that too frequent polling
                    may negatively affect you application performance
        action - function that is called on object age timeout. Signature is 'fn(key:Any, value:Any) -> None'

    Class PARTIALLY  implements dictionary interface, implementations allows for:

    d = TimeDict(action_time=2, poll_time=0.5)
    insertion:
        d[key] = value
    updating:
        NOTE: updating only changes the value, age remains unchanged
        d[key] = value
    deletion:
        del d[key]
    testing for membership:
        key in d
    checking length:
        len(d)

    Rest of the dictionary interface is not implements by design.

    """

    def __init__(self, action_time: float, poll_time: float, action: Callable[[Any, Any], None] = None,
                 no_delete=False):
        """
        Updating structure only updates the value but not the time-original insertion time is considered
        destroy method must be called remove this struct or it causes interpreter hangup at exit
        poll time should be around 1/4 of action time or less, to frequent polling is not recommened due to frequent
        mutex locking
        :param action_time: is the age in seconds of object has to be (since insertion) for action to be taken
        :param poll_time: is the frequency with which data will polled to check for timeouts,  value is in seconds
        :param action: action to be taken on object passing defined age - default is delete the object
                should be function that takes key, value as param and has no return value
                - `def action(key, value) ->None`
        :param no_delete: do not delete object after action() fired, default is False
        """
        self.data = {}
        self.lock = Lock()
        self.time_list = []
        action_time = timedelta(seconds=action_time)
        self.updater = Updater(self.data, self.time_list, self.lock, poll_time, action_time, action, no_delete)
        self.updater.start()

    def _check_exception(self):
        """
        Check if updater thread is working, if not re raise exception
        :raises Exception
        """
        if self.updater.exception:
            raise self.updater.exception

    def clear(self) -> None:
        """
        Safely clear all data in the structure
        :raises Exception
        """
        self._check_exception()
        with self.lock:
            self.time_list.clear()
            self.data.clear()

    def flush(self) -> None:
        """
        Flush all the objects by calling the action function, does not remove objects
        Does not respect object age, calls action method on all objects
        :raises Exception if updated thread died
        """
        self._check_exception()
        self.updater.flush()

    def destroy(self) -> None:
        """
        Destroys the structure, must be called to properly deinitialize it
        """
        self.updater.active.clear()
        self.updater.join()

    def __setitem__(self, key, value) -> None:
        """
        Set or update item. Age of the objects is calculated since the insertion, updating the objects does not change
        its age
        :param key: dict key
        :param value: dict value
        :raises Exception if updated thread died
        """
        self._check_exception()
        with self.lock:
            if key not in self.data:
                tv = TimedKey(datetime.now(), key)
                self.time_list.append(tv)
            self.data[key] = value

    def __len__(self) -> int:
        """
        Number of objects in the structure
        :return: number of objects int the structure
        """
        with self.lock:
            return len(self.data)

    def __getitem__(self, key) -> Any:
        """
        Get item, does not remove item
        :param key: dict key
        :return: item
        :raises KeyError, Exception - if updated thread died
        """
        self._check_exception()
        with self.lock:
            return self.data[key]

    def __contains__(self, key):
        """Check if item is in the structure"""
        self._check_exception()
        with self.lock:
            return key in self.data

    def __delitem__(self, key):
        """
        Delete item from structure with `del`
        This is slow operation - O(n)"""
        self._check_exception()
        with self.lock:
            value_index = [i for i, v in enumerate(self.time_list) if v.key == key].pop()
            del self.time_list[value_index]
            del self.data[key]

    def __repr__(self):
        return self.data.__repr__() + os.linesep + self.time_list.__repr__()

    def __del__(self):
        """
        Object needs to be explicitly deleted to join updater thread
        """
        self.destroy()
        self.updater.join()

