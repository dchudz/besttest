# sample ./setup.py file
from setuptools import setup

setup(
    name="besttest",
    packages=['besttest'],

    # the following makes a plugin available to pytest
    entry_points={
        'pytest11': [
            'besttest = besttest.plugin',
        ]
    },
    install_requires=[
        # Need the version of pytest-cov in master on Github, so install manually for now.
        # 'pytest_cov',
    ],

    # custom PyPI classifier for pytest plugins
    classifiers=[
        "Framework :: Pytest",
    ],
)
