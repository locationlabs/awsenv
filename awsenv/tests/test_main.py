"""
Tests for command line input and output.
"""
from hamcrest import assert_that, equal_to, is_, none

from awsenv.cache import DEFAULT_SESSION_DURATION
from awsenv.main import get_profile_name, parse_args, to_environment
from awsenv.tests import envvars


def test_get_profile_name_default():
    assert_that(get_profile_name(), is_(equal_to("default")))


def test_get_profile_name_custom_profile():
    with envvars(AWS_PROFILE="custom"):
        assert_that(get_profile_name(), is_(equal_to("custom")))


def test_get_profile_name_custom_default_profile():
    with envvars(AWS_DEFAULT_PROFILE="custom"):
        assert_that(get_profile_name(), is_(equal_to("custom")))


def test_get_profile_name_custom_profile_and_default_profile():
    with envvars(AWS_PROFILE="custom", AWS_DEFAULT_PROFILE="other"):
        assert_that(get_profile_name(), is_(equal_to("custom")))


def test_parse_args_none():
    args = parse_args([])
    assert_that(args.profile, is_(none()))
    assert_that(args.session_duration, is_(DEFAULT_SESSION_DURATION))


def test_parse_args_custom_profile():
    args = parse_args(["custom"])
    assert_that(args.profile, is_(equal_to("custom")))
    assert_that(args.session_duration, is_(DEFAULT_SESSION_DURATION))


def test_parse_args_custom_session_duration():
    args = parse_args(["--session-duration", "100"])
    assert_that(args.profile, is_(none()))
    assert_that(args.session_duration, is_(100))


def test_to_environment():
    assert_that(
        to_environment(dict(foo="bar", bar=None)),
        is_(equal_to("export foo=bar\nunset bar;")),
    )
