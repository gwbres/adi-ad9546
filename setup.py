#! /usr/bin/env python3

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="distutils",
    scripts=[
        "calib.py",
        "distrib.py",
        "irq.py",
        "misc.py",
        "mx-pin.py",
        "power-down.py",
        "profile.py",
        "reset.py",
        "status.py",
    ],
)
