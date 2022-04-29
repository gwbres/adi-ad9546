#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# status.py: AD9546,45 status monitor (read only)
#################################################################
import sys
import math
import json
import argparse
from smbus import SMBus

def read_data (handle, dev, addr):
    msb = (addr & 0xFF00)>>8
    lsb = addr & 0xFF
    handle.write_i2c_block_data(dev, msb, [lsb])
    data = handle.read_byte(dev)
    return data
def bitfield (data, mask):
    return int((data & mask) >> int(math.log2(mask))) 
def read_reg (handle, dev, status, reg, addr, bitfields):
    if not reg in status:
        status[reg] = {}
    data = read_data(handle, dev, addr)
    for b in bitfields:
        status[reg][b[0]] = bitfield(data, b[1])

def filter_by_key (tree, key):
    ret = {} 
    for k in tree.keys():
        if type(tree[k]) is dict:
            if k == key: # top branch of interest
                # => plain copy
                ret[k] = tree[k].copy()
            else: # top branch, not filtered
                # ==> inner filter ?
                retained = filter_by_key(tree[k], key)
                got_something = len(retained.keys()) > 0
                if got_something:
                    ret[k] = retained
        else:
            if k == key: # value of interest
                ret[k] = tree[k]
    return ret

def filter_by_value (tree, value):
    ret = {}
    for k in tree.keys():
        if type(tree[k]) is dict:
            continue
        else:
            if str(tree[k]) == value:
                ret[k] = value
    return ret

