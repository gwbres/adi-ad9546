#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# sysclk.py: sys clock management tool
#################################################################
import sys
import math
import argparse
from ad9546 import *

def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 sys clock management")
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
    dev = AD9546(args.bus, int(args.address, 16))

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
        dev.write_data(0x0200, args.fb_div & 0xFF)
    if args.sel:
        r = dev.read_data(0x0201)
        r &= 0xF7 # mask out
        dev.write_data(0x0201, r | (sel[args.sel]<<3))
    if args.divider:
        r = dev.read_data(0x0201)
        r &= 0xF9
        dev.write_data(0x0201, r | (round(math.log2(args.divider)) << 1))
    if args.doubler:
        r = dev.read_data(0x0201)
        r &= 0xFE # mask bit out
        dev.write_data(0x0201, r | en[args.doubler])
    if args.dpll_source:
        r = dev.read_data(0x0284)
        r &= 0xE0 # mask bits out
        dev.write_data(0x0284, r | dpll_sources[args.dpll_source])
    if args.dpll_bw:
        bw = args.dpll_bw * 10
        dev.write_data(0x0285, r & 0xFF)
        dev.write_data(0x0286, (r & 0xFF00)>>8)
    if args.dpll_ch:
        r = dev.read_data(0x0287)
        r &= 0xFE # mask bit out
        dev.write_data(0x0287, r | dpll_ch[args.dpll_ch]) # assign
    if args.cutoff:
        r = dev.read_data(0x0288)
        r &= 0xF8 # mask bits out 
        dev.write_data(0x0288, r | cutoffs[args.cutoff])
    if args.freq:
        freq = args.freq * pow(10,3)
        dev.write_data(0x0202, freq & 0xFF)
        dev.write_data(0x0203, (freq & 0xFF00)>>8)
        dev.write_data(0x0204, (freq & 0xFF0000)>>16)
        dev.write_data(0x0205, (freq & 0xFF000000)>>24)
        dev.write_data(0x0206, (freq & 0xFF00000000)>>32)
    if args.slew_rate_lim:
        r = dev.read_data(0x0283)
        r &= 0xF8
        dev.write_data(0x0283, r | slew_r[args.slew_rate_lim])
    if args.stability:
        stab = args.stability * pow(10,3)
        dev.write_data(0x0207, stab & 0xFF)
        dev.write_data(0x0208, (stab & 0xFF00)>>8)
        r = dev.read_data(0x0209)
        dev.write_data(0x0209, r | ((stab & 0x0F0000)>>16))
    dev.io_update()

if __name__ == "__main__":
    main(sys.argv[1:])
