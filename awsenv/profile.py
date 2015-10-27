"""
Profile-aware session wrapper.
"""
from os import environ
from time import time
from uuid import UUID, uuid1

from botocore.session import Session


def uuid1_to_timestamp(uuid):
    """
    Translate uuid1s to timestamps.
    """
    # http://code.activestate.com/recipe/576420/
    # 0x01b21dd213814000 is the number of 100-ns intervals between the
    # UUID epoch 1582-10-15 00:00:00 and the Unix epoch 1970-01-0100:00:00.
    MAGIC = 0x01b21dd213814000
    unix_timestamp = (UUID(uuid).time - MAGIC) / 1e7
    return unix_timestamp


class AWSProfile(object):
    """
    AWS profile configuration.
    """
    def __init__(self,
                 profile,
                 session_token=None,
                 session_name=None,
                 session_duration=3600):
        self.profile = profile
        self.session = Session(profile=self.profile)
        self.session_name = environ.get("AWS_SESSION_NAME")
        self.session_duration = session_duration

    @property
    def access_key_id(self):
        return self.merged_config.get("aws_access_key_id")

    @property
    def secret_access_key(self):
        return self.merged_config.get("aws_secret_access_key")

    @property
    def session_token(self):
        return self.merged_config.get("aws_session_token")

    @property
    def region_name(self):
        return self.merged_config.get("region")

    @property
    def role_arn(self):
        return self.profile_config.get("role_arn")

    @property
    def profile_config(self):
        """
        Return the loaded configuration for the profile.
        """
        return self.session.get_scoped_config()

    @property
    def source_profile_config(self):
        """
        Return the loaded configuration for the source profile, if any.
        """
        source_profile_name = self.profile_config.get("source_profile")
        all_profiles = self.session.full_config["profiles"]
        return all_profiles.get(source_profile_name, {})

    @property
    def merged_config(self):
        """
        Merged the profile and source configurations along with the current credentials.
        """
        result = self.source_profile_config.copy()
        result.update(self.profile_config)
        if self.session._credentials:
            result.update(
                aws_access_key_id=self.session._credentials.access_key,
                aws_secret_access_key=self.session._credentials.secret_key,
                aws_session_token=self.session._credentials.token,
            )
        return result

    def get_cached_token(self, now=None):
        if "AWS_SESSION_TOKEN" not in environ:
            return None

        if self.session_name is None:
            return None

        if now is None:
            now = time()

        session_timestamp = uuid1_to_timestamp(self.session_name)
        if (session_timestamp + self.session_duration) < now:
            return None

        return environ["AWS_SESSION_TOKEN"]

    def to_envvars(self):
        return {
            "AWS_ACCESS_KEY_ID": self.access_key_id,
            "AWS_DEFAULT_REGION": self.region_name,
            "AWS_PROFILE": self.profile,
            "AWS_SECRET_ACCESS_KEY": self.secret_access_key,
            "AWS_SESSION_NAME": self.session_name,
            "AWS_SESSION_TOKEN": self.session_token,
        }

    def assume_role(self, now=None):
        """
        Assume the profile's role, if any.
        """
        if not self.role_arn:
            return

        cached_token = self.get_cached_token(now)
        if cached_token is not None:
            self.session.set_credentials(
                access_key=self.access_key_id,
                secret_key=self.secret_access_key,
                token=cached_token,
            )
            return

        # generate a UUID for the session name; since uuid1 is time-based,
        # we can avoid regeneration of session tokens before they have expired
        self.session_name = uuid1().hex

        # be sure to pass the merged configuration here if you want
        # to rely on the source_profile property
        sts_client = self.session.create_client(
            service_name="sts",
            region_name=self.region_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

        result = sts_client.assume_role(**{
            "RoleArn": self.role_arn,
            "RoleSessionName": self.session_name,
            "DurationSeconds": self.session_duration,
        })
        self.session.set_credentials(
            access_key=result["Credentials"]["AccessKeyId"],
            secret_key=result["Credentials"]["SecretAccessKey"],
            token=result["Credentials"]["SessionToken"],
        )
