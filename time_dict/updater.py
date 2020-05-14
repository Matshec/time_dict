import logging
import time
from datetime import timedelta, datetime
from threading import Thread, Lock, Event
from typing import Dict, List

logger = logging.getLogger()


class Updater(Thread):
    """
    This is a thread class used to update time_dict internal structure
    NOTE: store object should be treated as the highest source of truth
    """
    def __init__(self, store: Dict, time_store: List,
                 lock: Lock, poll_time: float, action_time: timedelta, action, no_delete):
        super().__init__()
        self.store = store
        self.time_store = time_store
        self.lock = lock
        self.poll_time = poll_time
        self.action_time = action_time
        self.action = action
        self.no_delete = no_delete

        self.active = Event()
        self.removed_elems = 0
        self.exception = None

    def start(self) -> None:
        self.active.set()
        super().start()

    def flush(self):
        with self.lock:
            no_del_store = self.no_delete
            self.no_delete = True
            for tv in self.time_store:
                self._handle_timed(tv)
            self.no_delete = no_del_store

    def join(self, *args, **kwargs):
        logger.info('stopping updater thread')
        self.active.clear()
        super().join(*args, **kwargs)

    def _handle_timed(self, obj):
        value = self.store[obj.key]
        if self.action:
            self.action(obj.key, value)
        if not self.no_delete:
            self.removed_elems += 1
            del self.store[obj.key]

    def _timestore_remove_old(self):
        # make sure last object does not stay
        # varying indexes - store as higher source of truth
        if self.removed_elems > 0:
            self.time_store[:] = self.time_store[self.removed_elems:]
            self.removed_elems = 0
        assert len(self.store) == len(self.time_store), "mismanaged object in store, len varies"

    def run(self):
        try:
            logger.info('updater thread started')
            while self.active.is_set():
                time.sleep(self.poll_time)
                now = datetime.now()
                # TODO better optimize locking
                self.lock.acquire()
                for i, tv in enumerate(self.time_store):
                    if now - tv.time >= self.action_time:
                        self._handle_timed(tv)
                    else:
                        # list should be sorted descending with age of object ( assured by insertion )
                        # so if first or n-th object id not old enough all the following also won't be
                        break
                self._timestore_remove_old()
                self.lock.release()
        except Exception as e:
            self.exception = e
            if self.lock.locked():
                self.lock.release()