def main (argv):
    parser = argparse.ArgumentParser(description="AD9545/46 status reporting")
    parser.add_argument(
        "bus",
        help="I2C bus",
    )
    parser.add_argument(
        "address",
        help="I2C slv address",
    )
    flags = [
        ("info",    "Device general infos (SN#, ..)"),
        ("serial",  "Serial port status (I2C/SPI)"),
        ("sysclk",  "Sys clock (all) infos"),
        ("pll", "Pll cores info"),
        ("ref-input",  "REFx and input signals infos"),
        ('distrib', 'Clock distribution & output signals infos'),
        ("iuts", "User time stamping units infos"),
        ("digitized-clocking", "Digitized clocking core infos"),
        ("irq", "IRQ registers"),
        ("watchdog", "Watchdog timer period"),
        ("temp", "Temperature sensor reading [°C]"),
        ("eeprom", "EEPROM controller status"),
        ("misc", "Auxilary NCOs, DPll and Temp info"),
    ]
    for (v_flag, v_helper) in flags:
        #_helper = helper if helper is not None else "Report {} Status".format(flag.upper())
        parser.add_argument(
            "--{}".format(v_flag), 
            action="store_true",
            help=v_helper,
        )
    parser.add_argument(
        "--filter-by-key",
        type=str,
        help="Filter results by matching (comma separeted) identifiers.",
    )
    parser.add_argument(
        "--filter-by-value",
        type=str,
        help="Filter results by matching (comma separeted) values.",
    )
    args = parser.parse_args(argv)

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)
        
    status = {}
    done = {
        0: 'idle',
        1: 'done',
    }
    enabled = {
        0: 'disabled',
        1: 'enabled',
    }
    active = {
        0: 'disabled',
        1: 'active',
    }
    available = {
        0: "unavailable",
        1: "available",
    }

    if args.info:
        status['info'] = {}
        status['info']['chip-type'] = hex(read_data(handle, address, 0x0003))
        data = read_data(handle, address, 0x0004) & 0xFF
        data |= (read_data(handle, address, 0x0005) & 0xFF)<<8
        data |= (read_data(handle, address, 0x0006) & 0xFF)<<16
        status['info']['device-code'] = hex(data) 
        status['info']['spi-version'] = hex(read_data(handle, address, 0x000B) & 0xFF)
        data = read_data(handle, address, 0x000C) & 0xFF
        data |= (read_data(handle, address, 0x000D) & 0xFF)<<8
        status['info']['vendor'] = hex(data) 
    if args.serial:
        bitfields = [
            ("soft-reset",0x01),
            ("lsbf-spi",0x02),
            ("addr-asc-spi",0x04),
            ("sdo-spi",0x08),
        ]
        read_reg(handle, address, status, 'serial', 0x0000, bitfields)
        bitfields = [
            ('reset-regs', 0x04),
            ('buffered-read', 0x40),
        ]
        read_reg(handle, address, status, 'serial', 0x0001, bitfields)
    if args.sysclk:
        status['sysclk'] = {}
        status['sysclk']['pll'] = {}
        r = read_data(handle, address, 0x3001)
        status['sysclk']['calibrating'] = bool((r & 0x04)>>2)
        status['sysclk']['stable'] = bool((r & 0x02)>>1)
        status['sysclk']['locked'] = bool((r & 0x01)>>0)
        status['sysclk']['pll']['fb-div-ratio'] = read_data(handle, address, 0x200) 
        data = read_data(handle, address, 0x201)
        status['sysclk']['pll']['input-sel'] = (data & 0x08)>>3
        status['sysclk']['pll']['input-div'] = (data & 0x06)>>1
        status['sysclk']['pll']['freq-doubler'] = bool(data & 0x01)
        ref_freq = read_data(handle, address, 0x202)
        ref_freq += read_data(handle, address, 0x203) << 8
        ref_freq += read_data(handle, address, 0x204) << 16
        ref_freq += read_data(handle, address, 0x205) << 24
        ref_freq += read_data(handle, address, 0x206) << 32
        status['sysclk']['pll']['ref-freq'] = ref_freq * 1E3
        per = read_data(handle, address, 0x207)
        per += read_data(handle, address, 0x208) << 8
        per += (read_data(handle, address, 0x209) & 0x0F) << 16
        status['sysclk']['pll']['stab-period'] = per * 10E-3 
    if args.sysclk:
        if not 'sysclk' in status:
            status['sysclk'] = {}
        status['sysclk']['comp'] = {}
        bitfields = [
            ('method2-aux-dpll', 0x20),
            ('method1-aux-dpll', 0x10),
            ('method3-tdcs', 0x04),
            ('method2-tdcs', 0x02),
            ('method1-tdcs', 0x01),
        ]
        read_reg(handle, address, status['sysclk'], 'comp', 0x0280, bitfields)
        bitfields = [
            ('method3-aux-nco1', 0x40),
            ('method2-aux-nco1', 0x20),
            ('method1-aux-nco1', 0x10),
            ('method3-aux-nco0', 0x04),
            ('method2-aux-nco0', 0x02),
            ('method1-aux-nco0', 0x01),
        ]
        read_reg(handle, address, status['sysclk'], 'comp', 0x0281, bitfields)
        bitfields = [
            ('method3-dpll1', 0x40),
            ('method2-dpll1', 0x20),
            ('method2-dpll1', 0x10),
            ('method3-dpll0', 0x04),
            ('method2-dpll0', 0x02),
            ('method2-dpll0', 0x01),
        ]
        read_reg(handle, address, status['sysclk'], 'comp', 0x0282, bitfields)
        r = read_data(handle, address, 0x0283) & 0x07
        values = {
            0: '0',
            1: "0.715 ppm/s",
            2: "1.430 ppm/s",
            3: "2.860 ppm/s",
            4: "5.720 ppm/s",
            5: "11.44 ppm/s",
            6: "22.88 ppm/s",
            7: "45.76 ppm/s",
        }
        status['sysclk']['comp']['slew-rate-lim'] = values[r]
        sources = {
            0: 'REFA',
            1: 'REFAA',
            2: 'REFB',
            3: 'REFBB',
            6: 'aux-REF0',
            7: 'aux-REF1',
            11: 'aux-REF2',
            12: 'aux-REF3',
        }
        r = read_data(handle, address, 0x0284) & 0x0F
        status['sysclk']['comp']['source']  = sources[r]
        r = read_data(handle, address, 0x0285)
        r += read_data(handle, address, 0x0286) << 8
        status['sysclk']['comp']['dpll-bw'] = r /10
        sel = {
            0: 'dpll0',
            1: 'dpll1',
        }
        status['sysclk']['comp']['dpll-sel'] = sel[read_data(handle, address, 0x0287)&0x01]
        cutoff = {
            0: '156 Hz',
            1: '78 Hz',
            2: '39 Hz',
            3: '20 Hz',
            4: '10 Hz',
            5: '5 Hz',
            6: '2 Hz',
            7: '1 Hz',
        }
        status['sysclk']['comp']['method1-cutoff'] = cutoff[read_data(handle, address, 0x0288)&0x07]
        c0 = read_data(handle, address, 0x0289)
        c0 += read_data(handle, address, 0x028A) << 8
        c0 += read_data(handle, address, 0x028B) << 16
        c0 += read_data(handle, address, 0x028C) << 24
        c0 += read_data(handle, address, 0x028D) << 32
        status['sysclk']['comp']['method1-c0'] = c0 / pow(2,45)  
        base = 0x028E
        for cx in range (1, 6):
            cx_s  = read_data(handle, address, base+0)
            cx_s += read_data(handle, address, base+1) << 8
            cx_e  = read_data(handle, address, base+2)
            base += 3
            #TODO conclure

    if args.eeprom:
        bitfields = [
            ('crc-fault', 0x08),
            ('fault', 0x04),
            ('busy-downloading', 0x02),
            ('busy-uploading', 0x01),
        ]
        read_reg(handle, address, status, 'eeprom', 0x3000, bitfields)
    if args.pll:
        status['pll'] = {}
        for c in ['ch0','ch1']:
            status['pll'][c] = {}
            for a in ['digital','analog']:
                status['pll'][c][a] = {}

        r = read_data(handle, address, 0x3001)
        status['pll']['ch1']['locked'] = bool((r&0x20)>>5)
        status['pll']['ch0']['locked'] = bool((r&0x10)>>4) 
        
        base = 0x3100
        for ch in ['ch0','ch1']:
            r = read_data(handle, address, base+0)
            status['pll'][ch]['analog']['calibration'] = done[(r&0x20)>>5]
            status['pll'][ch]['analog']['calibrating'] = bool((r&0x10)>>4)
            status['pll'][ch]['analog']['phase-locked'] = bool((r&0x08)>>3)
            status['pll'][ch]['digital']['freq-locked'] = bool((r&0x04)>>2)
            status['pll'][ch]['digital']['phase-locked'] = bool((r&0x02)>>1)
            
            r = read_data(handle, address, base+1)
            status['pll'][ch]['digital']['profile'] = (r & 0x70)>>4
            status['pll'][ch]['digital']['active'] = bool((r&0x08)>>3)
            status['pll'][ch]['digital']['switching-profile'] = bool((r & 0x04)>>2)
            status['pll'][ch]['digital']['holdover'] = bool((r&0x02) >>1)
            status['pll'][ch]['digital']['free-running'] = bool((r&0x01) >>0)

            r = read_data(handle, address, base+2)
            status['pll'][ch]['digital']['fast-acquisition'] = done[(r&0x20)>>5]
            status['pll'][ch]['digital']['fast-acquisitionning'] = bool((r&0x10)>>4)
            status['pll'][ch]['digital']['phase-slew'] = active[(r&0x04)>>2]
            status['pll'][ch]['digital']['freq-clamping'] = active[(r&0x02)>>1]
            status['pll'][ch]['digital']['tunning-word-history'] = available[(r&0x01)>>0]

            ftw = read_data(handle, address, base+3)
            ftw += read_data(handle, address, base+4) <<8
            ftw += read_data(handle, address, base+5) <<16
            ftw += read_data(handle, address, base+6) <<24
            ftw += read_data(handle, address, base+7) <<32
            ftw += (read_data(handle, address, base+8) & 0x1F) <<40
            status['pll'][ch]['digital']['ftw-history'] = ftw

            value = read_data(handle, address, base+9)
            value+= (read_data(handle, address, base+10) & 0x0F)<<8
            status['pll'][ch]['digital']['phase-lock-tub'] = value
            value = read_data(handle, address, base+11)
            value+= (read_data(handle, address, base+12) & 0x0F)<<8
            status['pll'][ch]['digital']['freq-lock-tub'] = value

            if ch == 'ch0':
                r = read_data(handle, address, base+13)
                status['pll'][ch]['cc-phase-slew'] = active[(r & 0x20)>>5]
                status['pll'][ch]['c-phase-slew'] = active[(r & 0x10)>>4]
                status['pll'][ch]['bb-phase-slew'] = active[(r & 0x08)>>3]
                status['pll'][ch]['b-phase-slew'] = active[(r & 0x04)>>2]
                status['pll'][ch]['aa-phase-slew'] = active[(r & 0x02)>>1]
                status['pll'][ch]['a-phase-slew'] = active[(r & 0x01)>>0]
                r = read_data(handle, address, base+14)
                status['pll'][ch]['cc-phase-error'] = bool((r & 0x20)>>5)
                status['pll'][ch]['c-phase-error'] =  bool((r & 0x10)>>4)
                status['pll'][ch]['bb-phase-error'] = bool((r & 0x08)>>3)
                status['pll'][ch]['b-phase-error'] =  bool((r & 0x04)>>2)
                status['pll'][ch]['aa-phase-error'] = bool((r & 0x02)>>1)
                status['pll'][ch]['a-phase-error'] =  bool((r & 0x01)>>0)
            else:
                r = read_data(handle, address, base+13)
                status['pll'][ch]['bb-phase-slew'] = active[(r & 0x08)>>3]
                status['pll'][ch]['b-phase-slew'] = active[(r & 0x04)>>2]
                status['pll'][ch]['aa-phase-slew'] = active[(r & 0x02)>>1]
                status['pll'][ch]['a-phase-slew'] = active[(r & 0x01)>>0]
                r = read_data(handle, address, base+14)
                status['pll'][ch]['bb-phase-error'] = bool((r & 0x08)>>3)
                status['pll'][ch]['b-phase-error'] =  bool((r & 0x04)>>2)
                status['pll'][ch]['aa-phase-error'] = bool((r & 0x02)>>1)
                status['pll'][ch]['a-phase-error'] =  bool((r & 0x01)>>0)
            base += 0x100
        
        base = 0x2100
        for ch in ['ch0','ch1']:
            r = read_data(handle, address, base +0)
            status['pll'][ch]['power-down'] = available[r & 0x01] 
            base += 0x100

    if args.misc:
        bitfields = [
            ('aux-nco1-phase-error', 0x80),
            ('aux-nco1-phase-slewing', 0x40),
            ('aux-nco0-phase-error', 0x20),
            ('aux-nco0-phase-slewing', 0x10),
            ('aux-dpll-ref-status', 0x04),
            ('aux-dpll-lock-status', 0x02),
            ('temperature-alarm', 0x01),
        ]
        read_reg(handle, address, status, 'misc', 0x3002, bitfields)
    if args.ref_input:
        status['ref-input'] = {}
        for ref in ['a','aa','b','bb']: #TODO '0','1','2'..aux
            status['ref-input'][ref] = {}
        coupling = {
            0: 'AC 1.2V',
            1: 'DC 1.2V CMOS',
            2: 'DC 1.8V CMOS',
            3:u'DC 1.2V CMOS + 46k\u03A9pull-up',
        }
        ref_mode = {
            0: 'single ended',
            1: 'differential',
        }
        bw = {
            0: 'narrow',
            1: 'wide',
        }
        demod_polarity = {
            0: 'manual',
            1: 'automatic',
        }
        event_pol = {
            0: 'narrow/wide',
            1: 'wide/narrow',
        }
        mon_hysteresis = {
            0: 'No hysteresis',
            1: '3.125%',
            2: '6.25%',
            3: '12.5%',
            4: '25%',
            5: '50%',
            6: '75%',
            7: '87.5%',
        }
        r = read_data(handle, address, 0x0300)
        status['ref-input']['aa']['input-termination'] = coupling[(r & 0xC0)>>6]
        status['ref-input']['a']['input-termination'] = coupling[(r & 0x30)>>4]
        status['ref-input']['a']['differential'] = coupling[(r & 0x0C)>>2]
        status['ref-input']['a-aa-input-mode'] = ref_mode[r & 0x01]
        status['ref-input']['a-aa-demod-bw'] = bw[read_data(handle, address, 0x0301) & 0x01]
        base = 0x0302
        for ref in ['a','aa']:
            r = read_data(handle, address, base)
            status['ref-input'][ref]['demod-polarity'] = demod_polarity[(r & 0x80)>>7]
            status['ref-input'][ref]['demod-persist-enabled'] = bool((r & 0x40)>>6)
            status['ref-input'][ref]['demod-sync-edge'] = (r & 0x30)>>4
            status['ref-input'][ref]['demod-enabled'] = bool((r & 0x80)>>3)
            status['ref-input'][ref]['demod-event-pol'] = event_pol[(r & 0x04)>>2]
            status['ref-input'][ref]['demod-sensitivity'] = r & 0x03
            base += 1
        r = read_data(handle, address, 0x0304)
        status['ref-input']['bb']['input-termination'] = coupling[(r & 0xC0)>>6]
        status['ref-input']['b']['input-termination'] = coupling[(r & 0x30)>>4]
        status['ref-input']['b']['differential'] = coupling[(r & 0x0C)>>2]
        status['ref-input']['b-bb-input-mode'] = ref_mode[r & 0x01]
        status['ref-input']['b-bb-demod-bw'] = bw[read_data(handle, address, 0x0305) & 0x01]
        base = 0x0306
        for ref in ['b','bb']:
            r = read_data(handle, address, base)
            status['ref-input'][ref]['demod-polarity'] = demod_polarity[(r & 0x80)>>7]
            status['ref-input'][ref]['demod-persist-enabled'] = bool((r & 0x40)>>6)
            status['ref-input'][ref]['demod-sync-edge'] = (r & 0x30)>>4
            status['ref-input'][ref]['demod-enabled'] = bool((r & 0x80)>>3)
            status['ref-input'][ref]['demod-event-pol'] = event_pol[(r & 0x04)>>2]
            status['ref-input'][ref]['demod-sensitivity'] = r & 0x03
            base += 1

        #base = 0x030A
        #for ref in ['0','1']:
        #    r = read_data(handle, address, base)
        #    status['ref-input'][ref]['aux-demod-polarity'] = demod_polarity[(r & 0x80)>>7]
        #    status['ref-input'][ref]['aux-demod-persist-enabled'] = bool((r & 0x40)>>6)
        #    status['ref-input'][ref]['aux-demod-sync-edge'] = (r & 0x30)>>4
        #    status['ref-input'][ref]['aux-demod-enabled'] = bool((r & 0x80)>>3)
        #    status['ref-input'][ref]['aux-demod-event-pol'] = event_pol[(r & 0x04)>>2]
        #    status['ref-input'][ref]['aux-demod-sensitivity'] = r & 0x03
        #    base += 1
        #
        #base = 0x030E
        #for ref in ['ref2-aux','ref3-aux']:
        #    r = read_data(handle, address, base)
        #    status['ref-input'][ref]['demod-polarity'] = demod_polarity[(r & 0x80)>>7]
        #    status['ref-input'][ref]['demod-persist-enabled'] = bool((r & 0x40)>>6)
        #    status['ref-input'][ref]['demod-sync-edge'] = (r & 0x30)>>4
        #    status['ref-input'][ref]['demod-enabled'] = bool((r & 0x80)>>3)
        #    status['ref-input'][ref]['demod-event-pol'] = event_pol[(r & 0x04)>>2]
        #    status['ref-input'][ref]['demod-sensitivity'] = r & 0x03
        #    base += 1

        base = 0x0400
        for ref in ['a','aa','b','bb']: # '0','1'
            rdiv =  read_data(handle, address, base+0)
            rdiv += read_data(handle, address, base+1) << 8
            rdiv += read_data(handle, address, base+2) << 16
            rdiv += (read_data(handle, address, base+3) & 0x1F) << 24
            status['ref-input'][ref]['r-div'] = rdiv+1 
            per =  read_data(handle, address, base+4)
            per += read_data(handle, address, base+5) << 8
            per += read_data(handle, address, base+6) << 16
            per += read_data(handle, address, base+7) << 24
            per += read_data(handle, address, base+8) << 32
            per += read_data(handle, address, base+9) << 40
            per += read_data(handle, address, base+10) << 48
            per += (read_data(handle, address, base+11) & 0x0F) << 56
            status['ref-input'][ref]['freq'] = pow(10,18)/per 
            t = read_data(handle, address, base+12)
            t += read_data(handle, address, base+13) << 8
            t += read_data(handle, address, base+14) << 16
            status['ref-input'][ref]['max-freq-deviation'] = t /10E9 /(1-t/10E9)
            status['ref-input'][ref]['mon-hysteresis'] = mon_hysteresis[read_data(handle, address, base+15) & 0x07]
            t = read_data(handle, address, base+16)
            t += read_data(handle, address, base+17)<<8
            t += (read_data(handle, address, base+18)&0x0F)<<16
            status['ref-input'][ref]['validation-time'] = '{:.3e} sec'.format(t /1000)
            j = read_data(handle, address, base+19)
            j += read_data(handle, address, base+20)
            status['ref-input'][ref]['jitter-tolerance'] = '{:.3e} sec rms'.format(j /10E9)
            base += 0x0020

        base = 0x3005
        for ref in ['a','aa','b','bb']:
            bitfields = [
                ('loss-of-signal', 0x20),
                ('valid', 0x10),
                ('fault', 0x08),
                ('jitter-excess', 0x04),
                ('fast', 0x02),
                ('slow', 0x01),
            ]
            r = read_data(handle, address, base)
            status['ref-input'][ref]['loss-of-signal'] = bool((r&0x20)>>5)
            status['ref-input'][ref]['valid'] = bool((r&0x10)>>4)
            status['ref-input'][ref]['fault'] = bool((r&0x08)>>3)
            status['ref-input'][ref]['jitter-excess'] = bool((r&0x04)>>2)
            status['ref-input'][ref]['fast'] = bool((r&0x02)>>1)
            status['ref-input'][ref]['slow'] = bool((r&0x01)>>0)
            base += 1
    
    if args.irq:
        bitfields = [
            ('sysclk-unlock', 0x80),
            ('sysclk-stable', 0x40),
            ('sysclk-lock', 0x20),
            ('sysclk-cal-end', 0x10),
            ('sysclk-cal-start', 0x08),
            ('watchdog-timeo', 0x04),
            ('eeprom-fault', 0x02),
            ('eepromm-complete', 0x01),
        ]
        read_reg(handle, address, status, 'irq', 0x300B, bitfields)
        bitfields = [
            ('skew-limit', 0x20),
            ('temp-warning', 0x10),
            ('aux-dpll-unfault', 0x08),
            ('aux-dpll-fault', 0x04),
            ('aux-dpll-unlock', 0x02),
            ('aux-dpll-lock', 0x01),
        ]
        read_reg(handle, address, status, 'irq', 0x300C, bitfields)
        bitfields = [
            ('refaa-r-div-resync', 0x80),
            ('refaa-valid', 0x40),
            ('refaa-unfault', 0x20),
            ('refaa-fault', 0x10),
            ('refa-r-div-resync', 0x08),
            ('refa-valid', 0x04),
            ('refa-unfault', 0x02),
            ('refa-fault', 0x01),
        ]
        read_reg(handle, address, status, 'irq', 0x300D, bitfields)
        bitfields = [
            ('refbb-r-div-resync', 0x80),
            ('refbb-valid', 0x40),
            ('refbb-unfault', 0x20),
            ('refbb-fault', 0x10),
            ('refb-r-div-resync', 0x08),
            ('refb-valid', 0x04),
            ('refb-unfault', 0x02),
            ('refb-fault', 0x01),
        ]
        read_reg(handle, address, status, 'irq', 0x300E, bitfields)
        bitfields = [
            ('skew-update', 0x10),
            ('utsp1-update', 0x08),
            ('utps0-update', 0x04),
            ('aux-nco1-event', 0x02),
            ('aux-nco0-event', 0x01),
        ]
        read_reg(handle, address, status, 'irq', 0x300F, bitfields)
        bitfields = [
            ('dpll0-freq-unclamped', 0x80),
            ('dpll0-freq-clamped', 0x40),
            ('dpll0-slew-limiter-inactive', 0x20),
            ('dpll0-slew-limiter-active', 0x10),
            ('dpll0-freq-unlocked', 0x08),
            ('dpll0-freq-locked', 0x04),
            ('dpll0-phase-unlocked', 0x02),
            ('dpll0-phase-locked', 0x01),
        ]
        read_reg(handle, address, status, 'irq', 0x3010, bitfields)
        bitfields = [
            ('dpll0-ref-switch', 0x80),
            ('dpll0-freerun', 0x40),
            ('dpll0-holdover', 0x20),
            ('dpll0-hitless-entered', 0x10),
            ('dpll0-hitless-exit', 0x08),
            ('dpll0-holdover-ftw-upd', 0x04),
            ('dpll0-phase-step', 0x01),
        ]
        read_reg(handle, address, status, 'irq', 0x3011, bitfields)
    if args.watchdog:
        status['watchdog'] = {}
        status['watchdog']['period'] = read_data(handle, address, 0x10A) & 0xFF
        status['watchdog']['period'] |= (read_data(handle, address, 0x10B) & 0xFF)<<8
    if args.iuts:
        bitfields = [
            ('iuts1-valid', 0x02),
            ('iuts2-valid', 0x01),
        ]
        read_reg(handle, address, status, 'iuts', 0x3023, bitfields)
    if args.temp:
        temp = (read_data(handle, address, 0x3004) & 0xFF)<< 8 
        temp |= read_data(handle, address, 0x3003) & 0xFF
        status['temp'] = {}
        status['temp']['reading'] = temp * pow(2,-7)

    if args.distrib:
        status['distrib'] = {}
        for ch in ['ch0','ch1']:
            status['distrib'][ch] = {}
            pins = ['pll','a','aa','b','bb','outa','outb']
            if ch == 'ch0':
                pins.append('c')
                pins.append('cc')
                pins.append('outc')
            for pin in pins:
                status['distrib'][ch][pin] = {}
                if 'out' in pin:
                    status['distrib'][ch][pin]['+'] = {}
                    status['distrib'][ch][pin]['-'] = {}
        
        fmts = {
           0: 'cml',
           1: 'hcsl',
        }
        currents = {
            0: '7.6 mA',
            1: '12.5 mA',
            2: '15 mA',
        }
        modes = {
            0: 'diff',
            1: 'se',
            2: 'sedd',
        }
        shot_mod = {
            0: 'immediate',
            1: 'triggered',
        }
        single_pulse_mod = {
            0: 'balanced',
            1: 'unbalanced',
        }
        mod_polarity = {
            0: 'narrow/wide',
            1: 'wide/narrow',
        }
        n_shot_mod = {
            0: 'burst',
            1: 'periodic',
        }
        retime_to_mod = {
            0: 'carrier-retiming',
            1: 'trigger-retiming',
        }
        retiming = {
            0: 'direct',
            1: 'retimed',
        }
        slew_mode = {
            0: 'lag',
            1: 'minimum-steps',
        }
        max_phase_slew = {
            0: 'Q180°',
            1: 'Q90°',
            2: '1/32Q',
            3: '1/16Q',
            4: '1/8Q',
            5: '1/4Q',
            6: '1/2Q',
            7: '1Q',
        }
        #################
        #CH0        
        #################
        base = 0x1100
        for pin in ['a','aa','b','bb','c','cc']:
            div = read_data(handle, address,  base+0 )
            div += read_data(handle, address, base+1 ) << 8
            div += read_data(handle, address, base+2 ) << 16
            div += read_data(handle, address, base+3 ) << 24
            status['distrib']['ch0'][pin]['q-div'] = div
            offset = read_data(handle, address, base +4 )
            offset += read_data(handle, address, base+5 ) <<8
            offset += read_data(handle, address, base+6 ) <<16
            offset += read_data(handle, address, base+7 ) <<24
            r = read_data(handle, address, base+8)
            offset += ((r & 0x40)>>6) << 32
            status['distrib']['ch0'][pin]['phase-offset'] = offset
            status['distrib']['ch0'][pin]['half-div'] = enabled[(r & 0x20)>>5]
            status['distrib']['ch0'][pin]['pwm/phase'] = enabled[(r & 0x10)>>4]
            status['distrib']['ch0'][pin]['slew-mode'] = slew_mode[(r & 0x08)>>3]
            status['distrib']['ch0'][pin]['max-phase-slew'] = max_phase_slew[(r & 0x07)]
            base += 9

        mod = read_data(handle, address, 0x10C0+0)
        mod += read_data(handle, address, 0x10C1+1) << 8
        for pin in ['a','b','c']:
            q_div = status['distrib']['ch0'][pin]['q-div']
            try:
                status['distrib']['ch0'][pin]['mod-step'] = mod /2 /q_div
            except ZeroDivisionError:
                status['distrib']['ch0'][pin]['mod-step'] = 0
        
        base = 0x10C2
        for pin in ['a','b','c']:
            mod = read_data(handle, address, base+0)
            mod += read_data(handle, address, base+1) << 8
            mod += read_data(handle, address, base+2) << 16
            mod += (read_data(handle, address, base+3) &0x0F) << 24
            status['distrib']['ch0'][pin]['mod-counter'] = mod
            base += 6

        r = read_data(handle, address, 0x10CE) & 0x03
        status['distrib']['ch0']['pll']['fb-div-sync-edge'] = r 

        base = 0x10CF
        for pin in ['a','b','c']:
            r = read_data(handle, address, base) & 0x0F
            status['distrib']['ch0'][pin]['n-shot-mod'] = shot_mod[(r & 0x08)>>3]
            status['distrib']['ch0'][pin]['single-pulse-modulation'] = single_pulse_mod[(r & 0x04)>>2]
            status['distrib']['ch0'][pin]['modulation-polarity'] = mod_polarity[(r & 0x02)>>1]
            status['distrib']['ch0'][pin]['modulation'] = enabled[r & 0x01]
            base += 1

        r = read_data(handle, address, 0x10D2)
        status['distrib']['ch0']['pll']['n-shot-gap'] = r
        r = read_data(handle, address, 0x10D3)
        status['distrib']['ch0']['pll']['n-shot-request-mode'] = n_shot_mod[(r & 0x40)>>6]
        status['distrib']['ch0']['pll']['n-shots'] = r & 0x3F

        r = read_data(handle, address, 0x10D4)
        status['distrib']['ch0']['bb']['prbs'] = enabled[(r&0x80)>>7] 
        status['distrib']['ch0']['bb']['n-shot'] = enabled[(r&0x40)>>6]
        status['distrib']['ch0']['b']['prbs'] = enabled[(r&0x20)>>5]
        status['distrib']['ch0']['b']['n-shot'] = enabled[(r&0x10)>>4]
        status['distrib']['ch0']['aa']['prbs'] = enabled[(r&0x08)>>3] 
        status['distrib']['ch0']['aa']['n-shot'] = enabled[(r&0x04)>>2]
        status['distrib']['ch0']['a']['prbs'] = enabled[(r&0x02)>>1]
        status['distrib']['ch0']['a']['n-shot'] = enabled[r&0x01]
        r = read_data(handle, address, 0x10D5)
        status['distrib']['ch0']['cc']['prbs'] = enabled[(r&0x08)>>3]
        status['distrib']['ch0']['cc']['n-shot'] = enabled[(r&0x04)>>2]
        status['distrib']['ch0']['c']['prbs'] = enabled[(r&0x02)>>1]
        status['distrib']['ch0']['c']['n-shot'] = enabled[r&0x01]
        r = read_data(handle, address, 0x10D6)
        status['distrib']['ch0']['pll']['nshot-2-mod-retime'] = retime_to_mod[(r & 0x10)>>4]
        status['distrib']['ch0']['pll']['nshot-retiming'] = retiming[r & 0x01]

        base = 0x10D7
        for pin in ['a','b','c']:
            r = read_data(handle, address, base)
            status['distrib']['ch0'][pin]['mute-retiming'] = enabled[(r & 0x20)>>5]
            status['distrib']['ch0'][pin]['mode'] = modes[(r & 0x18)>>3]
            status['distrib']['ch0'][pin]['current'] = currents[(r & 0x03)>>1]
            status['distrib']['ch0'][pin]['format'] = fmts[r & 0x01]
            base += 1
        
        r = read_data(handle, address, 0x310D)
        status['distrib']['ch0']['cc']['phase-slewing'] = enabled[(r & 0x20)>>5]
        status['distrib']['ch0']['c']['phase-slewing'] = enabled[(r & 0x10)>>4]
        status['distrib']['ch0']['bb']['phase-slewing'] = enabled[(r & 0x08)>>3]
        status['distrib']['ch0']['b']['phase-slewing'] = enabled[(r & 0x04)>>2]
        status['distrib']['ch0']['aa']['phase-slewing'] = enabled[(r & 0x02)>>1]
        status['distrib']['ch0']['a']['phase-slewing'] = enabled[r & 0x01]
        
        r = read_data(handle, address, 0x310E)
        status['distrib']['ch0']['cc']['phase-ctrl-error'] = bool((r & 0x20)>>5)
        status['distrib']['ch0']['c']['phase-ctrl-error'] = bool((r & 0x10)>>4)
        status['distrib']['ch0']['bb']['phase-ctrl-error'] = bool((r & 0x08)>>3)
        status['distrib']['ch0']['b']['phase-ctrl-error'] = bool((r & 0x04)>>2)
        status['distrib']['ch0']['aa']['phase-ctrl-error'] = bool((r & 0x02)>>1)
        status['distrib']['ch0']['a']['phase-ctrl-error'] = bool((r & 0x01)>>0)
        
        #################
        #CH1        
        #################
        base = 0x1500
        for pin in ['a','aa','b','bb']:
            div = read_data(handle, address,  base+0 )
            div += read_data(handle, address, base+1 ) << 8
            div += read_data(handle, address, base+2 ) << 16
            div += read_data(handle, address, base+3 ) << 24
            status['distrib']['ch1'][pin]['q-div'] = div
            offset = read_data(handle, address, base +4 )
            offset += read_data(handle, address, base+5 ) <<8
            offset += read_data(handle, address, base+6 ) <<16
            offset += read_data(handle, address, base+7 ) <<24
            r = read_data(handle, address, base+8)
            offset += ((r & 0x40)>>6) << 32
            status['distrib']['ch1'][pin]['phase-offset'] = offset
            status['distrib']['ch1'][pin]['half-div'] = enabled[(r & 0x20)>>5]
            status['distrib']['ch1'][pin]['pwm/phase'] = enabled[(r & 0x10)>>4]
            status['distrib']['ch1'][pin]['slew-mode'] = slew_mode[(r & 0x08)>>3]
            status['distrib']['ch1'][pin]['max-phase-slew'] = max_phase_slew[(r & 0x07)]
            base += 9

        mod = read_data(handle, address, 0x14C0+0)
        mod += read_data(handle, address, 0x14C1+1) << 8
        for pin in ['a','b']:
            q_div = status['distrib']['ch1'][pin]['q-div']
            try:
                status['distrib']['ch1'][pin]['mod-step'] = mod /2 /q_div
            except ZeroDivisionError:
                status['distrib']['ch1'][pin]['mod-step'] = 0
        
        base = 0x14C2
        for pin in ['a','b']:
            mod = read_data(handle, address, base+0)
            mod += read_data(handle, address, base+1) << 8
            mod += read_data(handle, address, base+2) << 16
            mod += (read_data(handle, address, base+3) &0x0F) << 24
            status['distrib']['ch1'][pin]['mod-counter'] = mod
            base += 6

        r = read_data(handle, address, 0x14CE) & 0x03
        status['distrib']['ch1']['pll']['fb-div-sync-edge'] = r 

        base = 0x14CF
        for pin in ['a','b']:
            r = read_data(handle, address, base) & 0x0F
            status['distrib']['ch1'][pin]['n-shot-mod'] = shot_mod[(r & 0x08)>>3]
            status['distrib']['ch1'][pin]['single-pulse-modulation'] = single_pulse_mod[(r & 0x04)>>2]
            status['distrib']['ch1'][pin]['modulation-polarity'] = mod_polarity[(r & 0x02)>>1]
            status['distrib']['ch1'][pin]['modulation'] = enabled[r & 0x01]
            base += 1

        r = read_data(handle, address, 0x14D2)
        status['distrib']['ch1']['pll']['n-shot-gap'] = r
        r = read_data(handle, address, 0x14D3)
        status['distrib']['ch1']['pll']['n-shot-request-mode'] = n_shot_mod[(r & 0x40)>>6]
        status['distrib']['ch1']['pll']['n-shots'] = r & 0x3F

        r = read_data(handle, address, 0x14D4)
        status['distrib']['ch1']['bb']['prbs'] = enabled[(r&0x80)>>7] 
        status['distrib']['ch1']['bb']['n-shot'] = enabled[(r&0x40)>>6]
        status['distrib']['ch1']['b']['prbs'] = enabled[(r&0x20)>>5]
        status['distrib']['ch1']['b']['n-shot'] = enabled[(r&0x10)>>4]
        status['distrib']['ch1']['aa']['prbs'] = enabled[(r&0x08)>>3] 
        status['distrib']['ch1']['aa']['n-shot'] = enabled[(r&0x04)>>2]
        status['distrib']['ch1']['a']['prbs'] = enabled[(r&0x02)>>1]
        status['distrib']['ch1']['a']['n-shot'] = enabled[r&0x01]
        r = read_data(handle, address, 0x14D6)
        status['distrib']['ch1']['pll']['nshot-2-mod-retime'] = retime_to_mod[(r & 0x10)>>4]
        status['distrib']['ch1']['pll']['nshot-retiming'] = retiming[r & 0x01]

        base = 0x14D7
        for pin in ['a','b']:
            r = read_data(handle, address, base)
            status['distrib']['ch1'][pin]['mute-retiming'] = enabled[(r & 0x20)>>5]
            status['distrib']['ch1'][pin]['mode'] = modes[(r & 0x18)>>3]
            status['distrib']['ch1'][pin]['current'] = currents[(r & 0x03)>>1]
            status['distrib']['ch1'][pin]['format'] = fmts[r & 0x01]
            base += 1
        
        r = read_data(handle, address, 0x320D)
        status['distrib']['ch1']['bb']['phase-slewing'] = enabled[(r & 0x08)>>3]
        status['distrib']['ch1']['b']['phase-slewing'] = enabled[(r & 0x04)>>2]
        status['distrib']['ch1']['aa']['phase-slewing'] = enabled[(r & 0x02)>>1]
        status['distrib']['ch1']['a']['phase-slewing'] = enabled[r & 0x01]
        
        r = read_data(handle, address, 0x320E)
        status['distrib']['ch1']['bb']['phase-ctrl-error'] = bool((r & 0x08)>>3)
        status['distrib']['ch1']['b']['phase-ctrl-error'] = bool((r & 0x04)>>2)
        status['distrib']['ch1']['aa']['phase-ctrl-error'] = bool((r & 0x02)>>1)
        status['distrib']['ch1']['a']['phase-ctrl-error'] = bool((r & 0x01)>>0)

        base = 0x2100
        for ch in ['ch0','ch1']:
            r = read_data(handle, address, base+0)
            status['distrib'][ch]['reset'] = bool((r & 0x04)>>2)
            status['distrib'][ch]['muted'] = bool((r & 0x02)>>1)
            r = read_data(handle, address, base+1)
            status['distrib'][ch]['outa']['reset'] = bool((r & 0x20)>>5)
            status['distrib'][ch]['outa']['power-down'] = bool((r & 0x10)>>4)
            status['distrib'][ch]['outa']['-']['muted'] = bool((r & 0x08)>>3)
            status['distrib'][ch]['outa']['+']['muted'] = bool((r & 0x04)>>2)
            r = read_data(handle, address, base+2)
            status['distrib'][ch]['outb']['reset'] = bool((r & 0x20)>>5)
            status['distrib'][ch]['outb']['power-down'] = bool((r & 0x10)>>4)
            status['distrib'][ch]['outb']['-']['muted'] = bool((r & 0x08)>>3)
            status['distrib'][ch]['outb']['+']['muted'] = bool((r & 0x04)>>2)
            if ch == 'ch0':
                r = read_data(handle, address, base+2)
                status['distrib'][ch]['outc']['reset'] = bool((r & 0x20)>>5)
                status['distrib'][ch]['outc']['power-down'] = bool((r & 0x10)>>4)
                status['distrib'][ch]['outc']['-']['muted'] = bool((r & 0x08)>>3)
                status['distrib'][ch]['outc']['+']['muted'] = bool((r & 0x04)>>2)
            base += 0x100
            
    #print("======== TOTAL ===============")
    #print(json.dumps(status, sort_keys=True, indent=2))
    #print("==============================")
 
    if args.filter_by_key:
        filtered = {}
        filters = args.filter_by_key.split(",")
        for category in status.keys(): # filter all categories
            filtered[category] = {}
            to_merge = []
            for f in filters:
                to_merge.append(filter_by_key(status[category], f))
            all_empty = True
            for d in to_merge:
                if len(d) > 0:
                    all_empty = False
                filtered[category] |= d 
            if all_empty: # trick to catch non relevant filter ops
                filtered[category] = status[category].copy()    
    else:
        filtered = status.copy()
                
    if args.filter_by_value:
        filters = args.filter_by_value.split(",")
        for category in status.keys(): # filter all categories
            to_diff = []
            for f in filters:
                to_diff = filter_by_value(filtered[category], f)
                #TODO conclude diff op
                #print("========= diff ==============")
                #print(json.dumps(to_diff, sort_keys=True, indent=2))
    
    print(json.dumps(filtered, sort_keys=True, indent=2))
    
if __name__ == "__main__":
    main(sys.argv[1:])
