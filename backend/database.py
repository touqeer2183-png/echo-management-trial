"""Central SQLite connections and serialized, atomic write transactions."""
import sqlite3
import threading
from contextlib import contextmanager
from . import config
LOCK = threading.RLock()

def connect():
    c = sqlite3.connect(config.DB, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA busy_timeout=20000')
    return c

@contextmanager
def transaction(write=True):
    with LOCK:
        c = connect()
        try:
            c.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()
