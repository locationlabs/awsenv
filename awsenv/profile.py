"""
Profile-aware session wrapper.
"""
from os import environ

from botocore.exceptions import ProfileNotFound
from botocore.session import Session

from awsenv.cache import CachedSession


def get_default_profile_name():
    """
    Get the default profile name from the environment.
    """
    return environ.get("AWS_DEFAULT_PROFILE", "default")


class AWSSession(object):
    """
    AWS session wrapper.
    """
    def __init__(self, profile=None):
        self.profile = profile
        self.session = Session(profile=self.profile)

    @property
    def access_key_id(self):
        return None

    @property
    def secret_access_key(self):
        return None

    @property
    def region_name(self):
        return environ.get("AWS_REGION", environ.get("AWS_DEFAULT_REGION", "us-west-2"))

    @property
    def session_token(self):
        return None

    def create_client(self,
                      service_name,
                      api_version=None,
                      use_ssl=True,
                      verify=None,
                      endpoint_url=None,
                      config=None):
        """
        Create a service from the wrapped session.

        Automatically populates the region name, access key, secret key, and session token.
        Allows other parameters to be passed.
        """
        return self.session.create_client(
            service_name=service_name,
            region_name=self.region_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token,
            api_version=api_version,
            use_ssl=use_ssl,
            verify=verify,
            endpoint_url=endpoint_url,
            config=config,
        )


class AWSProfile(AWSSession):
    """
    AWS profile configuration.
    """
    def __init__(self,
                 profile,
                 session_duration,
                 cached_session,
                 account_id=None):
        """
        Configure a session for a profile.

        :param profile: the name of the profile to use, if any
        :param session_duration: the duration of the session (in seconds)
               must be in the range 900-3600
        :param cached_session: the cached session to use, if any
        :param account_id: the account id for profile auto-generation (if any)
        """
        self.session_duration = session_duration
        self.cached_session = cached_session
        self.account_id = account_id
        super(AWSProfile, self).__init__(profile)

    @property
    def access_key_id(self):
        return self.merged_config.get("aws_access_key_id")

    @property
    def secret_access_key(self):
        return self.merged_config.get("aws_secret_access_key")

    @property
    def region_name(self):
        return self.merged_config.get("region")

    @property
    def role_arn(self):
        return self.profile_config.get("role_arn")

    @property
    def session_token(self):
        return self.cached_session.token if self.cached_session else None

    @property
    def session_name(self):
        return self.cached_session.name if self.cached_session else None

    @property
    def profile_config(self):
        """
        Return the loaded configuration for the profile.
        """
        try:
            return self.session.get_scoped_config()
        except ProfileNotFound:
            if self.account_id is None:
                raise
            # attempt to generate the profile configuration
            self.session._profile_map[self.profile] = dict(
                role_arn="arn:aws:iam::{}:role/{}".format(
                    self.account_id,
                    self.profile,
                ),
                source_profile=get_default_profile_name(),
            )
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

        # Override with AWS_REGION environment variable
        region_from_envvar = environ.get("AWS_REGION")
        if region_from_envvar:
            result.update(region=region_from_envvar)

        return result

    def to_envvars(self):
        return {
            "AWS_ACCESS_KEY_ID": self.access_key_id,
            "AWS_DEFAULT_REGION": self.region_name,
            "AWS_PROFILE": self.profile,
            "AWS_SECRET_ACCESS_KEY": self.secret_access_key,
            "AWS_SESSION_NAME": self.session_name,
            "AWS_SESSION_TOKEN": self.session_token,
        }

    def update_credentials(self):
        """
        Update the profile's credentials by assuming a role, if necessary.
        """
        if not self.role_arn:
            return

        if self.cached_session is not None:
            # use current role
            access_key, secret_key = self.current_role()
        else:
            # assume role to get a new token
            access_key, secret_key = self.assume_role()

        if access_key and secret_key:
            self.session.set_credentials(
                access_key=access_key,
                secret_key=secret_key,
                token=self.cached_session.token if self.cached_session else None,
            )

    def current_role(self):
        """
        Load credentials for the current role.
        """
        return (
            environ.get("AWS_ACCESS_KEY_ID", self.access_key_id),
            environ.get("AWS_SECRET_ACCESS_KEY", self.secret_access_key),
        )

    def assume_role(self):
        """
        Assume a role.
        """
        # we need to pass in the regions and keys because botocore does not
        # automatically merge configuration from the source_profile
        sts_client = self.session.create_client(
            service_name="sts",
            region_name=self.region_name,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )

        session_name = CachedSession.make_name()
        result = sts_client.assume_role(**{
            "RoleArn": self.role_arn,
            "RoleSessionName": session_name,
            "DurationSeconds": self.session_duration,
        })

        # update the cached session
        self.cached_session = CachedSession(
            name=session_name,
            token=result["Credentials"]["SessionToken"],
            profile=self.profile,
        )
        return (
            result["Credentials"]["AccessKeyId"],
            result["Credentials"]["SecretAccessKey"],
        )
