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
    parser = argparse.ArgumentParser(description="AD9545/46 calibration tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
    )
    flags = [
        ('sysclk', 'Request Sys clock pll calibration'),
        ('pll',    'Request DPll + APll calibration'),
    ]
    for (flag, helper) in flags:
        parser.add_argument(
            "-{}".format(flag), 
            action="store_true",
            help=helper,
        )
    args = parser.parse_args(argv)

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    # [1] perform request
    reg = read_data(handle, address, 0x2000)
    if args.sysclk:
        reg |= 0x04
    if args.pll:
        reg |= 0x08
    write_data(handle, address, 0x2000, reg)
    write_data(handle, address, 0x0F, 0x01) # [2] I/O update
    # [3] clear bits
    if args.sysclk:
        reg &= 0xFB
    if args.pll:
        reg &= 0xF7
    write_data(handle, address, 0x2000, reg)
    write_data(handle, address, 0x0F, 0x01) # [4] I/O update

if __name__ == "__main__":
    main(sys.argv[1:])
