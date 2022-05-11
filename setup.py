#! /usr/bin/env python3

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="adi-ad9546",
    py_modules=["ad9546"],
    scripts=[
        "calib.py",
        "distrib.py",
        "pll.py",
        "irq.py",
        "misc.py",
        "mx-pin.py",
        "power-down.py",
        "ref-input.py",
        "regmap.py",
        "regmap-diff.py",
        "reset.py",
        "status.py",
        "sysclk.py",
    ],
)
