#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# pll.py: internal DPLL/APLL management
#################################################################
import sys
import argparse
from ad9546 import *
def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 pll control tool")
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
        choices=["digital","analog"],
        type=str,
        help="Select DPLLx or APLLx, where x = channel",
    )
    parser.add_argument(
        "--channel",
        metavar="channel",
        choices=["0","1","all"],
        default="all",
        type=str,
        help="Select which channel (PLLx) to configure. Defaults to `all`. Refer to README",
    )
    flags = [
        ("free-run", None, [], "Force PLLx to free run state"),
        ("holdover", None, [], "Force PLLx to holdover state"),
    ]
    
    for (v_label, v_type, v_choices, v_helper) in flags:
        if v_type is None:
            parser.add_argument(
                "--{}".format(v_label),
                action="store_true",
                help=v_helper,
            )
        else:
            if len(v_choices) > 0:
                parser.add_argument(
                    "--{}".format(v_label),
                    choices=v_choices,
                    type=v_type,
                    help=v_helper,
                )
            else:
                parser.add_argument(
                    "--{}".format(v_label),
                    type=v_type,
                    help=v_helper,
                )
    args = parser.parse_args(argv)
    dev = AD9546(args.bus, int(args.address, 16)) # open device

    if args.free_run:
        if args.channel == 'all' or args.channel == '0':
            r = dev.read_data(0x2105)    
            dev.write_data(0x2105, r | 0x01)
        if args.channel == 'all' or args.channel == '1':
            r = dev.read_data(0x2206)    
            dev.write_data(0x2206, r | 0x01)
    if args.holdover:
        if args.channel == 'all' or args.channel == '0':
            r = dev.read_data(0x2105)    
            dev.write_data(0x2105, r | 0x02)
        if args.channel == 'all' or args.channel == '1':
            r = dev.read_data(0x2206) 
            dev.write_data(0x2206, r | 0x02)
    dev.io_update()

if __name__ == "__main__":
    main(sys.argv[1:])
