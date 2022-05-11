#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# reference.py: reference, input signal, 
# switching mechanism control
#################################################################
import sys
import argparse
from ad9546 import *

def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 reference input management")
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
        ('freq', float, [], 'Set REFx input frequency [Hz]'),
        ('coupling', str, ['AC 1.2V','DC 1.2V CMOS','DC 1.8V CMOS','internal pull-up'], 'Set REFx input coupling'),
        ('diff-mode', str, ['AC','DC','DC-LVDS'], 'Set REFx input differential mode'),
        ('differential', None, [], 'Set REFx as differential input. REFx and REFxx is a differential pair'),
        ('single-ended', None, [], 'Set REFx as single-ended input. REFx and REFxx are independent pins'),
        ('demod', str, ['enable','disable'], 'Enable / Disable REFx demodulator'),
        ('demod-bw', str, ['narrow','wide'], 'Select REFx/xx demodulator bandwidth'),
        ('demod-sensitivity', int, [0,1,2,3], 'Select REFx demodulator level sensitivity (0=max, 3=min)'),
        ('demod-sync-edge', int, [0,1,2,3], 'Select REFx synchronization edge'),
        ('demod-persistence', str, ['enable','disable'], 'Enable / Disable REFx demodulator persistence'),
        ('freq-lock-thresh',  float, [], 'Set REFx freq lock threshold. Requires `freq` to be previously set, for internal calculations, [n.a: df/f]'),
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
    ref = args.ref
    # open device
    dev = AD9546(args.bus, int(args.address, 16))

    if args.coupling:
        couplings = {
            'AC 1.2V': 0,
            'DC 1.2V CMOS': 1,
            'DC 1.8V CMOS': 2,
            'internal pull-up': 3,
        }
        if args.ref == 'all':
            r = dev.read_data(0x0300)
            r &= 0x0F
            r |= couplings[args.coupling] << 4
            r |= couplings[args.coupling] << 6
            dev.write_data(0x0300, r)
            r = dev.read_data(0x0304)
            r &= 0x0F
            r |= couplings[args.coupling] << 4
            r |= couplings[args.coupling] << 6
            dev.write_data(0x0304, r)

        elif args.ref == 'aa':
            r = dev.read_data(0x0300)
            r &= 0x3F
            r |= couplings[args.coupling] << 6
            dev.write_data(0x0300, r)
        elif args.ref == 'a':
            r = dev.read_data(0x0300)
            r &= 0xCF
            r |= couplings[args.coupling] << 4
            dev.write_data(0x0300, r)
        
        elif args.ref == 'bb':
            r = dev.read_data(0x0304)
            r &= 0x3F
            r |= couplings[args.coupling] << 6
            dev.write_data(0x0304, r)
        elif args.ref == 'b':
            r = dev.read_data(0x0304)
            r &= 0xCF
            r |= couplings[args.coupling] << 4
            dev.write_data(0x0304, r)
  
    if args.demod_bw:
        bw = {
            'narrow': 0,
            'wide': 1,
        }
        if args.ref == 'all':
            r = dev.read_data(0x0301)
            r &= 0xFE
            r |= bw[args.demod_bw]
            dev.write_data(0x0301, r)
            r = dev.read_data(0x0305)
            r &= 0xFE
            r |= bw[args.demod_bw]
            dev.write_data(0x0305, r)
        elif args.ref == 'a' or args.ref == 'aa':
            r = dev.read_data(0x0301)
            r &= 0xFE
            r |= bw[args.demod_bw]
            dev.write_data(0x0301, r)
        elif args.ref == 'b' or args.ref == 'bb':
            r = dev.read_data(0x0305)
            r &= 0xFE
            r |= bw[args.demod_bw]
            dev.write_data(0x0305, r)

    if args.diff_mode:
        modes = {
            'AC': 0,
            'DC': 1,
            'DC-LVDS': 2,
        }
        if args.ref == 'all':
            r = dev.read_data(0x0300)
            r &= 0xF3
            r |= modes[args.diff_mode] << 2
            dev.write_data(0x0300, r)
            r = dev.read_data(0x0304)
            r &= 0xF3
            r |= modes[args.diff_mode] << 2
            dev.write_data(0x0304, r)
        elif args.ref == 'aa' or args.ref == 'a': # user should only use 'A' but whatever
            r = dev.read_data(0x0300)
            r &= 0xF3
            r |= modes[args.diff_mode] << 2
            dev.write_data(0x0300, r)
        elif args.ref == 'bb' or args.ref == 'b': # user should only use 'B' but whatever
            r = dev.read_data(0x0304)
            r &= 0xF3
            r |= modes[args.diff_mode] << 2
            dev.write_data(0x0304, r)

    if args.differential:
        if args.ref == 'all':
            r = dev.read_data(0x0300)
            dev.write_data(0x0300, r|0x01)
            r = dev.read_data(0x0304)
            dev.write_data(0x0304, r|0x01)
        
        elif args.ref == 'aa' or args.ref == 'a':
            r = dev.read_data(0x0300)
            dev.write_data(0x0300, r|0x01)
        elif args.ref == 'bb' or args.ref == 'b':
            r = dev.read_data(0x0304)
            dev.write_data(0x0304, r|0x01)
    
    if args.single_ended:
        if args.ref == 'all':
            r = dev.read_data(0x0300)
            dev.write_data(0x0300, r & 0xFE)
            r = dev.read_data(0x0304)
            dev.write_data(0x0304, r & 0xFE)
        
        elif args.ref == 'aa' or args.ref == 'a':
            r = dev.read_data(0x0300)
            dev.write_data(0x0300, r & 0xFE)
        elif args.ref == 'bb' or args.ref == 'b':
            r = dev.read_data(0x0304)
            dev.write_data(0x0304, r & 0xFE)

    if args.demod_sync_edge:
        if args.ref == 'all':
            for reg in [0x0302,0x0303,0x0306,0x0307,0x030A,0x030B,0x030E,0x030F]:
                r = dev.read_data(reg)
                r &= 0xCF
                r |= args.demod_sensitivity << 4
                dev.write_data(reg, r)
        elif args.ref == 'aa':
            r = dev.read_data(0x0303)
            r &= 0xCF
            r |= args.demod_sensitivity << 4
            dev.write_data(0x0303, r)
        elif args.ref == 'a':
            r = dev.read_data(0x0302)
            r &= 0xCF
            r |= args.demod_sensitivity << 4
            dev.write_data(0x0302, r)
        elif args.ref == 'bb':
            r = dev.read_data(0x0307)
            r &= 0xCF
            r |= args.demod_sensitivity << 4
            dev.write_data(0x0307, r)
        elif args.ref == 'b':
            r = dev.read_data(0x0306)
            r &= 0xCF
            r |= args.demod_sensitivity << 4
            dev.write_data(0x0306, r)
        elif args.ref == 'aux-0':
            r = dev.read_data(0x030A)
            r &= 0xCF
            r |= args.demod_sensitivity << 4
            dev.write_data(0x030A, r)
        elif args.ref == 'aux-1':
            r = dev.read_data(0x030B)
            r &= 0xCF
            r |= args.demod_sensitivity << 4
            dev.write_data(0x030B, r)
        elif args.ref == 'aux-2':
            r = dev.read_data(0x030E)
            r &= 0xCF
            r |= args.demod_sensitivity << 4
            dev.write_data(0x030E, r)
        elif args.ref == 'aux-3':
            r = dev.read_data(0x030F)
            r &= 0xCF
            r |= args.demod_sensitivity << 4
            dev.write_data(0x030F, r)

    if args.demod_sensitivity:
        if args.ref == 'all':
            for reg in [0x0302,0x0303,0x0306,0x0307,0x030A,0x030B,0x030E,0x030F]:
                r = dev.read_data(reg)
                r &= 0xFC
                r |= args.demod_sensitivity
                dev.write_data(reg, r)
        elif args.ref == 'aa':
            r = dev.read_data(0x0303)
            r &= 0xFC
            r |= args.demod_sensitivity
            dev.write_data(0x0303, r)
        elif args.ref == 'a':
            r = dev.read_data(0x0302)
            r &= 0xFC
            r |= args.demod_sensitivity
            dev.write_data(0x0302, r)
        elif args.ref == 'bb':
            r = dev.read_data(0x0307)
            r &= 0xFC
            dev.write_data(0x0307, r)
            r |= args.demod_sensitivity
        elif args.ref == 'b':
            r = dev.read_data(0x0306)
            r &= 0xFC
            r |= args.demod_sensitivity
            dev.write_data(0x0306, r)
        elif args.ref == 'aux-0':
            r = dev.read_data(0x030A)
            r &= 0xFC
            r |= args.demod_sensitivity
            dev.write_data(0x030A, r)
        elif args.ref == 'aux-1':
            r = dev.read_data(0x030B)
            r &= 0xFC
            r |= args.demod_sensitivity
            dev.write_data(0x030B, r)
        elif args.ref == 'aux-2':
            r = dev.read_data(0x030E)
            r &= 0xFC
            r |= args.demod_sensitivity
            dev.write_data(0x030E, r)
        elif args.ref == 'aux-3':
            r = dev.read_data(0x030F)
            r &= 0xFC
            r |= args.demod_sensitivity
            dev.write_data(0x030F, r)

    if args.demod_persistence:
        enable = {
            'disable': 0,
            'enable': 1,
        }
        if args.ref == 'all':
            for reg in [0x0302,0x0303,0x0306,0x0307,0x030A,0x030B,0x030E,0x030F]:
                r = dev.read_data(reg)
                r &= 0xBF
                r |= enable[args.demod_persistence] << 6 
                dev.write_data(reg, r)
        elif args.ref == 'a':
            r = dev.read_data(0x0302)
            r &= 0xBF
            r |= enable[args.demod_persistence] << 6 
            dev.write_data(0x0302, r)
        elif args.ref == 'aa':
            r = dev.read_data(0x0303)
            r &= 0xBF
            r |= enable[args.demod_persistence] << 6 
            dev.write_data(0x0303, r)
        elif args.ref == 'b':
            r = dev.read_data(0x0306)
            r &= 0xBF
            r |= enable[args.demod_persistence] << 6 
            dev.write_data(0x0306, r)
        elif args.ref == 'bb':
            r = dev.read_data(0x0307)
            r &= 0xBF
            r |= enable[args.demod_persistence] << 6 
            dev.write_data(0x0307, r)
        elif args.ref == 'aux-0':
            r = dev.read_data(0x030A)
            r &= 0xBF
            r |= enable[args.demod_persistence] << 6 
            dev.write_data(0x030A, r)
        elif args.ref == 'aux-1':
            r = dev.read_data(0x030B)
            r &= 0xBF
            r |= enable[args.demod_persistence] << 6 
            dev.write_data(0x030B, r)
        elif args.ref == 'aux-2':
            r = dev.read_data(0x030E)
            r &= 0xBF
            r |= enable[args.demod_persistence] << 6 
            dev.write_data(0x030E, r)
        elif args.ref == 'bb':
            r = dev.read_data(0x030F)
            r &= 0xBF
            r |= enable[args.demod_persistence] << 6 
            dev.write_data(0x030F, r)
    
    if args.demod:
        enable = {
            'disable': 0,
            'enable': 1,
        }
        if args.ref == 'all':
            for reg in [0x0302,0x0303,0x0306,0x0307,0x030A,0x030B,0x030E,0x030F]:
                r = dev.read_data(reg)
                r &= 0xF7
                r |= enable[args.demod] << 3
                dev.write_data(reg, r)
        elif args.ref == 'a':
            r = dev.read_data(0x0302)
            r &= 0xF7
            r |= enable[args.demod] << 3
            dev.write_data(0x0302, r)
        elif args.ref == 'aa':
            r = dev.read_data(0x0303)
            r &= 0xF7
            r |= enable[args.demod] << 3
            dev.write_data(0x0303, r)
        elif args.ref == 'b':
            r = dev.read_data(0x0306)
            r &= 0xF7
            r |= enable[args.demod] << 3
            dev.write_data(0x0306, r)
        elif args.ref == 'bb':
            r = dev.read_data(0x0307)
            r &= 0xF7
            r |= enable[args.demod] << 3
            dev.write_data(0x0307, r)
        elif args.ref == 'aux-0':
            r = dev.read_data(0x030A)
            r &= 0xF7
            r |= enable[args.demod] << 3
            dev.write_data(0x030A, r)
        elif args.ref == 'aux-1':
            r = dev.read_data(0x030B)
            r &= 0xF7
            r |= enable[args.demod] << 3
            dev.write_data(0x030B, r)
        elif args.ref == 'aux-2':
            r = dev.read_data(0x030E)
            r &= 0xF7
            r |= enable[args.demod] << 3
            dev.write_data(0x030E, r)
        elif args.ref == 'aux-3':
            r = dev.read_data(0x030F)
            r &= 0xF7
            r |= enable[args.demod] << 3
            dev.write_data(0x030F, r)

    if args.freq:
        period = round(1E18/args.freq)
        r0 = period & 0xFF
        r1 = (period & 0xFF00)>>8
        r2 = (period & 0xFF0000)>>16
        r3 = (period & 0xFF000000)>>24
        r4 = (period & 0xFF00000000)>>32
        r5 = (period & 0xFF0000000000)>>40
        r6 = (period & 0xFF000000000000)>>48
        regs = []
        if args.ref == 'all' or args.ref == 'a':
            regs.append(0x0404) 
        if args.ref == 'all' or args.ref == 'aa':
            regs.append(0x0424)
        if args.ref == 'all' or args.ref == 'b':
            regs.append(0x0444)
        if args.ref == 'all' or args.ref == 'bb':
            regs.append(0x0464)
        if args.ref == 'all' or args.ref == 'aux-0':
            regs.append(0x0484)
        if args.ref == 'all' or args.ref == 'aux-1':
            regs.append(0x04A4)
        if args.ref == 'all' or args.ref == 'aux-2':
            regs.append(0x04C4)
        if args.ref == 'all' or args.ref == 'aux-3':
            regs.append(0x04E4)
        for reg in regs:
            dev.write_data(reg+0, r0)
            dev.write_data(reg+1, r1)
            dev.write_data(reg+2, r2)
            dev.write_data(reg+3, r3)
            dev.write_data(reg+4, r4)
            dev.write_data(reg+5, r5)
            dev.write_data(reg+6, r6 & 0xF)
    
    if args.phase_lock_thresh:
        value = round(args.phase_lock_thresh * 1E12)
        regs = []
        if args.ref == 'all' or args.ref == 'a':
            regs.append(0x0800)
        if args.ref == 'all' or args.ref == 'aa':
            regs.append(0x0820)
        if args.ref == 'all' or args.ref == 'b':
            regs.append(0x0840)
        if args.ref == 'all' or args.ref == 'bb':
            regs.append(0x0860)
        for reg in regs: 
            dev.write_data(reg+0, value & 0xFF)
            dev.write_data(reg+1, (value & 0xFF00)>>8)
            dev.write_data(reg+2, (value & 0xFF0000)>>16)
    if args.phase_step_thresh:
        value = round(args.phase_step_thresh * 1E12)
        regs = []
        if args.ref == 'all' or args.ref == 'a':
            regs.append(0x080A)
        if args.ref == 'all' or args.ref == 'aa':
            regs.append(0x082A)
        if args.ref == 'all' or args.ref == 'b':
            regs.append(0x084A)
        if args.ref == 'all' or args.ref == 'bb':
            regs.append(0x086A)
        for reg in regs: 
            dev.write_data(reg+0, value & 0xFF)
            dev.write_data(reg+1, (value & 0xFF00)>>8)
            dev.write_data(reg+2, (value & 0xFF0000)>>16)
            dev.write_data(reg+3, (value & 0xFF000000)>>24)
    if args.freq_lock_thresh:
        df = args.freq_lock_thresh
        regs = []
        freqs = []
        if args.ref == 'all' or args.ref == 'a':
            regs.append(0x0805)
            t = dev.read_data(0x0404)
            t += dev.read_data(0x0405) << 8
            t += dev.read_data(0x0406) << 16
            t += dev.read_data(0x0407) << 24
            t += dev.read_data(0x0408) << 32
            t += dev.read_data(0x0409) << 40
            t += dev.read_data(0x040A) << 48
            t += (dev.read_data(0x040B)&0x0F) << 56
            f = 1E18/t
            freqs.append(f)
        if args.ref == 'all' or args.ref == 'aa':
            regs.append(0x0825)
        if args.ref == 'all' or args.ref == 'b':
            regs.append(0x0845)
        if args.ref == 'all' or args.ref == 'bb':
            regs.append(0x0865)
        for reg in range(len(regs)): 
            value = round((df/freqs[i])*1/(freqs[i]+df)) 
            dev.write_data(regs[i]+0, value & 0xFF)
            dev.write_data(regs[i]+1, (value & 0xFF00)>>8)
            dev.write_data(regs[i]+2, (value & 0xFF0000)>>16)
            dev.write_data(regs[i]+3, (value & 0xFF000000)>>24)

    dev.io_update()

if __name__ == "__main__":
    main(sys.argv[1:])
