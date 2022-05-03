#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# reference.py
# Reference, input signal, switching mechanism control
#################################################################
import sys
import math
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
    parser = argparse.ArgumentParser(description="AD9545/46 reference control tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
    )
    flags = [
        ('free-run', None, [], 'Force to free-run state'),
        ('holdover', None, [], 'Force to holdover state'),
        ('fb-div', int, [], 'Set Pll multiplication ratio'),
        ('freq', float, [], 'Set sys clock reference frequency [Hz]'),
        0x0202
        ('sel', str, ['direct','crystal'], 'Select ref. frequency source'),
        ('divider', int, [1,2,4,8], 'Set input frequency division ratio (int)'),
        ('doubler', str, ['enable','disable'], 'Enable / Disable input frequency doubler'),
        0x0201
        ('stab-period', float, [], 'Set sys clock stability period [s]'),
        0x0207
    ]
    for (v_flag, v_type, v_choices, v_helper) in flags:
        if v_type is None:
            parser.add_argument(
                "--{}".format(v_flag), 
                action="store_true",
                help=v_helper,
            )
        else:
            parser.add_argument(
                "--{}".format(v_flag), 
                type=v_type,
                choices=v_choices,
                help=v_helper,
            )
    args = parser.parse_args(argv)

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    sel = {
        'direct': 0,
        'crystal': 1,
    }

    if args.fb_div:
        write_data(handle, address, 0x0200, args.fb_div & 0xFF)
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop
    
    if args.sel:
        r = read_data(handle, address, 0x0201)
        write_data(handle, address, 0x0201, r | (sel[args.sel]<<3))
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop
   
    if args.divider:
        r = read_data(handle, address, 0x0201)
        write_data(handle, address, 0x0201, r | (round(math.log2(args.divider)) << 1))
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop
    
    if args.free_run:
        reg = read_data(handle, address, 0x2105)
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop

    if args.holdover:
        reg = read_data(handle, address, 0x2105)
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop

    if args.period:
        period = round(10E-18/args.period)
        r0 = period & 0xFF
        r1 = (period & 0xFF00)>>8
        r2 = (period & 0xFF0000)>>16
        r3 = (period & 0xFF000000)>>24
        r4 = (period & 0xFF00000000)>>32
        r5 = (period & 0xFF0000000000)>>40
        r6 = (period & 0xFF000000000000)>>48
        if pin == 'all':
            regs = [0x0404, 0x0424, 0x0444, 0x0464, 0x0484, 0x04C4, 0x04E4]
        elif pin == 'a':
            regs = [0x0404]
        elif pin == 'aa':
            regs = [0x0424]
        elif pin == 'b':
            regs = [0x0444]
        elif pin == 'bb':
            regs = [0x0464]
        elif pin == 'aux-0':
            regs = [0x0484]
        elif pin == 'aux-1':
            regs = [0x04A4]
        elif pin == 'aux-2':
            regs = [0x04C4]
        elif pin == 'aux-2':
            regs = [0x04C4]
        elif pin == 'aux-3':
            regs = [0x04E4]
        for reg in regs:
            write_data(handle, address, reg+0, r0)
            write_data(handle, address, reg+1, r1)
            write_data(handle, address, reg+2, r2)
            write_data(handle, address, reg+3, r3)
            write_data(handle, address, reg+4, r4)
            write_data(handle, address, reg+5, r5)
            write_data(handle, address, reg+6, r6 & 0xF)
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0

    if args.phase_lock_thresh:
        value = round(args.phase_lock_thresh * 1E-12)
        if parser.channel == "all":
            0x0820 + 0x0821 + 0x0822 # aa
        else:
 
    if args.freq_lock_thresh:
        df = args.freq_lock_thresh
        value = round(df / fr * (1/(df+fr)) * pow(10,12))
            0x0825 + 0x0826 + 0x0827 # aa

if __name__ == "__main__":
    main(sys.argv[1:])
