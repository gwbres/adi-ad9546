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
    parser = argparse.ArgumentParser(description="AD9545/46 clock distribution tool")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
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
        "--pin",
        metavar="pin",
        choices=["a","b","aa","bb","c","cc","all"],
        default="all",
        type=str,
        help="Select pin between [A, B, AA, BB, (and C, CC when feasible), or all (all existing)]",
    )
    flags = [
        ("sync-all", None, [], """Synchronize all distribution dividers.
        If output behavior is not set to `immediate`, one must run a `sync-all` to
        output a synthesis."""),
        ('format', str, ['cml','hcsl'], u"""Select driver format for OUTx where x = chnnal.
        CML: Current Sink. External 50\u03A9 pull up needed.
        HCSL: External 50\u03A9 pull down needed."""),
        ('current', float, [7.5,12.5,15], 'Set driver output current [mA] for OUTx, where x = channel'),
        ('mode', str, ['diff','se','sedd'], """Select between Differential, Single Ended or
        Single Ended Dual Divider for OUTx pin, where x = channel"""),
        ('autosync', str, ['manual', 'immediate','phase','freq'], 'Set PLLx drivers output mode, where x = channel. Refer to README & datasheet.'),
        ('unmute', str, ['immediate', 'hitless', 'phase', 'freq'], 'Set PLLx distribution unmuting opmode, where x = channel. Refer to README & datasheet.'),
        ('divider', int, [], 'Control Qxy division ratio, where x = channel, y = pin. Refer to README & datasheet.'),
        ('phase-offset', int, [], 'Apply inst. phase offset to Qxy output pin'),
        ('half-divider', str, ['enable','disable'], 'Control Qxy Half integer divider'),
        ('q-sync', None, [], 'Initialize a sync sequence on Q div. stage manually. Refer to README & datasheet.'),
        ('pwm', str, ['enable','disable'],  'Control OUTxy PWM modulator, where x = channel, y = output pin'),
    ]
    
    for (v_label, v_type, v_choices, v_helper) in flags:
        if v_type is None:
            parser.add_argument(
                "--{}".format(v_label),
                action="store_true",
                help=v_helper,
            )
        else:
            parser.add_argument(
                "--{}".format(v_label),
                choices=v_choices,
                type=v_type,
                help=v_helper,
            )
    args = parser.parse_args(argv)
    
    core = args.core
    channel = args.channel

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    # Special Flags
    if args.sync_all:
        r = read_data(handle, address, 0x2000)
        write_data(handle, address, 0x2000, reg | 0x08)
        write_data(handle, address, 0x000F, 0x01) # IO update
        return 0 # force stop, avoids possible corruption when mishandling this script

    if args.autosync:
        value = 0x00
        if args.auto_sync == 'immediate':
            value = 0x01
        if args.auto_sync == 'phase':
            value = 0x02
        if args.auto_sync == 'freq':
            value = 0x03
        if args.channel == '0':
            reg = read_data(handle, address, 0x10DB)
            write_data(handle, address, 0x10DB, reg|value)
            write_data(handle, address, 0x000F, 0x01) # IO update
        elif args.channel == '1':
            reg = read_data(handle, address, 0x14DB)
            write_data(handle, address, 0x14DB, reg|value)
            write_data(handle, address, 0x000F, 0x01) # IO update
        else: # all
            reg = read_data(handle, address, 0x10DB)
            write_data(handle, address, 0x10DB, reg|value)
            reg = read_data(handle, address, 0x14DB)
            write_data(handle, address, 0x14DB, reg|value)
            write_data(handle, address, 0x000F, 0x01) # IO update
        return 0 # force stop, to avoid corruption on misusage

    if args.format:
        regs = []
        value = 0x00 if args.format == 'cml' else 0x01 # hcsl
        if args.channel == 'all':
            if args.pin == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9, 0x14D7, 0x14D8]
            elif args.pin == 'a':
                regs = [0x10D7]
            elif args.pin == 'b':
                regs = [0x10D8]
            elif args.pin == 'c':
                regs = [0x10D9]
        elif args.channel == '0':
            if args.pin == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9]
            elif args.pin == 'a':
                regs = [0x10D7]
            elif args.pin == 'b':
                regs = [0x10D8]
            elif args.pin == 'c':
                regs = [0x10D9]
        elif args.channel == '1':
            if args.pin == 'all':
                regs = [0x14D7, 0x14D8]
            elif args.pin == 'a':
                regs = [0x14D7]
            elif args.pin == 'b':
                regs = [0x14D8]
        for reg in regs:
            r = read_data(handle, address, reg)
            r &= 0xFE # mask out
            r |= value # assign
            write_data(handle, address, reg, r) 
        write_data(handle, address, 0x000F, 0x01) # IO update
        return 0 # force stop, to avoid corruption on misusage
            
    if args.current:
        regs = []
        if args.current == 12.5:
            value = 0x01
        elif args.current == 15:
            value = 0x02
        else:
            value = 0x00
        if args.channel == 'all':
            if args.pin == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9, 0x14D7, 0x14D8]
            elif args.pin == 'a':
                regs = [0x10D7]
            elif args.pin == 'b':
                regs = [0x10D8]
            elif args.pin == 'c':
                regs = [0x10D9]
        elif args.channel == '0':
            if args.pin == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9]
            elif args.pin == 'a':
                regs = [0x10D7]
            elif args.pin == 'b':
                regs = [0x10D8]
            elif args.pin == 'c':
                regs = [0x10D9]
        elif args.channel == '1':
            if args.pin == 'all':
                regs = [0x14D7, 0x14D8]
            elif args.pin == 'a':
                regs = [0x14D7]
            elif args.pin == 'b':
                regs = [0x14D8]
        for reg in regs:
            r = read_data(handle, address, reg)
            r &= 0xF9 # mask out
            r |= (value <<1) # assign
            write_data(handle, address, reg, r)
        write_data(handle, address, 0x000F, 0x01) # IO update
        return 0 # force stop, to avoid corruption on misusage
    
    if args.mode:
        regs = []
        if args.mode == 'se':
            value = 0x01
        elif args.mode == 'sedd':
            value = 0x02
        else: # diff
            value = 0x00
        if args.channel == 'all':
            if args.pin == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9, 0x14D7, 0x14D8]
            elif args.pin == 'a':
                regs = [0x10D7]
            elif args.pin == 'b':
                regs = [0x10D8]
            elif args.pin == 'c':
                regs = [0x10D9]
        elif args.channel == '0':
            if args.pin == 'all':
                regs = [0x10D7, 0x10D8, 0x10D9]
            elif args.pin == 'a':
                regs = [0x10D7]
            elif args.pin == 'b':
                regs = [0x10D8]
            elif args.pin == 'c':
                regs = [0x10D9]
        elif args.channel == '1':
            if args.pin == 'all':
                regs = [0x14D7, 0x14D8]
            elif args.pin == 'a':
                regs = [0x14D7]
            elif args.pin == 'b':
                regs = [0x14D8]
        for reg in regs:
            r = read_data(handle, address, reg)
            r &= 0xF9 # mask out
            r |= (value <<1) # assign
            write_data(handle, address, reg, r)
        write_data(handle, address, 0x000F, 0x01) # IO update
        return 0 # force stop, to avoid corruption on misusage
    if args.phase_offset:
        regs = []
        r0 = args.phase_offset & 0xFF
        r1 = (args.phase_offset & 0xFF00)>>8
        r2 = (args.phase_offset & 0xFF0000)>>16
        r3 = (args.phase_offset & 0xFF000000)>>24
        r4 = (args.phase_offset &0x100000000)>>32
        if args.channel == 'all':
            if args.pin == 'all':
                regs = [0x1104, 0x110D, 0x1116, 0x111F, 0x1128, 0x1131, 0x1504, 0x150D, 0x1516, 0x151F]
            elif args.pin == 'a':
                regs = [0x1104, 0x1504]
            elif args.pin == 'aa':
                regs = [0x110D, 0x150D]
            elif args.pin == 'b':
                regs = [0x1116, 0x1516]
            elif args.pin == 'bb':
                regs = [0x111F, 0x151F]
            elif args.pin == 'c':
                regs = [0x1128]
            elif args.pin == 'cc':
                regs = [0x1131]
        elif args.channel == '0':
            if args.pin == 'all':
                regs = [0x1104, 0x110D, 0x1116, 0x111F, 0x1128, 0x1131]
            elif args.pin == 'a':
                regs = [0x1104]
            elif args.pin == 'aa':
                regs = [0x110D]
            elif args.pin == 'b':
                regs = [0x1116]
            elif args.pin == 'bb':
                regs = [0x111F]
            elif args.pin == 'c':
                regs = [0x1128]
            elif args.pin == 'cc':
                regs = [0x1131]
        elif args.channel == '1': 
            if args.pin == 'all':
                regs = [0x1504, 0x150D, 0x1516, 0x151F]
            elif args.pin == 'a':
                regs = [0x1504]
            elif args.pin == 'aa':
                regs = [0x150D]
            elif args.pin == 'b':
                regs = [0x1516]
            elif args.pin == 'bb':
                regs = [0x151F]
            
        for reg in regs:
            write_data(handle, address, reg, r0) 
            write_data(handle, address, reg+1, r1) 
            write_data(handle, address, reg+2, r2) 
            write_data(handle, address, reg+3, r3) 
            r = read_data(handle, address, reg+4)
            write_data(handle, address, reg+4, r | ((r4 & 0x01)<<6))
        write_data(handle, address, 0x000F, 0x01) # IO update
        return 0 # force stop, to avoid corruption on misusage

    if args.divider:
        regs = []
        r0 = args.divider & 0xFF
        r1 = (args.divider & 0xFF00)>>8
        r2 = (args.divider & 0xFF0000)>>16
        r3 = (args.divider & 0xFF000000)>>24
        if args.channel == 'all':
            if args.pin == 'all':
                regs = [0x1100, 0x1109, 0x1112, 0x111B, 0x1124, 0x112D, 0x1500, 0x1509, 0x1512, 0x151B]
            elif args.pin == 'a':
                regs = [0x1100]
            elif args.pin == 'aa':
                regs = [0x1109]
            elif args.pin == 'b':
                regs = [0x1112]
            elif args.pin == 'bb':
                regs = [0x111B]
            elif args.pin == 'c':
                regs = [0x1124]
            elif args.pin == 'cc':
                regs = [0x112D]
        elif args.channel == '0':
            if args.pin == 'all':
                regs = [0x1100, 0x1109, 0x1112, 0x111B, 0x1124, 0x112D]
            elif args.pin == 'a':
                regs = [0x1100]
            elif args.pin == 'aa':
                regs = [0x1109]
            elif args.pin == 'b':
                regs = [0x1112]
            elif args.pin == 'bb':
                regs = [0x111B]
            elif args.pin == 'c':
                regs = [0x1124]
            elif args.pin == 'cc':
                regs = [0x112D]
        elif args.channel == '1':
            if args.pin == 'all':
                regs = [0x1500, 0x1509, 0x1512, 0x151B]
            elif args.pin == 'a':
                regs = [0x1500]
            elif args.pin == 'aa':
                regs = [0x1509]
            elif args.pin == 'b':
                regs = [0x1512]
            elif args.pin == 'bb':
                regs = [0x151B]
        for r in regs:
            write_data(handle, address, r+0, r0)
            write_data(handle, address, r+1, r1)
            write_data(handle, address, r+2, r2)
            write_data(handle, address, r+3, r3)
        write_data(handle, address, 0x000F, 0x01) # IO update
        return 0 # force stop, to avoid corruption on misusage

    if args.q_sync:
        if args.channel == '0':
            reg = read_data(handle, address, 0x2101)
            write_data(handle, address, 0x2101, reg|0x08) # assert
            write_data(handle, address, 0x000F, 0x01) # IO update
            write_data(handle, address, 0x2101, reg|0xF7) # clear
            write_data(handle, address, 0x000F, 0x01) # IO update
        elif args.channel == '1':
            reg = read_data(handle, address, 0x2201)
            write_data(handle, address, 0x2201, reg|0x08) # assert
            write_data(handle, address, 0x000F, 0x01) # IO update
            write_data(handle, address, 0x2201, reg|0xF7) # clear
            write_data(handle, address, 0x000F, 0x01) # IO update
        else: # all
            reg = read_data(handle, address, 0x2101)
            write_data(handle, address, 0x2101, reg|0x08) # assert
            write_data(handle, address, 0x000F, 0x01) # IO update
            write_data(handle, address, 0x2101, reg|0xF7) # clear
            write_data(handle, address, 0x000F, 0x01) # IO update
            reg = read_data(handle, address, 0x2201)
            write_data(handle, address, 0x2201, reg|0x08) # assert
            write_data(handle, address, 0x000F, 0x01) # IO update
            write_data(handle, address, 0x2201, reg|0xF7) # clear
            write_data(handle, address, 0x000F, 0x01) # IO update
    
    if args.unmute:
        value = 0x00
        if args.unmute == 'hitless':
            value = 0x01
        elif args.unmute == 'phase':
            value = 0x02
        elif args.unmute == 'freq':
            value = 0x03
        if args.channel == 'all':
            reg = read_data(handle, address, 0x10DC) & 0xFC
            write_data(handle, address, 0x10DC, reg | value)
            reg = read_data(handle, address, 0x14DC) & 0xFC
            write_data(handle, address, 0x14DC, reg | value)
            write_data(handle, address, 0x000F, 0x01) # IO update
            
        elif args.channel == '0':
            reg = read_data(handle, address, 0x10DC) & 0xFC
            write_data(handle, address, 0x10DC, reg | value)
            write_data(handle, address, 0x000F, 0x01) # IO update
        elif args.channel == '1':
            reg = read_data(handle, address, 0x14DC) & 0xFC
            write_data(handle, address, 0x14DC, reg | value)
            write_data(handle, address, 0x000F, 0x01) # IO update

    if args.pwm:
        regs = []
        if args.channel == 'all':
            if args.pin == 'all':
                regs = [0x10CF, 0x10D0]
            elif args.pin == 'a':
                regs = [0x10CF]
            elif args.pin == 'b':
                regs = [0x10D0]
        elif args.channel == '0':
            if args.pin == 'all':
                regs = [0x10CF, 0x10D0]
            elif args.pin == 'a':
                regs = [0x10CF]
            elif args.pin == 'b':
                regs = [0x10D0]
        elif args.channel == '1':
            if args.pin == 'all':
                regs = [0x14CF, 0x14D0]
            elif args.pin == 'a':
                regs = [0x14CF]
            elif args.pin == 'b':
                regs = [0x14D0]
        for reg in regs:
            r = read_data(handle, address, reg)
            if args.pwm == 'enable':
                write_data(handle, address, r|0x01)
            else:
                write_data(handle, address, r&0xFE)
        write_data(handle, address, 0x000F, 0x01) # IO update
    
    if args.half_divider:
        regs = []
        if args.channel == 'all':
            if args.pin == 'all':
                regs = [0x1108, 0x111A, 0x1111, 0x111A, 0x1123, 0x112C, 0x1135] 
            elif args.pin == 'a':
                regs = [0x1108] 
            elif args.pin == 'aa':
                regs = [0x1111] 
            elif args.pin == 'b':
                regs = [0x111A] 
            elif args.pin == 'bb':
                regs = [0x1123] 
            elif args.pin == 'c':
                regs = [0x112C] 
            elif args.pin == 'cc':
                regs = [0x1135] 
        elif args.channel == '0':
            if args.pin == 'all':
                regs = [0x1108, 0x111A, 0x1111, 0x111A, 0x1123, 0x112C, 0x1135]
            elif args.pin == 'a':
                regs = [0x1108] 
            elif args.pin == 'aa':
                regs = [0x1111] 
            elif args.pin == 'b':
                regs = [0x111A] 
            elif args.pin == 'bb':
                regs = [0x1123] 
            elif args.pin == 'c':
                regs = [0x112C] 
            elif args.pin == 'cc':
                regs = [0x1135] 
        elif args.channel == '1':
            if args.pin == 'all':
                regs = [0x1508, 0x1511, 0x151A, 0x1523] 
            elif args.pin == 'a':
                regs = [0x1508]
            elif args.pin == 'aa':
                regs = [0x1511]
            elif args.pin == 'b':
                regs = [0x151A]
            elif args.pin == 'bb':
                regs = [0x1523]

        for reg in regs:
            r = read_data(handle, address, reg)
            if args.half_divider == 'enable':
                write_data(handle, address, reg, r|0x10)
            else:
                write_data(handle, address, reg, r&0xEF)

if __name__ == "__main__":
    main(sys.argv[1:])
