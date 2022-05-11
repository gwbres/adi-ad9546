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
from ad9546 import *
def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 clock distribution tool")
    parser.add_argument(
        "bus",
        type=int,
        help="I2C bus (int)",
    )
    parser.add_argument(
        "address",
        type=str,
        help="I2C slv address (hex)",
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
        "--path",
        metavar="path",
        choices=["a","b","aa","bb","c","cc","all"],
        default="all",
        type=str,
        help="Select path between [A, B, AA, BB, (and C, CC when feasible), or all (all existing)]",
    )
    parser.add_argument(
        "--pin",
        metavar="pin",
        choices=['+','-','all'],
        type=str,
        default='all',
        help='Select +/- pin if needed, when targetting an output pin',
    )
    flags = [
        ("sync-all", None, [], """Synchronize all distribution dividers.
        If output behavior is not set to `immediate`, one must run a `sync-all` to
        output a synthesis."""),
        ('format', str, ['cml','hcsl'], u"""Select driver format for OUTx where x = chnnal.
        CML: Current Sink. External 50\u03A9 pull up needed.
        HCSL: External 50\u03A9 pull down needed."""),
        ('current', str, ['7.5mA','12.5mA','15mA'], 'Set driver output current [mA] for OUTx, where x = channel'),
        ('mode', str, ['diff','se','sedd'], """Select between Differential, Single Ended or
        Single Ended Dual Divider for OUTx path, where x = channel"""),
        ('autosync', str, ['manual', 'immediate','phase','freq'], 'Set PLLx drivers output mode, where x = channel. Refer to README & datasheet.'),
        ('unmuting', str, ['immediate', 'hitless', 'phase', 'freq'], 'Set PLLx distribution unmuting opmode, where x = channel. Refer to README & datasheet.'),
        ('divider', int, [], 'Control Qxy division ratio, where x = channel, y = path. Refer to README & datasheet.'),
        ('phase-offset', int, [], 'Apply inst. phase offset to Qxy output path'),
        ('half-divider', str, ['enable','disable'], 'Control Qxy Half integer divider'),
        ('q-sync', None, [], 'Initialize a sync sequence on Q div. stage manually. Refer to README & datasheet.'),
        ('pwm', str, ['enable','disable'],  'Control Qxy PWM modulator, where x = channel, y = output path'),
        ('mute', None, [],   'Mute OUTxy+/- output path, x = channel, y = path and optionnal pin'),
        ('unmute', None, [], 'Unmute OUTxy+/- output path, x = channel, y = path and optionnal pin'),
    ]
    
    for (v_label, v_type, v_choices, v_helper) in flags:
        if v_type is None:
            parser.add_argument(
                "--{}".format(v_label),
                action="store_true",
                help=v_helper,
            )
        else:
            if len(v_choices) > 0:
                parser.add_argument(
                    "--{}".format(v_label),
                    choices=v_choices,
                    type=v_type,
                    help=v_helper,
                )
            else:
                parser.add_argument(
                    "--{}".format(v_label),
                    type=v_type,
                    help=v_helper,
                )
    args = parser.parse_args(argv)
    # open device
    dev = AD9546(args.bus, int(args.address, 16))

    # Special Flags
    if args.sync_all:
        r = dev.read_data(0x2000)
        dev.write_data(0x2000, r|0x08)
        dev.io_update()
        return 0 # force stop, avoids possible corruption when mishandling this script

    autosyncs = {
        'manual': 0,
        'immediate': 1,
        'phase': 2,
        'freq': 3,
    }

    if args.autosync:
        mask = 0x03
        if args.channel == '0':
            r = dev.read_data(0x10DB)
            r &= (mask^0xFF) # mask out
            dev.write_data(0x10DB, r | autosyncs[args.autosync])
            dev.io_update()
        elif args.channel == '1':
            r = dev.read_data(0x14DB)
            r &= (mask^0xFF) # mask out
            dev.write_data(0x14DB, r | autosyncs[args.autosync])
            dev.io_update()
        else: # all
            r = dev.read_data(0x10DB)
            r &= (mask^0xFF) # mask out
            dev.write_data(0x10DB, r | autosyncs[args.autosync])
            r = dev.read_data(0x14DB)
            r &= (mask^0xFF) # mask out
            dev.write_data(0x14DB, r | autosyncs[args.autosync])
            dev.io_update()
        return 0 # force stop, to avoid corruption on misusage

    if args.format:
        regs = []
        formats = {
            'cml': 0,
            'hcsl': 1,
        }
        if args.channel == 'all':
            if args.path == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9, 0x14D7, 0x14D8]
            elif args.path == 'a':
                regs = [0x10D7]
            elif args.path == 'b':
                regs = [0x10D8]
            elif args.path == 'c':
                regs = [0x10D9]
        elif args.channel == '0':
            if args.path == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9]
            elif args.path == 'a':
                regs = [0x10D7]
            elif args.path == 'b':
                regs = [0x10D8]
            elif args.path == 'c':
                regs = [0x10D9]
        elif args.channel == '1':
            if args.path == 'all':
                regs = [0x14D7, 0x14D8]
            elif args.path == 'a':
                regs = [0x14D7]
            elif args.path == 'b':
                regs = [0x14D8]
        for reg in regs:
            r = dev.read_data(reg)
            r &= 0xFE # mask out
            dev.write_data(reg, r | formats[args.format])
        dev.io_update()
        return 0 # force stop, to avoid corruption on misusage
            
    if args.current:
        regs = []
        currents = {
            '7.5mA': 0,
            '12.5mA': 1,
            '15mA': 2,
        }
        if args.channel == 'all':
            if args.path == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9, 0x14D7, 0x14D8]
            elif args.path == 'a':
                regs = [0x10D7]
            elif args.path == 'b':
                regs = [0x10D8]
            elif args.path == 'c':
                regs = [0x10D9]
        elif args.channel == '0':
            if args.path == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9]
            elif args.path == 'a':
                regs = [0x10D7]
            elif args.path == 'b':
                regs = [0x10D8]
            elif args.path == 'c':
                regs = [0x10D9]
        elif args.channel == '1':
            if args.path == 'all':
                regs = [0x14D7, 0x14D8]
            elif args.path == 'a':
                regs = [0x14D7]
            elif args.path == 'b':
                regs = [0x14D8]
        for reg in regs:
            r = dev.read_data(reg)
            mask = (0x03)<<1
            r &= (mask ^0xFF) #mask out
            dev.write_data(reg, r | (currents[args.current]<<1))
        dev.io_update()
        return 0 # force stop, to avoid corruption on misusage
    
    if args.mode:
        regs = []
        modes = {
            'diff': 0,
            'se': 1,
            'sedd': 2,
        }
        mask = 0x03 << 3
        if args.channel == 'all':
            if args.path == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9, 0x14D7, 0x14D8]
            elif args.path == 'a':
                regs = [0x10D7]
            elif args.path == 'b':
                regs = [0x10D8]
            elif args.path == 'c':
                regs = [0x10D9]
        elif args.channel == '0':
            if args.path == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9]
            elif args.path == 'a':
                regs = [0x10D7]
            elif args.path == 'b':
                regs = [0x10D8]
            elif args.path == 'c':
                regs = [0x10D9]
        elif args.channel == '1':
            if args.path == 'all':
                regs = [0x14D7, 0x14D8]
            elif args.path == 'a':
                regs = [0x14D7]
            elif args.path == 'b':
                regs = [0x14D8]
        for reg in regs:
            r = dev.read_data(reg)
            r &= (mask ^0xFF)
            dev.write_data(reg, r | (modes[args.mode] << 3))
        dev.io_update()
        return 0 # force stop, to avoid corruption on misusage
    if args.phase_offset:
        regs = []
        r0 = args.phase_offset & 0xFF
        r1 = (args.phase_offset & 0xFF00)>>8
        r2 = (args.phase_offset & 0xFF0000)>>16
        r3 = (args.phase_offset & 0xFF000000)>>24
        r4 = (args.phase_offset &0x100000000)>>32
        if args.channel == 'all':
            if args.path == 'all':
                regs = [0x1104, 0x110D, 0x1116, 0x111F, 0x1128, 0x1131, 0x1504, 0x150D, 0x1516, 0x151F]
            elif args.path == 'a':
                regs = [0x1104, 0x1504]
            elif args.path == 'aa':
                regs = [0x110D, 0x150D]
            elif args.path == 'b':
                regs = [0x1116, 0x1516]
            elif args.path == 'bb':
                regs = [0x111F, 0x151F]
            elif args.path == 'c':
                regs = [0x1128]
            elif args.path == 'cc':
                regs = [0x1131]
        elif args.channel == '0':
            if args.path == 'all':
                regs = [0x1104, 0x110D, 0x1116, 0x111F, 0x1128, 0x1131]
            elif args.path == 'a':
                regs = [0x1104]
            elif args.path == 'aa':
                regs = [0x110D]
            elif args.path == 'b':
                regs = [0x1116]
            elif args.path == 'bb':
                regs = [0x111F]
            elif args.path == 'c':
                regs = [0x1128]
            elif args.path == 'cc':
                regs = [0x1131]
        elif args.channel == '1': 
            if args.path == 'all':
                regs = [0x1504, 0x150D, 0x1516, 0x151F]
            elif args.path == 'a':
                regs = [0x1504]
            elif args.path == 'aa':
                regs = [0x150D]
            elif args.path == 'b':
                regs = [0x1516]
            elif args.path == 'bb':
                regs = [0x151F]
 
        for reg in regs:
            dev.write_data(reg+0, r0)
            dev.write_data(reg+1, r1)
            dev.write_data(reg+2, r2)
            dev.write_data(reg+3, r3)
            r = dev.read_data(reg+4)
            r &= 0xBF # mask 1 bit out
            dev.write_data(reg+4, r | ((r4 & 0x01)<<6))
        dev.io_update()
        return 0 # force stop, to avoid corruption on misusage

    if args.divider:
        regs = []
        r0 = args.divider & 0xFF
        r1 = (args.divider & 0xFF00)>>8
        r2 = (args.divider & 0xFF0000)>>16
        r3 = (args.divider & 0xFF000000)>>24
        if args.channel == 'all':
            if args.path == 'all':
                regs = [0x1100, 0x1109, 0x1112, 0x111B, 0x1124, 0x112D, 0x1500, 0x1509, 0x1512, 0x151B]
            elif args.path == 'a':
                regs = [0x1100]
            elif args.path == 'aa':
                regs = [0x1109]
            elif args.path == 'b':
                regs = [0x1112]
            elif args.path == 'bb':
                regs = [0x111B]
            elif args.path == 'c':
                regs = [0x1124]
            elif args.path == 'cc':
                regs = [0x112D]
        elif args.channel == '0':
            if args.path == 'all':
                regs = [0x1100, 0x1109, 0x1112, 0x111B, 0x1124, 0x112D]
            elif args.path == 'a':
                regs = [0x1100]
            elif args.path == 'aa':
                regs = [0x1109]
            elif args.path == 'b':
                regs = [0x1112]
            elif args.path == 'bb':
                regs = [0x111B]
            elif args.path == 'c':
                regs = [0x1124]
            elif args.path == 'cc':
                regs = [0x112D]
        elif args.channel == '1':
            if args.path == 'all':
                regs = [0x1500, 0x1509, 0x1512, 0x151B]
            elif args.path == 'a':
                regs = [0x1500]
            elif args.path == 'aa':
                regs = [0x1509]
            elif args.path == 'b':
                regs = [0x1512]
            elif args.path == 'bb':
                regs = [0x151B]
        for r in regs:
            dev.write_data(r+0, r0)
            dev.write_data(r+1, r1)
            dev.write_data(r+2, r2)
            dev.write_data(r+3, r3)
        dev.io_update()
        return 0 # force stop, to avoid corruption on misusage

    if args.q_sync:
        if args.channel == '0':
            r = dev.read_data(0x2101)
            dev.write_data(0x2101, r|0x08) # assert
            dev.io_update()
            dev.write_data(0x2101, r|0xF7) # clear
            dev.io_update()
        elif args.channel == '1':
            r = dev.read_data(0x2201)
            dev.write_data(0x2201, r|0x08) # assert
            dev.io_update()
            dev.write_data(0x2201, r|0xF7) # clear
            dev.io_update()
        else: # all
            r = dev.read_data(0x2101)
            dev.write_data(0x2101, r|0x08) # assert
            dev.io_update()
            dev.write_data(0x2101, r|0xF7) # clear
            dev.io_update()
            r = dev.read_data(0x2201)
            dev.write_data(0x2201, r|0x08) # assert
            dev.io_update()
            dev.write_data(0x2201, r|0xF7) # clear
            dev.io_update()
        return 0 # force stop, to avoid corruption on misusage
    
    if args.unmuting:
        mask = 0x03
        unmutings = {
            'immediate': 0,
            'hitless': 1,
            'phase': 2,
            'freq': 3,
        }
        if args.unmuting == 'hitless':
            value = 0x01
        elif args.unmuting == 'phase':
            value = 0x02
        elif args.unmuting == 'freq':
            value = 0x03
        if args.channel == 'all':
            r = dev.read_data(0x10DC)
            r &= (mask ^0xFF) # mask out
            dev.write_data(0x10DC, r | unmutings[args.unmuting])
            r = dev.read_data(0x14DC)
            r &= (mask ^0xFF) # mask out
            dev.write_data(0x14DC, r | unmutings[args.unmuting])
            dev.io_update()
            
        elif args.channel == '0':
            r = dev.read_data(0x10DC)
            r &= (mask ^0xFF) # mask out
            dev.write_data(0x10DC, r | unmutings[args.unmuting])
            dev.io_update()
        elif args.channel == '1':
            r = dev.read_data(0x14DC)
            r &= (mask ^0xFF) # mask out
            dev.write_data(0x14DC, r | unmutings[args.unmuting])
            dev.io_update()
        return 0 # force stop, to avoid corruption on misusage

    if args.pwm:
        regs = []
        if args.channel == 'all':
            if args.path == 'all':
                regs = [0x10CF, 0x10D0]
            elif args.path == 'a':
                regs = [0x10CF]
            elif args.path == 'b':
                regs = [0x10D0]
        elif args.channel == '0':
            if args.path == 'all':
                regs = [0x10CF, 0x10D0]
            elif args.path == 'a':
                regs = [0x10CF]
            elif args.path == 'b':
                regs = [0x10D0]
        elif args.channel == '1':
            if args.path == 'all':
                regs = [0x14CF, 0x14D0]
            elif args.path == 'a':
                regs = [0x14CF]
            elif args.path == 'b':
                regs = [0x14D0]
        for reg in regs:
            r = dev.read_data(reg)
            if args.pwm == 'enable':
                dev.write_data(r|0x01)
            else:
                dev.write_data(r&0xFE)
        dev.io_update()
        return 0 # force stop, to avoid corruption on misusage
    
    if args.half_divider:
        regs = []
        if args.channel == 'all':
            if args.path == 'all':
                regs = [0x1108, 0x1111, 0x111A, 0x1123, 0x112C, 0x1135, 0x1508, 0x1511, 0x151A, 0x1523] 
            elif args.path == 'a':
                regs = [0x1108] 
            elif args.path == 'aa':
                regs = [0x1111] 
            elif args.path == 'b':
                regs = [0x111A] 
            elif args.path == 'bb':
                regs = [0x1123] 
            elif args.path == 'c':
                regs = [0x112C] 
            elif args.path == 'cc':
                regs = [0x1135] 
        elif args.channel == '0':
            if args.path == 'all':
                regs = [0x1108, 0x1111, 0x111A, 0x1123, 0x112C, 0x1135]
            elif args.path == 'a':
                regs = [0x1108] 
            elif args.path == 'aa':
                regs = [0x1111] 
            elif args.path == 'b':
                regs = [0x111A] 
            elif args.path == 'bb':
                regs = [0x1123] 
            elif args.path == 'c':
                regs = [0x112C] 
            elif args.path == 'cc':
                regs = [0x1135] 
        elif args.channel == '1':
            if args.path == 'all':
                regs = [0x1508, 0x1511, 0x151A, 0x1523] 
            elif args.path == 'a':
                regs = [0x1508]
            elif args.path == 'aa':
                regs = [0x1511]
            elif args.path == 'b':
                regs = [0x151A]
            elif args.path == 'bb':
                regs = [0x1523]
        
        for reg in regs:
            r = dev.read_data(reg)
            if args.half_divider == 'enable':
                dev.write_data(reg, r|0x10) # assign
            else:
                dev.write_data(reg, r&0xEF) # mask out
        dev.io_update()
        return 0 # force stop, to avoid corruption on misusage

    if args.mute or args.unmute:
        if args.channel == 'all':
            if args.path == 'all':
                if args.pin == 'all':
                    base = 0x2101
                    for ch in ['ch0','ch1']:
                        r = dev.read_data(base)
                        if args.mute:
                            dev.write_data(base, r|0x02) # assign
                        else:
                            dev.write_data(base, r&0xFD) # mask out
                        base += 0x100
                elif args.pin == '+':
                    base = 0x2102
                    for ch in ['ch0','ch1']:
                        paths = ['a','b']
                        if ch == 'ch0':
                            paths.append('c')
                        reg = base
                        for path in paths: 
                            r = dev.read_data(reg)
                            if args.mute:
                                dev.write_data(r|0x04) # assign
                            elif args.unmute:
                                dev.write_data(r&0xFB) # assign
                            reg += 1
                        base += 0x100
                elif args.pin == '-':
                    base = 0x2102
                    for ch in ['ch0','ch1']:
                        paths = ['a','b']
                        if ch == 'ch0':
                            paths.append('c')
                        reg = base
                        for path in paths: 
                            r = dev.read_data(reg)
                            if args.mute:
                                dev.write_data(r|0x08) # assign
                            elif args.unmute:
                                dev.write_data(r&0xF7) # assign
                            reg += 1
                        base += 0x100
        elif args.channel == '0':
            if args.path == 'all':
                if args.pin == 'all':
                    base = 0x2101
                    r = dev.read_data(base)
                    if args.mute:
                        dev.write_data(base, r|0x02) # assign
                    else:
                        dev.write_data(base, r&0xFD) # mask out
                elif args.pin == '+':
                    base = 0x2102
                    paths = ['a','b','c']
                    for path in paths: 
                        r = dev.read_data(base)
                        if args.mute:
                            dev.write_data(r|0x04)
                        elif args.unmute:
                            dev.write_data(r&0xFB)
                        base += 1
                elif args.pin == '-':
                    base = 0x2102
                    paths = ['a','b','c']
                    for path in paths: 
                        r = dev.read_data(base)
                        if args.mute:
                            dev.write_data(r|0x08)
                        elif args.unmute:
                            dev.write_data(r&0xF7)
                        base += 1
        elif args.channel == '1':
            if args.path == 'all':
                if args.pin == 'all':
                    base = 0x2201
                    r = dev.read_data(base)
                    if args.mute:
                        dev.write_data(base, r|0x02)
                    else:
                        dev.write_data(base, r&0xFD)
                elif args.pin == '+':
                    base = 0x2202
                    paths = ['a','b']
                    for path in paths: 
                        r = dev.read_data(base)
                        if args.mute:
                            dev.write_data(r|0x04)
                        elif args.unmute:
                            dev.write_data(r&0xFB)
                        base += 1
                elif args.pin == '-':
                    base = 0x2202
                    paths = ['a','b']
                    for path in paths: 
                        r = dev.read_data(base)
                        if args.mute:
                            dev.write_data(r|0x08)
                        elif args.unmute:
                            dev.write_data(r&0xF7)
                        base += 1
        dev.io_update()
        return 0 # force stop, to avoid corruption on misusage

if __name__ == "__main__":
    main(sys.argv[1:])
