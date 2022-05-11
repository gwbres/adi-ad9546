#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# Mx-pin.py: AD9546 programmable I/Os
#################################################################
import sys
import argparse
from ad9546 import *

def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 mx-pin programmable i/o")
    parser.add_argument(
        "bus",
        type=int,
        help="i2c bus (int)",
    )
    parser.add_argument(
        "address",
        type=str,
        help="i2c slv address (hex)",
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
    # open device
    dev = AD9546(args.bus, int(args.address,16))

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

    r = dev.read_data(reg)
    mask = 0x03 << ((pin_n % 4)*2)
    r &= (mask ^0xFF) #mask bits out
    if args.rcv:
        dev.write_data(reg, r | (recv[args.rcv] << ((pin_n%4)*2))) # assign
    elif args.drv:
        dev.write_data(reg, r | (drv[args.drv] << ((pin_n%4)*2))) # assign
    
    base = 0x0102
    r = dev.read_data(base + pin_n)
    r &= 0x7F # mask bit out
    dev.write_data(base + pin_n, r | (modes[args.mode] <<7))

    r = dev.read_data(0x0109)
    mask = 0x01 << pin_n
    r &= (mask ^0xFF) # mask out
    dev.write_data(0x0109, r | (currents[args.current] << pin_n))
    dev.io_update()

if __name__ == "__main__":
    main(sys.argv[1:])
