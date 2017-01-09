"""
Test for profile processing.
"""
from contextlib import contextmanager
from mock import patch
from os import environ
from tempfile import NamedTemporaryFile
from textwrap import dedent

from hamcrest import assert_that, equal_to, is_, none

from awsenv.cache import CachedSession, DEFAULT_SESSION_DURATION
from awsenv.profile import AWSProfile


CACHED_SESSION = CachedSession(
    name="name,",
    token="token",
    profile="profile",
)
PROFILE = "custom"
ROLE_ARN = "role_arn"


@contextmanager
def custom_config(profile, role_arn=None):
    """
    Inject a temporary AWS configuration, overriding ~/.aws/config.
    """
    with NamedTemporaryFile() as file_:
        file_.write(dedent("""\
            [default]
            region = us-west-2

            [profile {}]
            {}
            source_profile = default
        """.format(
            profile,
            "role_arn = {}".format(role_arn) if role_arn else "",
        )))
        file_.flush()
        environ["AWS_CONFIG_FILE"] = file_.name
        try:
            yield
        finally:
            del environ["AWS_CONFIG_FILE"]


def test_profile_no_role_arn():
    """
    A profile with no role arn defined will not assume any role.
    """
    with custom_config(profile=PROFILE):
        aws_profile = AWSProfile(
            profile=PROFILE,
            session_duration=DEFAULT_SESSION_DURATION,
            cached_session=None,
        )

        assert_that(aws_profile.role_arn, is_(none()))
        assert_that(aws_profile.cached_session, is_(none()))

        with patch.object(aws_profile, "assume_role") as assume_role:
            # we do not expect a role to be assumed
            aws_profile.update_credentials()
            assert_that(assume_role.call_count, is_(equal_to(0)))
            assert_that(aws_profile.cached_session, is_(none()))

        # session variables are NOT set
        assert_that(aws_profile.to_envvars().get("AWS_SESSION_TOKEN"), is_(none()))
        assert_that(aws_profile.to_envvars().get("AWS_SESSION_NAME"), is_(none()))


def test_profile_role_arn_cached_session():
    """
    A profile with a role arn but a valid cached session will not (re)assume any role.
    """
    with custom_config(profile=PROFILE, role_arn=ROLE_ARN):
        aws_profile = AWSProfile(
            profile=PROFILE,
            cached_session=CACHED_SESSION,
            session_duration=DEFAULT_SESSION_DURATION,
        )

        assert_that(aws_profile.role_arn, is_(equal_to(ROLE_ARN)))
        assert_that(aws_profile.cached_session, is_(equal_to(CACHED_SESSION)))

        with patch.object(aws_profile, "assume_role") as assume_role:
            # we do not expect a role to be assumed
            aws_profile.update_credentials()
            assert_that(assume_role.call_count, is_(equal_to(0)))
            assert_that(aws_profile.cached_session, is_(equal_to(CACHED_SESSION)))

        # session variables are set
        assert_that(
            aws_profile.to_envvars().get("AWS_SESSION_TOKEN"),
            is_(equal_to(CACHED_SESSION.token)),
        )
        assert_that(
            aws_profile.to_envvars().get("AWS_SESSION_NAME"),
            is_(equal_to(CACHED_SESSION.name)),
        )


def test_profile_with_role_arn():
    """
    A profile with a role arn and no cached session will assume the role.
    """
    with custom_config(profile=PROFILE, role_arn=ROLE_ARN):
        aws_profile = AWSProfile(
            profile=PROFILE,
            session_duration=DEFAULT_SESSION_DURATION,
            cached_session=None,
        )
        assert_that(aws_profile.role_arn, is_(equal_to(ROLE_ARN)))
        assert_that(aws_profile.cached_session, is_(none()))

        with patch.object(aws_profile, "assume_role") as assume_role:
            # we do expect a role to be assumed
            def create_cached_session():
                aws_profile.cached_session = CACHED_SESSION
                return "access_key", "secret_key"

            assume_role.side_effect = create_cached_session
            aws_profile.update_credentials()
            assert_that(assume_role.call_count, is_(equal_to(1)))

        # session variables are set
        assert_that(
            aws_profile.to_envvars().get("AWS_SESSION_TOKEN"),
            is_(equal_to(CACHED_SESSION.token)),
        )
        assert_that(
            aws_profile.to_envvars().get("AWS_SESSION_NAME"),
            is_(equal_to(CACHED_SESSION.name)),
        )


def test_profile_region_from_envvar():
    """
    Use AWS_REGION environment variable for region if set.
    """
    with custom_config(profile=PROFILE, role_arn=ROLE_ARN):
        region = 'us-east-2'
        environ['AWS_REGION'] = region
        aws_profile = AWSProfile(
            profile=PROFILE,
            session_duration=DEFAULT_SESSION_DURATION,
            cached_session=None,
        )
        assert_that(aws_profile.region_name, is_(equal_to(region)))
