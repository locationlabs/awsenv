"""
Tests for cached session loading.
"""
from contextlib import contextmanager
from os import environ
from time import time

from hamcrest import assert_that, is_, equal_to, none

from awsenv.cache import CachedSession, DEFAULT_SESSION_DURATION


@contextmanager
def envvars(**kwargs):
    environ.update(kwargs)
    try:
        yield
    finally:
        # not trying to restore existing values
        for key in kwargs:
            del environ[key]


def test_cached_session_absent():
    now = time()
    cached_session = CachedSession.from_environment(now=now)
    assert_that(cached_session, is_(none()))


def test_cached_session_missing_argument():
    now = time()
    token, profile = "token", "profile"
    with envvars(AWS_SESSION_TOKEN=token, AWS_PROFILE=profile):
        cached_session = CachedSession.from_environment(now=now)
        assert_that(cached_session, is_(none()))


def test_cached_session_expired():
    now = time() + 2 * DEFAULT_SESSION_DURATION
    name, token, profile = CachedSession.make_name(), "token", "profile"
    with envvars(AWS_SESSION_TOKEN=token, AWS_SESSION_NAME=name, AWS_PROFILE=profile):
        cached_session = CachedSession.from_environment(now=now)
        assert_that(cached_session, is_(none()))


def test_cached_session_valid():
    now = time()
    name, token, profile = CachedSession.make_name(), "token", "profile"
    with envvars(AWS_SESSION_TOKEN=token, AWS_SESSION_NAME=name, AWS_PROFILE=profile):
        cached_session = CachedSession.from_environment(now=now)
        assert_that(cached_session.name, is_(equal_to(name)))
        assert_that(cached_session.token, is_(equal_to(token)))
