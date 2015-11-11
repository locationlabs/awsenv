#!/usr/bin/env python

from setuptools import setup, find_packages

__version__ = "1.10"

setup(
    name="awsenv",
    version=__version__,
    description="AWS profile and session management from the CLI",
    author="Location Labs",
    author_email="info@locationlabs.com",
    url="http://locationlabs.com",
    packages=find_packages(exclude=["*.tests"]),
    setup_requires=[
        "nose>=1.3.7"
    ],
    install_requires=[
        "botocore>=1.3.1",
    ],
    tests_require=[
        "PyHamcrest>=1.8.5",
        "mock>=1.0.1",
        "coverage>=4.0.1",
    ],
    test_suite="awsenv.tests",
    entry_points={
        "console_scripts": [
            "awsenv = awsenv.main:main",
        ]
    }
)
