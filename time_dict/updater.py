import logging
import time
from datetime import timedelta, datetime
from threading import Thread, Lock, Event
from typing import Any
from collections import namedtuple, OrderedDict

logger = logging.getLogger()
TimedValue = namedtuple('TimedValue', ['time', 'value'])


class Updater(Thread):
    """
    This is a thread class used to update time_dict internal structure
    NOTE: store object should be treated as the highest source of truth
    """
    def __init__(self, store: OrderedDict,
                 lock: Lock, poll_time: float, action_time: timedelta, action, no_delete):
        super().__init__()
        self.store = store
        self.lock = lock
        self.poll_time = poll_time
        self.action_time = action_time
        self.action = action
        self.no_delete = no_delete

        self.active = Event()
        self.exception = None

    def start(self) -> None:
        self.active.set()
        super().start()

    def flush(self):
        with self.lock:
            no_del_store = self.no_delete
            self.no_delete = True
            for key, value in self.store.items():
                self._handle_timed(key, value)
            self.no_delete = no_del_store

    def join(self, *args, **kwargs):
        logger.info('stopping updater thread')
        self.active.clear()
        super().join(*args, **kwargs)

    def run(self):
        try:
            logger.info('updater thread started')
            while self.active.is_set():
                time.sleep(self.poll_time)
                with self.lock:
                    self.check_for_timed_and_process()
        except Exception as e:
            self.exception = e
            if self.lock.locked():
                self.lock.release()

    def check_for_timed_and_process(self):
        now = datetime.now()
        while self.store:
            key, value = self.store.popitem(last=False)
            if self._check_object_timed(value, now):
                self._handle_timed(key, value)
            else:
                # put it back at the end
                self._reinsert(key, value)
                return

    def _check_object_timed(self, object: TimedValue, now: datetime):
        return now - object.time >= self.action_time

    def _handle_timed(self, key: Any, value: TimedValue):
        if self.action:
            self.action(key, value.value)
        if self.no_delete:
            self._reinsert(key, value)

    def _reinsert(self, key: Any, value: TimedValue):
        if key not in self.store:
            self.store[key] = value
            self.store.move_to_end(key)
