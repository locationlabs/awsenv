"""
Profile-aware session wrapper.
"""
from botocore.session import Session

from awsenv.cache import CachedSession


class AWSProfile(object):
    """
    AWS profile configuration.
    """
    def __init__(self,
                 profile,
                 session_duration,
                 cached_session):
        self.profile = profile
        self.session_duration = session_duration
        self.cached_session = cached_session
        self.session = Session(profile=self.profile)

    def create_client(self,
                      service_name,
                      api_version=None,
                      use_ssl=True,
                      verify=None,
                      endpoint_url=None,
                      config=None):
        """
        Create a service from this profile's session.

        Automatically populates the region name, access key, secret key, and session token
        from the loaded profile. Allows other parameters to be passed.
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
            # use cached token
            access_key, secret_key = self.access_key_id, self.secret_access_key
        else:
            # assume role to get a new token
            access_key, secret_key = self.assume_role()

        self.session.set_credentials(
            access_key=access_key,
            secret_key=secret_key,
            token=self.cached_session.token if self.cached_session else None,
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
