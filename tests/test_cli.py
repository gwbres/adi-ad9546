#! /usr/bin/env python3
# simply runs *.py -h
# 1) basic syntax issues
# 2) all cli must have an -h helper
import os
def call_cli(script):
    os.system("python3 {} -h".format(script))
def test_all_cli_helper():
    for f in os.listdir("."):
        if f.split(".")[-1] == "py":
            if f == "setup.py":
                continue 
            call_cli(f)
