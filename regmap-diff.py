#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# regmap-diff.py: regmap differentiator 
#################################################################
import sys
import json
import argparse

def main (argv):
    parser = argparse.ArgumentParser(description="diff two register map (loaded & extracted)")
    parser.add_argument(
        "loaded",
        metavar="loaded",
        type=str,
        help="Loaded regmap from official A&D tools")
    parser.add_argument(
        "dumped",
        metavar="dumped",
        type=str,
        help="Extracted regmap with regmap.py --dump operation")
    args = parser.parse_args(argv)

    with open(args.loaded, encoding="utf-8-sig") as fd:
        ad_official = json.load(fd)["RegisterMap"]
    with open(args.dumped, encoding="utf-8-sig") as fd:
        dumped = json.load(fd)["RegisterMap"]
    for k in ad_official.keys():
        expected = ad_official[k]
        if dumped[k] != expected:
            print("reg {} - expected {} - {}".format(k, expected, dumped[k]))
if __name__ == "__main__":
    main(sys.argv[1:])
