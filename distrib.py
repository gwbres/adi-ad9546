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
        "--channel",
        metavar="channel",
        choices=["0","1","all"],
        default="all",
        type=str,
        help="Select which channel to configure. Defaults to `all`. Refer to README",
    )
    parser.add_argument(
        "--pin",
        metavar="pin",
        choices=["a","b","both"],
        default="both",
        type=str,
        help="Select pin between [A, B, or both]",
    )
    flags = [
        ("sync-all", None, [], """Synchronize all distribution dividers.
        If output behavior is not set to `immediate`, one must run a `sync-all` to
        output a synthesis."""),
        ('auto-sync', str, ['manual', 'immediate','phase','freq'], 'Set output pin behavior. Refer to README'),
        ('q-sync', None, [], 'Initialize a sync sequence on Q div. stage manually. Refer to README'),
        ('pwm-enable', None, [],  'Enable OUTxy PWM modulator, where x = channel, y = output pin'),
        ('pwm-disable', None, [], 'Disable OUTxy PWM modulator, where x = channel, y = output pin'),
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
            write_data(handle, address, 0x000F, 0x01) # IO update
        elif args.channel == '1':
            reg = read_data(handle, address, 0x14DB)
            write_data(handle, address, 0x14DB, reg|value)
            write_data(handle, address, 0x000F, 0x01) # IO update
        else: # all
            reg = read_data(handle, address, 0x10DB)
            write_data(handle, address, 0x10DB, reg|value)
            reg = read_data(handle, address, 0x14DB)
            write_data(handle, address, 0x14DB, reg|value)
            write_data(handle, address, 0x000F, 0x01) # IO update

    if args.q_sync:
        if args.channel == '0':
            reg = read_data(handle, address, 0x2101)
            write_data(handle, address, 0x2101, reg|0x08) # assert
            write_data(handle, address, 0x000F, 0x01) # IO update
            write_data(handle, address, 0x2101, reg|0xF7) # clear
            write_data(handle, address, 0x000F, 0x01) # IO update
        elif args.channel == '1':
            reg = read_data(handle, address, 0x2201)
            write_data(handle, address, 0x2201, reg|0x08) # assert
            write_data(handle, address, 0x000F, 0x01) # IO update
            write_data(handle, address, 0x2201, reg|0xF7) # clear
            write_data(handle, address, 0x000F, 0x01) # IO update
        else: # all
            reg = read_data(handle, address, 0x2101)
            write_data(handle, address, 0x2101, reg|0x08) # assert
            write_data(handle, address, 0x000F, 0x01) # IO update
            write_data(handle, address, 0x2101, reg|0xF7) # clear
            write_data(handle, address, 0x000F, 0x01) # IO update
            reg = read_data(handle, address, 0x2201)
            write_data(handle, address, 0x2201, reg|0x08) # assert
            write_data(handle, address, 0x000F, 0x01) # IO update
            write_data(handle, address, 0x2201, reg|0xF7) # clear
            write_data(handle, address, 0x000F, 0x01) # IO update

    if args.pwm_enable:
        if args.channel == 'all':
            if args.pin == 'both':
                for reg in [0x10CF, 0x10D0, 0x14CF, 0x14D0]:
                    v = read_data(handle, address, reg)
                    write_data(handle, address, reg, v | 0x01)
                write_data(handle, address, 0x000F, 0x01) # IO update
            elif args.pin == 'a':
                reg = read_data(handle, address, 0x10CF)
                write_data(handle, addres, 0x10CF, reg|0x01)
                reg = read_data(handle, address, 0x14CF)
                write_data(handle, addres, 0x14CF, reg|0x01)
                write_data(handle, address, 0x000F, 0x01) # IO update
            elif args.pin == 'b':
                reg = read_data(handle, address, 0x10D0)
                write_data(handle, addres, 0x10D0, reg|0x01)
                reg = read_data(handle, address, 0x14D0)
                write_data(handle, addres, 0x14D0, reg|0x01)
                write_data(handle, address, 0x000F, 0x01) # IO update
                    
        else:
            if args.channel == '0':
                if args.pin == 'both':
                    for reg in [0x10CF, 0x10D0]:
                        v = read_data(handle, address, reg)
                        write_data(handle, address, reg, v | 0x01)
                    write_data(handle, address, 0x000F, 0x01) # IO update
                elif args.pin == 'a':
                    v = read_data(handle, address, 0x10CF)
                    write_data(handle, address, reg, v | 0x01)
                    write_data(handle, address, 0x000F, 0x01) # IO update
                elif args.pin == 'b':
                    v = read_data(handle, address, 0x10D0)
                    write_data(handle, address, reg, v | 0x01)
                    write_data(handle, address, 0x000F, 0x01) # IO update
            else:
                if args.pin == 'both':
                    for reg in [0x14CF, 0x14D0]:
                        v = read_data(handle, address, reg)
                        write_data(handle, address, reg, v | 0x01)
                    write_data(handle, address, 0x000F, 0x01) # IO update
                elif args.pin == 'a':
                    v = read_data(handle, address, 0x14CF)
                    write_data(handle, address, reg, v | 0x01)
                    write_data(handle, address, 0x000F, 0x01) # IO update
                elif args.pin == 'b':
                    v = read_data(handle, address, 0x14D0)
                    write_data(handle, address, reg, v | 0x01)
                    write_data(handle, address, 0x000F, 0x01) # IO update

    if args.pwm_disable:
        if args.channel == 'all':
            if args.pin == 'both':
                for reg in [0x10CF, 0x10D0, 0x14CF, 0x14D0]:
                    v = read_data(handle, address, reg)
                    write_data(handle, address, reg, v & 0xFE)
                write_data(handle, address, 0x000F, 0x01) # IO update
            elif args.pin == 'a':
                reg = read_data(handle, address, 0x10CF)
                write_data(handle, address, reg, reg & 0xFE)
                reg = read_data(handle, address, 0x14CF)
                write_data(handle, address, reg, reg & 0xFE)
                write_data(handle, address, 0x000F, 0x01) # IO update
            elif args.pin == 'b':
                reg = read_data(handle, address, 0x10D0)
                write_data(handle, address, reg, reg & 0xFE)
                reg = read_data(handle, address, 0x14D0)
                write_data(handle, address, reg, reg & 0xFE)
                write_data(handle, address, 0x000F, 0x01) # IO update
                    
        else:
            if args.channel == '0':
                if args.pin == 'both':
                    for reg in [0x10CF, 0x10D0]:
                        v = read_data(handle, address, reg)
                        write_data(handle, address, reg, reg & 0xFE)
                    write_data(handle, address, 0x000F, 0x01) # IO update
                elif args.pin == 'a':
                    v = read_data(handle, address, 0x10CF)
                    write_data(handle, address, reg, reg & 0xFE)
                    write_data(handle, address, 0x000F, 0x01) # IO update
                elif args.pin == 'b':
                    v = read_data(handle, address, 0x10D0)
                    write_data(handle, address, reg, reg & 0xFE)
                    write_data(handle, address, 0x000F, 0x01) # IO update
            else:
                if args.pin == 'both':
                    for reg in [0x14CF, 0x14D0]:
                        v = read_data(handle, address, reg)
                        write_data(handle, address, reg, reg & 0xFE)
                    write_data(handle, address, 0x000F, 0x01) # IO update
                elif args.pin == 'a':
                    v = read_data(handle, address, 0x14CF)
                    write_data(handle, address, reg, reg & 0xFE)
                    write_data(handle, address, 0x000F, 0x01) # IO update
                elif args.pin == 'b':
                    v = read_data(handle, address, 0x14D0)
                    write_data(handle, address, reg, reg & 0xFE)
                    write_data(handle, address, 0x000F, 0x01) # IO update

if __name__ == "__main__":
    main(sys.argv[1:])
