#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# irq.py
# IRQ clearing tool 
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
    parser = argparse.ArgumentParser(description="AD9545/46 IRQ clearing tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
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

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    if args.all:
        write_data(handle, address, 0x2005, 0x01)
    if args.watchdog:
        write_data(handle, address, 0x2006, 0x04)
    if args.pll:
        write_data(handle, address, 0x2005, 0x08|0x04)
    if args.pll1:
        write_data(handle, address, 0x2005, 0x08)
    if args.pll0:
        write_data(handle, address, 0x2005, 0x04)
    if args.other:
        write_data(handle, address, 0x2005, 0x02)
    if args.sysclk:
        write_data(handle, address, 0x2006, 0xF8)
    if args.sysclk_unlock:
        write_data(handle, address, 0x2006, 0x80)
    if args.sysclk_stab:
        write_data(handle, address, 0x2006, 0x40)
    if args.sysclk_lock:
        write_data(handle, address, 0x2006, 0x20)
    if args.sysclk_cal_end:
        write_data(handle, address, 0x2006, 0x10)
    if args.sysclk_cal_start:
        write_data(handle, address, 0x2006, 0x08)
    if args.eeprom:
        write_data(handle, address, 0x2006, 0x01|0x02)
    if args.skew_limit: 
        write_data(handle, address, 0x2007, 0x20)
    if args.skew_meas:
        write_data(handle, address, 0x200A, 0x10)
    if args.refa:
        write_data(handle, address, 0x2008, 0x0F)
    if args.refaa:
        write_data(handle, address, 0x2008, 0xF0)
    if args.refb:
        write_data(handle, address, 0x2009, 0x0F)
    if args.refbb:
        write_data(handle, address, 0x2009, 0xF0)
    if args.tsu:
        write_data(handle, address, 0x200A, 0x08|0x04)
    if args.temp: 
        write_data(handle, address, 0x2007, 0x10)

if __name__ == "__main__":
    main(sys.argv[1:])
