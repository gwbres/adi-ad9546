#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# misc.py
# miscellaneous features
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
    parser = argparse.ArgumentParser(description="AD9545/46 misc control tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
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
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

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
