#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# calib.py
# small script to trigger an AD95xx calibration
# it is required to manually trigger a calibration every time
# the VCO frequency is modified by User.
#################################################################
import sys
import argparse
from ad9546 import *

def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 calibration tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
    )
    flags = [
        ('all',    'Request Sys clock + DPll + APll calibration'),
        ('sysclk', 'Request Sys clock calibration'),
    ]
    for (flag, helper) in flags:
        parser.add_argument(
            "--{}".format(flag),
            action="store_true",
            help=helper,
        )
    args = parser.parse_args(argv)

    dev = AD9546(int(args.bus), int(args.address, 16)) # open device

    dev.write_data(0x2000, 0x00)
    dev.io_update()
    
    value = 0
    if args.sysclk:
        value |= 0x04
    if args.all:
        value |= 0x02
    dev.write_data(0x2000, value)
    dev.io_update()
    
    # [3] clear bits
    if args.sysclk:
        value &= 0xFB
    if args.all:
        value &= 0xFD
    dev.write_data(0x2000, value)
    dev.io_update()

if __name__ == "__main__":
    main(sys.argv[1:])
