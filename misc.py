#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# misc.py: AD9546 miscellaneous features
#################################################################
import sys
import argparse
from ad9546 import *
def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 misc control tool")
    parser.add_argument(
        "bus",
        type=int,
        help="I2C bus (int)",
    )
    parser.add_argument(
        "address",
        type=str,
        help="I2C slv address (hex format)",
    )
    flags = [
        ('temp-thres-high', int, 'Set temperature warning threshold high value'),
        ('temp-thres-low', int, 'Set temperature warning threshold low value'),
    ]
    for (flag, v_type, helper) in flags:
        parser.add_argument(
            "--{}".format(flag), 
            type=v_type,
            help=helper,
        )
    args = parser.parse_args(argv)
    # open device
    dev = AD9546(args.bus, int(args.address, 16))

    if args.temp_thres_high:
        value = int(args.temp_thres_high * pow(2,7))
        write_data(handle, address, 0x2905, value & 0xFF)
        write_data(handle, address, 0x2906, (value & 0xFF00)>>8)
    if args.temp_thres_low:
        value = int(args.temp_thres_high * pow(2,7))
        write_data(handle, address, 0x2903, value & 0xFF)
        write_data(handle, address, 0x2904, (value & 0xFF00)>>8)

if __name__ == "__main__":
    main(sys.argv[1:])
