#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# reference.py
# Reference, input signal, switching mechanism control
#################################################################
import sys
import argparse
from ad9546 import *

def main (argv):
    parser = argparse.ArgumentParser(description="AD9545/46 reference control tool")
    parser.add_argument(
        "bus",
        type=int,
        help="i2c bus (int)",
    )
    parser.add_argument(
        "address",
        type=str,
        help="i2c slv address (hex format)",
    )
    parser.add_argument(
        '--ref',
        choices=['a','aa','b','bb','aux-0','aux-1','aux-2','aux-3','all'],
        default="all",
        help="""Select desired input reference. 
        Defaults to `all`. Aux-x means auxilary-x input reference, when feasible.""",
    )
    flags = [
        ('freq', float, [], 'Set REFxy input frequency [Hz], where x = channel'),
        ('coupling', str, ['ac','dc','dc-lvds'], 'Set REFx input coupling, where x = channel'),
        ('free-run', None, [], 'Force DPLLx to free-run state manually, where x = channel'),
        ('holdover', None, [], 'Force DPLLx to holdover state manually, `lock` being already be acquired. x = channel'),
        ('freq-lock-thresh',  float, [], 'Set REFx freq lock threshold [Hz], where x = channel'),
        ('phase-lock-thresh', float, [], 'Set REFx phase lock threshold [s]'),
        ('phase-step-thresh', float, [], 'Set REFx phase step detector threshold [s]'),
        ('phase-skew',        float, [], 'Set REFx phase skew [s]'),
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

    pin = args.pin
    channel = args.channel

    # open device
    dev = ad9546(args.bus, int(args.address, 16))

    if args.free_run:
        r = dev.read_data(0x2105)
        dev.write_data(0x2105, r | 0x01)
        dev.io_update()
        return 0 # force stop

    if args.holdover:
        r = dev.read_data(0x2105)
        dev.write_data(0x2105, r | 0x02)
        dev.io_update()
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
            dev.write_data(reg+0, r0)
            dev.write_data(reg+1, r1)
            dev.write_data(reg+2, r2)
            dev.write_data(reg+3, r3)
            dev.write_data(reg+4, r4)
            dev.write_data(reg+5, r5)
            dev.write_data(reg+6, r6 & 0xF)
        dev.io_update()
        return 0

    #if args.phase_lock_thresh:
    #    value = round(args.phase_lock_thresh * 1E-12)
    #    if parser.channel == "all":
    #        0x0820 + 0x0821 + 0x0822 # aa
    #    else:
 
    #if args.freq_lock_thresh:
    #    df = args.freq_lock_thresh
    #    value = round(df / fr * (1/(df+fr)) * pow(10,12))
    #        0x0825 + 0x0826 + 0x0827 # aa

if __name__ == "__main__":
    main(sys.argv[1:])
