#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Setup script.
# Ref: https://blog.ionelmc.ro/2014/05/25/python-packaging
#

import io
import os


from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import setup, find_namespace_packages


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="etherware.exec",
    version="0.1.dev0",
    author="Cristian S. Rocha",
    author_email="csrocha@gmail.com",
    description="Etherware.cloud python executor",
    long_description=f"{read('README.md')}\n{read('CHANGELOG.md')}",
    long_description_content_type="text/markdown",
    url="https://etherware.cloud/python/",
    packages=find_namespace_packages(where="src", include=["etherware.*"]),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    license="Apache Software License",
    platforms=[],
    install_requires=[
        "click",
        "aiohttp",
        "zeroconf",
    ],
    extras_require={
        "test": ["pytest", "pytest-click", "pytest-asyncio"],
        "docs": ["sphinx"],
    },
    entry_points="""
        [console_scripts]
        python_exec=etherware.exec.cli:cli
    """,
)
