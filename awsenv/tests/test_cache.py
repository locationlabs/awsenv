"""
Cache tests.
"""
from os import environ
from time import time
from uuid import uuid1

from hamcrest import assert_that, is_, equal_to, none

from awsenv.cache import CachedSession, DEFAULT_EXPIRATION


def test_cached_session_absent():
    now = time()
    cached_session = CachedSession.from_environment(now=now)
    assert_that(cached_session, is_(none()))


def test_cached_session_missing_argument():
    now = time()
    token = "token"
    try:
        environ["AWS_SESSION_TOKEN"] = token
        cached_session = CachedSession.from_environment(now=now)
        assert_that(cached_session, is_(none()))
    finally:
        del environ["AWS_SESSION_TOKEN"]


def test_cached_session_expired():
    now = time() + 2 * DEFAULT_EXPIRATION
    name, token = uuid1().hex, "token"
    try:
        environ["AWS_SESSION_NAME"] = name
        environ["AWS_SESSION_TOKEN"] = token
        cached_session = CachedSession.from_environment(now=now)
        assert_that(cached_session, is_(none()))
    finally:
        del environ["AWS_SESSION_NAME"]
        del environ["AWS_SESSION_TOKEN"]


def test_cached_session_valid():
    now = time()
    name, token = uuid1().hex, "token"
    try:
        environ["AWS_SESSION_NAME"] = name
        environ["AWS_SESSION_TOKEN"] = token
        cached_session = CachedSession.from_environment(now=now)
        assert_that(cached_session.name, is_(equal_to(name)))
        assert_that(cached_session.token, is_(equal_to(token)))
    finally:
        del environ["AWS_SESSION_NAME"]
        del environ["AWS_SESSION_TOKEN"]
