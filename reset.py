#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# reset.py: AD9546 reset macros
#################################################################
import sys
import argparse
from ad9546 import *

def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 reset tool")
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
    flags = [
        ('soft', """Performs a soft reset.
        If Mx pins are configured for automated EEPROM download, download gets initiated."""),
        ('sans', 'Performs a soft reset but maintains current registers value.'),
        ('watchdog', 'Resets watchdog timer'),
    ]
    for (flag, helper) in flags:
        parser.add_argument(
            "--{}".format(flag),
            action="store_true",
            help=helper,
        )
    args = parser.parse_args(argv)
    # open device
    dev = AD9546(args.bus, int(args.address, 16))

    if args.soft:
        r = dev.read_data(0x0000)
        r &= 0x7E # clear bits
        dev.write_data(0x0000, r | 0x01 | 0x80)
        dev.write_data(0x0000, r)
    if args.sans:
        r = dev.read_data(0x0001)
        r &= 0xFB # clear bit
        dev.write_data(0x0001, r | 0x04)
        dev.write_data(0x0001, r)
    if args.watchdog:
        r = dev.read_data(0x2005)
        dev.write_data(0x0001, r | 0x80)

if __name__ == "__main__":
    main(sys.argv[1:])
