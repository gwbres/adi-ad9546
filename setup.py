#! /usr/bin/env python3

from distutils.core import setup

setup(name="distutils",
    version="1.0",
    description="Analog Devices Clock synthesizers (AD95xx) management tools",
    author="Guillaume W. Bres",
    author_email="guillaume.bressaix@gmail.com",
    scripts=["profile.py"],
)
