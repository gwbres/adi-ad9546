#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# irq.py: IRQ clearing tool
#################################################################
import sys
import argparse
from ad9546 import *

def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 IRQ clearing tool")
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
    flags = [
        ('all', 'Clears all IRQ flags'),
        ('watchdog', 'Clear watchdog timer timeout event'),
        ('pll',  'Clear all pll (0+1 digital & analogic) events'),
        ('pll1', 'Clear all pll1 (digital & analogic) events'),
        ('pll0', 'Clear all pll0 (digital & analogic) events'),
        ('other', 'Clears all events that are not related to PLL (0+1) group'),
        ('eeprom', 'Clears all EEPROM related events'),
        ('sysclk', 'Clear all sysclk related events'),
        ('sysclk-unlock', 'Clears unlocking event'),
        ('sysclk-stab', 'Clears `stabilized` event'),
        ('sysclk-lock', 'Clears locking event'),
        ('sysclk-cal-start', 'Clears calibration start event'),
        ('sysclk-cal-end', 'Clears calibration end event'),
        ('skew-limit',  'Clear skew limit detection event'),
        ('skew-meas', 'Clear new skew measurement event'),
        ('temp', 'Clear temp range warning'),
        ('tsu', 'Clear timestamping units update events'),
        ('refa',  'Clear all A reference events'),
        ('refaa', 'Clear all AA reference events'),
        ('refb',  'Clear all B reference events'),
        ('refbb', 'Clear all BB reference events'),
    ]
    for (flag, helper) in flags:
        parser.add_argument(
            "--{}".format(flag),
            action="store_true",
            help=helper,
        )
    args = parser.parse_args(argv)
    dev = AD9546(args.bus, int(args.address, 16)) # open device

    if args.all:
        dev.write_data(0x2005, 0x01)
    if args.watchdog:
        dev.write_data(0x2006, 0x04)
    if args.pll:
        dev.write_data(0x2005, 0x08|0x04)
    if args.pll1:
        dev.write_data(0x2005, 0x08)
    if args.pll0:
        dev.write_data(0x2005, 0x04)
    if args.other:
        dev.write_data(0x2005, 0x02)
    if args.sysclk:
        dev.write_data(0x2006, 0xF8)
    if args.sysclk_unlock:
        dev.write_data(0x2006, 0x80)
    if args.sysclk_stab:
        dev.write_data(0x2006, 0x40)
    if args.sysclk_lock:
        dev.write_data(0x2006, 0x20)
    if args.sysclk_cal_end:
        dev.write_data(0x2006, 0x10)
    if args.sysclk_cal_start:
        dev.write_data(0x2006, 0x08)
    if args.eeprom:
        dev.write_data(0x2006, 0x01|0x02)
    if args.skew_limit:
        dev.write_data(0x2007, 0x20)
    if args.skew_meas:
        dev.write_data(0x200A, 0x10)
    if args.refa:
        dev.write_data(0x2008, 0x0F)
    if args.refaa:
        dev.write_data(0x2008, 0xF0)
    if args.refb:
        dev.write_data(0x2009, 0x0F)
    if args.refbb:
        dev.write_data(0x2009, 0xF0)
    if args.tsu:
        dev.write_data(0x200A, 0x08|0x04)
    if args.temp:
        dev.write_data(0x2007, 0x10)

if __name__ == "__main__":
    main(sys.argv[1:])
