"""
Support session caching.

Sessions for assumed roles will persist for up to an hour; we can avoid
calling assume role multiple times if we reuse the same session.
"""
from os import environ
from time import time
from uuid import UUID, uuid1


DEFAULT_SESSION_DURATION = 3600


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


class CachedSession(object):

    def __init__(self, name, token, profile):
        self.name = name
        self.token = token
        self.profile = profile

    @classmethod
    def make_name(cls):
        """
        Generate a UUID1 for the session name.

        Since uuid1 is time-based, we can simultaneusly generate a unique id
        and track expiration.
        """
        return uuid1().hex

    @classmethod
    def from_environment(cls, now=None, session_duration=None):
        """
        Load a session from environment variables.

        Introduces the `AWS_SESSION_NAME` variable to save the session's name.
        """
        envvars = ["AWS_SESSION_NAME", "AWS_SESSION_TOKEN", "AWS_PROFILE"]
        variables = [environ.get(key) for key in envvars]
        if any(variable is None for variable in variables):
            return None

        name, token, profile = variables

        if now is None:
            now = time()

        if session_duration is None:
            session_duration = DEFAULT_SESSION_DURATION

        session_timestamp = uuid1_to_timestamp(name)
        if (session_timestamp + session_duration) < now:
            return None

        return cls(
            name=name,
            token=token,
            profile=profile,
        )
