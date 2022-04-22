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
        ("sync-all", None, [], """Synchronize all distribution dividers. 
        If output behavior is not set to `immediate`, one must run a `sync-all` to 
        output a synthesis."""),
        ("divide-ratio", int, [], "A/AA/B/BB/C/CC integer paths div. ratio."), 
        ('auto-sync', str, ['manual', 'immediate','phase','freq'], 'Set output pin behavior. Refer to README'),
        ('q-sync', None, [], 'Initialize a sync sequence on Q div. stage manually. Refer to README'),
    ]
    for (v_label, v_type, v_choices, v_helper) in flags:
        if v_type is None:
            parser.add_argument(
                "--{}".format(v_label), 
                action="store_true",
                help=v_helper,
            )
        else:
            parser.add_argument(
                "--{}".format(v_label), 
                choices=v_choices,
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
        write_data(handle, address, 0x2000, 0x08)
        write_data(handle, address, 0x000F, 0x01) # IO update

    core = args.core
    channel = args.channel
    if args.auto_sync:
        value = 0x00
        if args.auto_sync == 'immediate':
            value = 0x01
        if args.auto_sync == 'phase':
            value = 0x02
        if args.auto_sync == 'freq':
            value = 0x03
        if args.channel == '0':
            reg = read_data(handle, address, 0x10DB)
            write_data(handle, address, 0x10DB, reg|value)
        elif args.channel == '1':
            reg = read_data(handle, address, 0x14DB)
            write_data(handle, address, 0x14DB, reg|value)
        else: # all
            reg = read_data(handle, address, 0x10DB)
            write_data(handle, address, 0x10DB, reg|value)
            write_data(handle, address, 0x10DB, reg|value)
            reg = read_data(handle, address, 0x14DB)
            write_data(handle, address, 0x14DB, reg|value)
            write_data(handle, address, 0x14DB, reg|value)
    
    if args.q_sync:
        if args.channel == '0':
            reg = read_data(handle, address, 0x2101)
            write_data(handle, address, 0x2101, reg|0x08)
        elif args.channel == '1':
            reg = read_data(handle, address, 0x2201)
            write_data(handle, address, 0x2201, reg|0x08)
        else: # all
            reg = read_data(handle, address, 0x2101)
            write_data(handle, address, 0x2101, reg|0x08)
            reg = read_data(handle, address, 0x2201)
            write_data(handle, address, 0x2201, reg|0x08)

if __name__ == "__main__":
    main(sys.argv[1:])
