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
    #parser.add_argument(
    #    "op",
    #    metavar="operation",
    #    choices=["config","assert"],
    #    type=str,
    #    help="Select whether we are configure or asserting a previously configured pin",
    #)
    parser.add_argument(
        "pin",
        metavar="pin",
        choices=["M0", "M1","M2","M3","M4","M5","M6"],
        help="Select with pin to assign",
        type=str,
    )
    parser.add_argument(
        "mode",
        metavar="mode",
        choices=["control","status"],
        help="Select whether this is a TX or an RX pin",
        type=str,
    )
    parser.add_argument(
        "--drv",
        metavar="drive",
        choices=["normal","inverted","open-drain","open-drain-inv"],
        type=str,
        help="Select TX logic",
    )
    parser.add_argument(
        "--rcv",
        metavar="receive",
        choices=["and", "nand", "or", "nor"],
        type=str,
        help="Select RX logic",
    )
    parser.add_argument(
        '--current',
        metavar='current',
        choices=['3mA','6mA'],
        default='6mA',
        type=str,
        help="Ouptut current (drive strength); default is 6mA",
    )
    args = parser.parse_args(argv)

    handle = SMBus()
    handle.open(int(args.bus))
    address = args.address

    pin = args.pin
    pin_n = int(pin.strip("M"))
    mode = args.mode
    current = args.current
    
    currents = {
        '6mA': 0,
        '3mA': 1,
    }
    modes = {
        'control': 0,
        'status': 1,
    }
    drv = {
        'normal': 0,
        'inverted': 1,
        'open-drain': 2,
        'open-drain-inv': 3,
    }
    recv = {
        'and': 0,
        'nand': 1,
        'or': 2,
        'nor': 3,
    }

    if pin_n < 4:
        reg = 0x0100 
    else:
        reg = 0x0101 

    r = read_data(handle, address, reg)
    mask = 0x03 << ((pin_n % 4)*2)
    r &= (mask ^0xFF) #mask bits out
    if args.rcv:
        write_data(handle, address, reg, r | (recv[args.rcv] << ((pin_n%4)*2))) # assign
    elif args.drv:
        write_data(handle, address, reg, r | (drv[args.drv] << ((pin_n%4)*2))) # assign
    
    base = 0x0102
    r = read_data(handle, address, base + pin_n)
    r &= 0x7F # mask bit out
    write_data(handle, address, base + pin_n, r | (modes[args.mode] <<7))

    r = read_data(handle, address, 0x0109)
    mask = 0x01 << pin_n
    r &= (mask ^0xFF) # mask out
    write_data(handle, address, 0x0109, r | (currents[args.current] << pin_n))
    write_data(handle, address, 0x000F, 0x01) # IO update

if __name__ == "__main__":
    main(sys.argv[1:])
