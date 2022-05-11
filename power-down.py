#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# power-down.py: power down operations for power management
#################################################################
import sys
import argparse
from ad9546 import *
def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 power management tool")
    parser.add_argument(
        "bus",
        type=int,
        help="i2c bus (int)",
    )
    parser.add_argument(
        "address",
        type=str,
        help="i2c slv address (hex format)",
    )
    flags = [
        ('clear', 'Clear (recover from a previous) power down op'), 
        ('all',   'Device power down (Sys clock pll, REFx, DPlls, APlls..)'),
        ('pll0',  'PLL0 core power down'),
        ('pll1',  'PLL1 core power down'),
        ('refb',  'TDC + ref-b power down'),
        ('refbb', 'TDC + ref-bb power down'),
        ('refa',  'TDC + ref-a power down'),
        ('refaa', 'TDC + ref-aa power down'),
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

    if args.all:
        reg = dev.read_data(0x2000)
        if args.clear:
            dev.write_data(0x2000, reg & 0xFE)
        else:
            dev.write_data(0x2000, reg | 0x01)
    else:
        reg = dev.read_data(0x2001)
        if args.refb:
            if args.clear:
                reg &= 0xFB
            else:
                reg |= 0x04
        if args.refbb:
            if args.clear:
                reg &= 0xF7
            else:
                reg |= 0x08
        if args.refa:
            if args.clear:
                reg &= 0xFE
            else:
                reg |= 0x01
        if args.refaa:
            if args.clear:
                reg &= 0xFD
            else:
                reg |= 0x02 
        dev.write_data(0x2000, reg)
        if args.pll0:
            reg = dev.read_data(0x2100)
            if args.clear:
                reg &= 0xFE
            else:
                reg |= 0x01
            dev.write_data(0x2100, reg)
        if args.pll1:
            reg = dev.read_data(0x2200)
            if args.clear:
                reg &= 0xFE
            else:
                reg |= 0x01
            dev.write_data(0x2200, reg)
    dev.io_update()

if __name__ == "__main__":
    main(sys.argv[1:])
