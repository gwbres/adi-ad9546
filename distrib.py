#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# distrib.py
# clock distribution dedicated script, to manage 
# internal clock distribution & output signals 
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
    parser = argparse.ArgumentParser(description="AD9545/46 clock distribution tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
    )
    parser.add_argument(
        "--core",
        metavar="object",
        choices=["pll", "qa", "qaa", "qb", "qbb", "qc", "qcc"],
        help="Select internal core to control. Refer to README", 
        type=str,
    )
    parser.add_argument(
        "--channel",
        metavar="channel",
        choices=["0","1","all"],
        default="all",
        type=str,
        help="Select which channel to configure. Defaults to `all`. Refer to README",
    )
    flags = [
        ("sync-all", None, """Synchronize all distribution dividers. 
        If output behavior is not set to `immediate`, one must run a `sync-all` to 
        output a synthesis."""),
        ("divide-ratio", int, "A/AA/B/BB/C/CC integer paths div. ratio."), 
    ]
    for (v_label, v_type, v_helper) in flags:
        if v_type is None:
            parser.add_argument(
                "--{}".format(v_label), 
                action="store_true",
                help=v_helper,
            )
        else:
            parser.add_argument(
                "--{}".format(v_label), 
                type=v_type,
                help=v_helper,
            )
    args = parser.parse_args(argv)

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    # Special Flags
    if args.sync_all:
        reg = read_data(handle, address, 0x2000)
        write_data(handle, address, 0x2000, reg|0x08)
        write_data(handle, address, 0x000F, 0x01) # IO update
        write_data(handle, address, 0x2000, reg&0xF7)
        write_data(handle, address, 0x000F, 0x01) # IO update

if __name__ == "__main__":
    main(sys.argv[1:])
