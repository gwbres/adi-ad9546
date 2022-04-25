#! /usr/bin/env python3

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="adi-ad9546",
    scripts=[
        "calib.py",
        "distrib.py",
        "irq.py",
        "misc.py",
        "mx-pin.py",
        "power-down.py",
        "regmap.py",
        "reset.py",
        "status.py",
    ],
)
