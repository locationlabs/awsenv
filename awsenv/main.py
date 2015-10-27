"""
Command line entry point.
"""
from argparse import ArgumentParser
from os import environ
from pipes import quote
from sys import argv

from awsenv.cache import CachedSession, DEFAULT_SESSION_DURATION
from awsenv.profile import AWSProfile


def parse_args(args):
    """
    Select the AWS profile to use.

    Defaults to the value of the `AWS_PROFILE` environment variable but
    allows overriding by command line arguments.
    """
    profile = environ.get("AWS_PROFILE", environ.get("AWS_DEFAULT_PROFILE", "default"))

    parser = ArgumentParser()
    parser.add_argument(
        "profile",
        nargs="?",
        default=profile,
    )
    parser.add_argument(
        "--session-duration",
        type=int,
        default=DEFAULT_SESSION_DURATION,
    )
    args = parser.parse_args(args)
    return args


def to_environment(variables):
    """
    Print environment variables for a profile.
    """
    return "\n".join(
        "unset {};".format(key) if value is None else "export {}={}".format(key, quote(value))
        for key, value in variables.items()
    )


def main():
    args = parse_args(argv[1:])
    cached_session = CachedSession.from_environment(
        session_duration=args.session_duration,
    )
    aws_profile = AWSProfile(
        profile=args.profile,
        session_duration=args.session_duration,
        cached_session=cached_session,
    )
    aws_profile.update_credentials()
    print to_environment(aws_profile.to_envvars())  # noqa
