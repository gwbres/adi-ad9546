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
        ('sel', str, ['direct','crystal'], 'Select ref. frequency source'),
        ('divider', int, [1,2,4,8], 'Set input frequency division ratio (int)'),
        ('doubler', str, ['enable','disable'], 'Enable / Disable input frequency doubler'),
        ('freq', float, [], 'Set sys clock reference frequency [Hz]'),
        ('stability', float, [], 'Set sys clock ref. stability period [s]'),
        ('slew-rate-lim', str, [
            'None',
            '0.715ppm/s',
            '1.430ppm/s',
            '2.860ppm/s',
            '5.720ppm/s',
            '11.44ppm/s',
            '22.88ppm/s',
            '45.76ppm/s',
        ], 
        'Sys clock compensation slew rate limiter control'),
        ('dpll-source', str, 
        ['refa','refaa','refb','refbb','aux-ref0','aux-ref1','aux-ref2','aux-ref3'],
        'Select source for compensation method 3 that uses auxilary Dpll'),
        ('dpll-bw', float, [],  'Auxilary Dpll Loop filter bandwidth [Hz]'),
        ('dpll-sel', str, ['dpll0','dpll1'], 'Sys clock compensation, method 2 Dpll channel selection'),
        ('cutoff', str, ['156Hz','78Hz','39Hz','20Hz','10Hz','5Hz','2Hz','1Hz'], 
        'Method 1 low pass filter cutoff frequency'),
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
    en = {
        'disable': 0,
        'enable': 1,
    }
    slew_r = {
        'None' : 0,
        '0.715ppm/s': 1,
        '1.430ppm/s': 2,
        '2.860ppm/s': 3,
        '5.720ppm/s': 4,
        '11.44ppm/s': 5,
        '22.88ppm/s': 6,
        '45.76ppm/s': 7,
    }
    dpll_sources = {
        'refa': 0,
        'refaa': 1,
        'refb': 2,
        'refbb': 3,
        'aux-ref0': 6,
        'aux-ref1': 7,
        'aux-ref2': 11,
        'aux-ref3': 12,
    }
    dpll_ch = {
        'dpll0': 0,
        'dpll1': 1,
    }
    cutoffs = {
        '156Hz': 0,
        '78Hz': 1,
        '39Hz': 2,
        '20Hz': 3,
        '10Hz': 4,
        '5Hz': 5,
        '2Hz': 6,
        '1Hz': 7,
    }

    if args.fb_div:
        write_data(handle, address, 0x0200, args.fb_div & 0xFF)
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop
    
    if args.sel:
        r = read_data(handle, address, 0x0201)
        r &= 0xF7 # mask out
        write_data(handle, address, 0x0201, r | (sel[args.sel]<<3))
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop
   
    if args.divider:
        r = read_data(handle, address, 0x0201)
        r &= 0xF9
        write_data(handle, address, 0x0201, r | (round(math.log2(args.divider)) << 1))
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop
    
    if args.doubler:
        r = read_data(handle, address, 0x0201)
        r &= 0xFE # mask bit out
        write_data(handle, address, 0x0201, r | en[args.doubler])
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop

    if args.dpll_source:
        r = read_data(handle, address, 0x0284)
        r &= 0xE0 # mask bits out
        write_data(handle, address, 0x0284, r | dpll_sources[args.dpll_source])
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop
    
    if args.dpll_bw:
        bw = args.dpll_bw * 10
        write_data(handle, address, 0x0285, r & 0xFF)
        write_data(handle, address, 0x0286, (r & 0xFF00)>>8)
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop

    if args.dpll_ch:
        r = read_data(handle, address, 0x0287)
        r &= 0xFE # mask bit out
        write_data(handle, address, 0x0287, r | dpll_ch[args.dpll_ch]) # assign
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop

    if args.cutoff:
        r = read_data(handle, address, 0x0288)
        r &= 0xF8 # mask bits out 
        write_data(handle, address, 0x0288, r | cutoffs[args.cutoff])
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop

    if args.free_run:
        r = read_data(handle, address, 0x2105)
        r &= 0xFE # clear bits out
        write_data(handle, address, 0x2105, r|0x01) # force free run
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop

    if args.holdover:
        r = read_data(handle, address, 0x2105)
        r &= 0xFD
        write_data(handle, address, 0x2105, r | 0x02) # force holdover
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0 # force stop

    if args.freq:
        freq = args.freq * pow(10,3)
        write_data(handle, address, 0x0202, freq & 0xFF)
        write_data(handle, address, 0x0203, (freq & 0xFF00)>>8)
        write_data(handle, address, 0x0204, (freq & 0xFF0000)>>16)
        write_data(handle, address, 0x0205, (freq & 0xFF000000)>>24)
        write_data(handle, address, 0x0206, (freq & 0xFF00000000)>>32)
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0
    
    if args.slew_rate_lim:
        r = read_data(handle, address, 0x0283)
        r &= 0xF8
        write_data(handle, address, 0x0283, r | slew_r[args.slew_rate_lim])
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0
    
    if args.stability:
        stab = args.stability * pow(10,3)
        write_data(handle, address, 0x0207, stab & 0xFF)
        write_data(handle, address, 0x0208, (stab & 0xFF00)>>8)
        r = read_data(handle, address, 0x0209)
        write_data(handle, address, 0x0209, r | ((stab & 0x0F0000)>>16))
        write_data(handle, address, 0x000F, 0x01) # I/O update
        return 0

if __name__ == "__main__":
    main(sys.argv[1:])
