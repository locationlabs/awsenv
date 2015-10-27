"""
Command line entry point.
"""
from argparse import ArgumentParser
from os import environ
from pipes import quote

from awsenv.profile import AWSProfile


def choose_profile():
    """
    Select the AWS profile to use.

    Defaults to the value of the `AWS_PROFILE` environment variable but
    allows overriding by command line arguments.
    """
    profile = environ.get("AWS_PROFILE")

    parser = ArgumentParser()
    parser.add_argument(
        "profile",
        nargs="?",
        default=profile,
    )
    args = parser.parse_args()
    return AWSProfile(args.profile)


def to_environment(profile):
    """
    Print environment variables for a profile.
    """
    return "\n".join(
        "unset {};".format(key) if value is None else "export {}={}".format(key, quote(value))
        for key, value in profile.to_envvars().items()
    )


def main():
    profile = choose_profile()
    profile.assume_role()
    print to_environment(profile)  # noqa
