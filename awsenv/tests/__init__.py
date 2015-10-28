"""
Helpers for tests.
"""
from contextlib import contextmanager
from os import environ


@contextmanager
def envvars(**kwargs):
    environ.update(kwargs)
    try:
        yield
    finally:
        # not trying to restore existing values
        for key in kwargs:
            del environ[key]
