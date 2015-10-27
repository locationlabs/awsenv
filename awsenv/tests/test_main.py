"""
"""
from os import environ

from hamcrest import assert_that, is_, equal_to

from awsenv.main import choose_profile, to_environment


def test_choose_profile_default():
    profile = choose_profile()
    assert_that(profile, is_(equal_to("default")))


def test_choose_profile_custom_default():
    try:
        environ["AWS_DEFAULT_PROFILE"] = "custom"
        profile = choose_profile()
        assert_that(profile, is_(equal_to("custom")))
    finally:
        del environ["AWS_DEFAULT_PROFILE"]


def test_choose_profile_custom():
    profile = choose_profile(["custom"])
    assert_that(profile, is_(equal_to("custom")))


def test_choose_profile_custom_env():
    try:
        environ["AWS_PROFILE"] = "custom"
        profile = choose_profile()
        assert_that(profile, is_(equal_to("custom")))
    finally:
        del environ["AWS_PROFILE"]


def test_to_environment():
    assert_that(
        to_environment(dict(foo="bar", bar=None)),
        is_(equal_to("export foo=bar\nunset bar;")),
    )
