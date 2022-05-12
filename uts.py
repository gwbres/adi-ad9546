#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# uts.py: time stamping units management 
#################################################################
import sys
import argparse
from ad9546 import *
def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 time stamping units control")
    parser.add_argument(
        "bus",
        type=int,
        help="I2C bus (int)",
    )
    parser.add_argument(
        "address",
        type=str,
        help="I2C slv address (hex)",
    )
    parser.add_argument(
        "--type",
        metavar="type",
        choices=["normal","inverse"],
        type=str,
        default="normal",
        help="""Select whether we are addressing a regular Time Stamping unit (default),
        or a inverse Timpe Stamping unit.""",
    )
    
    #for (v_label, v_type, v_choices, v_helper) in flags:
    #    if v_type is None:
    #        parser.add_argument(
    #            "--{}".format(v_label),
    #            action="store_true",
    #            help=v_helper,
    #        )
    #    else:
    #        if len(v_choices) > 0:
    #            parser.add_argument(
    #                "--{}".format(v_label),
    #                choices=v_choices,
    #                type=v_type,
    #                help=v_helper,
    #            )
    #        else:
    #            parser.add_argument(
    #                "--{}".format(v_label),
    #                type=v_type,
    #                help=v_helper,
    #            )
    
    args = parser.parse_args(argv)
    dev = AD9546(args.bus, int(args.address, 16)) # open device
    dev.io_update()

if __name__ == "__main__":
    main(sys.argv[1:])
