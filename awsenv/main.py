"""
Command line entry point.
"""
from argparse import ArgumentParser
from os import environ
from pipes import quote
from sys import argv

from awsenv.cache import CachedSession, DEFAULT_SESSION_DURATION
from awsenv.profile import AWSProfile, get_default_profile_name


def get_profile_name():
    """
    Get the profile name forom the environment.
    """
    return environ.get("AWS_PROFILE", get_default_profile_name())


def parse_args(args):
    """
    Select the AWS profile to use.

    Defaults to the value of the `AWS_PROFILE` environment variable but
    allows overriding by command line arguments.
    """
    parser = ArgumentParser()
    parser.add_argument(
        "profile",
        nargs="?",
    )
    parser.add_argument(
        "--session-duration",
        type=int,
        default=DEFAULT_SESSION_DURATION,
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
    )
    args = parser.parse_args(args)
    return args


def to_environment(variables):
    """
    Print environment variables for a profile.
    """
    return "\n".join(
        "unset {};".format(key)
        if variables[key] is None else "export {}={}".format(key, quote(variables[key]))
        for key in sorted(variables)
    )


def get_profile(profile=None,
                session_duration=DEFAULT_SESSION_DURATION,
                assume_role=True,
                refresh=False,
                account_id=None):
    """
    Construct an AWS Profile.

    :param profile: the name of the profile to use; resolves via environment
           variables if not set
    :param session_duration: the session duration (in seconds), defafults to
           one hour, which is also the maximum
    :param assume_role: control whether the given profile's role will be assumed;
           if not, the default profile's credentials will be used
    """
    # choose the profile name if necessary
    if profile is None:
        profile = get_profile_name()

    # look for a cached session in the environment
    cached_session = CachedSession.from_environment(
        session_duration=session_duration,
    ) if assume_role and not refresh else None

    # then load the profile, updating credentials based on the cached session and/or assumed role
    aws_profile = AWSProfile(
        profile=profile,
        session_duration=session_duration,
        cached_session=cached_session,
        account_id=account_id,
    )
    if assume_role:
        aws_profile.update_credentials()

    return aws_profile


def main():
    args = parse_args(argv[1:])
    profile = get_profile(
        profile=args.profile,
        session_duration=args.session_duration,
        refresh=args.refresh,
    )
    print to_environment(profile.to_envvars())  # noqa
