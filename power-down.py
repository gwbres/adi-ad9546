#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# power-down.py
# small script to perform power down operations
# Any power down will probably require either a partial
# or a complete recalibration
#################################################################
import sys
import argparse
from smbus import SMBus

def write_data (handle, dev, addr, data):
    lsb = addr & 0xFF
    msb = addr & (0xFF00)>>8
    handle.write_i2c_block_data(dev, msb, [lsb])
def read_data (handle, dev, addr):
    lsb = addr & 0xFF
    msb = addr & (0xFF00)>>8
    handle.write_i2c_block_data(dev, msb, [lsb])
    data = handle.read_i2c_block_data(dev, 0, 1)[0]
    return data

def main (argv):
    parser = argparse.ArgumentParser(description="AD9545/46 power-down tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
    )
    flags = [
        ('clear', 'Clear (recover from a previous) power down op'), 
        ('all',   'Device power down (Sys clock pll, REFx, DPlls, APlls..)'),
        ('refb',  'TDC ref-b'),
        ('refbb', 'TDC ref-bb'),
        ('refa',  'TDC ref-a'),
        ('refaa', 'TDC ref-aa'),
    ]
    for (flag, helper) in flags:
        parser.add_argument(
            "--{}".format(flag), 
            action="store_true",
            help=helper,
        )
    args = parser.parse_args(argv)

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    if args.all:
        reg = read_data(handle, address, 0x2000)
        if args.clear:
            write_data(handle, address, 0x2000, reg & 0xFE)
        else:
            write_data(handle, address, 0x2000, reg | 0x01)
    else:
        reg = read_data(handle, address, 0x20001)
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
        write_data(handle, address, 0x2000, reg)

if __name__ == "__main__":
    main(sys.argv[1:])
