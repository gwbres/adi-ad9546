#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# Mx-pin.py
# Programmable I/Os
#################################################################
import sys
import argparse
from smbus import SMBus

def write_data (handle, dev, addr, data):
    msb = (addr & 0xFF00)>>8
    lsb = addr & 0xFF
    handle.write_i2c_block_data(dev, msb, [lsb, data])
def read_data (handle, dev, addr):
    msb = (addr & 0xFF00)>>8
    lsb = addr & 0xFF
    handle.write_i2c_block_data(dev, msb, [lsb])
    data = handle.read_byte(dev)
    return data

def main (argv):
    parser = argparse.ArgumentParser(description="AD9545/46 Mx-pin programmable I/O")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
    )
    parser.add_argument(
        "pin",
        metavar="pin",
        choices=["M1","M2","M3","M4","M5","M6"],
        help="Select with pin to assign",
        type=str,
    )
    parser.add_argument(
        "mode",
        metavar="mode",
        choices=["control","status"],
        help="Select whether this is a control or a status assignment",
        type=str,
    )
    args = parser.parse_args(argv)
    print("this tool is work in progress")

if __name__ == "__main__":
    main(sys.argv[1:])
