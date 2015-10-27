"""
Command line entry point.
"""
from argparse import ArgumentParser
from os import environ
from pipes import quote

from awsenv.profile import AWSProfile


def choose_profile(argv=None):
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
    args = parser.parse_args(args=argv)
    return args.profile


def to_environment(variables):
    """
    Print environment variables for a profile.
    """
    return "\n".join(
        "unset {};".format(key) if value is None else "export {}={}".format(key, quote(value))
        for key, value in variables.items()
    )


def main():
    profile = AWSProfile(choose_profile())
    profile.assume_role()
    print to_environment(profile.to_envvars())  # noqa
