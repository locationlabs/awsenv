"""
Tests for command line input and output.
"""
from os import environ

from hamcrest import assert_that, is_, equal_to

from awsenv.main import parse_args, to_environment


def test_parse_args_default():
    args = parse_args([])
    assert_that(args.profile, is_(equal_to("default")))


def test_parse_args_custom_default():
    try:
        environ["AWS_DEFAULT_PROFILE"] = "custom"
        args = parse_args([])
        assert_that(args.profile, is_(equal_to("custom")))
    finally:
        del environ["AWS_DEFAULT_PROFILE"]


def test_parse_args_custom():
    args = parse_args(["custom"])
    assert_that(args.profile, is_(equal_to("custom")))


def test_parse_args_custom_env():
    try:
        environ["AWS_PROFILE"] = "custom"
        args = parse_args([])
        assert_that(args.profile, is_(equal_to("custom")))
    finally:
        del environ["AWS_PROFILE"]


def test_to_environment():
    assert_that(
        to_environment(dict(foo="bar", bar=None)),
        is_(equal_to("export foo=bar\nunset bar;")),
    )
