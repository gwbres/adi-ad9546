#! /usr/bin/env python3

from distutils.core import setup

setup(name="distutils",
    version="1.0",
    description="Analog Devices (AD9545,46) management tools",
    author="Guillaume W. Bres",
    author_email="guillaume.bressaix@gmail.com",
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
