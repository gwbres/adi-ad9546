#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# reset.py
# small script to quickly reset the device 
#################################################################
import sys
import argparse
from smbus import SMBus

def write_data (handle, dev, addr, data):
    lsb = addr & 0xFF
    msb = (addr & 0xFF00)>>8
    handle.write_i2c_block_data(dev, msb, [lsb, data])
def read_data (handle, dev, addr):
    lsb = addr & 0xFF
    msb = (addr & 0xFF00)>>8
    handle.write_i2c_block_data(dev, msb, [lsb])
    data = handle.read_i2c_block_data(dev, 0, 1)[0]
    return data

def main (argv):
    parser = argparse.ArgumentParser(description="AD9545/46 reset tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
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
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    if args.soft:
        reg = read_data(handle, address, 0x0000)
        reg &= 0x7E # clear bits
        write_data(handle, address, 0x0000, reg | 0x01 | 0x80)
        write_data(handle, address, 0x0000, reg)
    if args.sans:
        reg = read_data(handle, address, 0x0001)
        reg &= 0xFB # clear bit
        write_data(handle, address, 0x0001, reg | 0x04)
        write_data(handle, address, 0x0001, reg)
    if args.watchdog:
        reg = read_data(handle, address, 0x2005)
        write_data(handle, address, 0x0001, reg | 0x80)

if __name__ == "__main__":
    main(sys.argv[1:])
