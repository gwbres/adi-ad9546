#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# status.py: AD9546 status monitoring (read only tool)
#################################################################
import sys
import math
import json
import argparse
from ad9546 import *

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
                if len(retained) > 0: # got something
                    ret[k] = retained
        else:
            if k == key: # value of interest
                ret[k] = tree[k]
    return ret

def filter_by_value (tree, value):
    ret = {} 
    for k in tree.keys():
        if type(tree[k]) is dict: # is a branch
            # filter inside branch
            data = filter_by_value(tree[k], value)
            if len(data) > 0: # got something
                ret[k] = data # construct
        else:
            if str(tree[k]).lower() == value.lower(): # matched value
                ret[k] = tree[k] # construct 
    return ret

def unpack (tree):
    ret = {}
    for k in tree.keys(): 
        if type(tree[k]) is dict:
            # reduce dimension
            unpacked = unpack(tree[k])
            if type(unpacked) is dict:
                for key in unpacked.keys():
                    ret[key] = unpacked[key]
            else:
                ret[k] = unpacked
        else:
            ret[k] = tree[k]
    
    if len(ret) == 1:
        return ret[list(ret.keys())[0]]
    else:
        return ret

def main (argv):
    parser = argparse.ArgumentParser(description="AD9546 status reporting")
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
    flags = [
        ("info",    "Device general infos (SN#, ..)"),
        ("serial",  "Serial port status (I2C/SPI)"),
        ("sysclk",  "Sys clock (all) infos"),
        ("pll", "Pll cores info"),
        ("ref-input",  "REFx and input signals infos"),
        ('distrib', 'Clock distribution & output signals infos'),
        ('ccdpll', 'Common Clock DPLL core infos'),
        ("uts",  "User Time Stamping cores status + readings"),
        ("iuts", "Inverse UTS cores status + readings"),
        ("irq", "IRQ registers"),
        ("watchdog", "Watchdog timer period"),
        ("eeprom", "EEPROM controller status"),
        ("misc", "Auxilary NCOs, DPll, temperature sensor reading, ..."),
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
    parser.add_argument(
        "--unpack",
        action="store_true",
        help="Reduce output to 1D or extract single field value",
    )
    args = parser.parse_args(argv)
    # open device
    dev = AD9546(args.bus, int(args.address, 16))
        
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
        status['info']['chip-type'] = hex(dev.read_data(0x0003))
        data = dev.read_data(0x0004)
        data |= dev.read_data(0x0005)<<8
        data |= dev.read_data(0x0006)<<16
        status['info']['device-code'] = hex(data) 
        status['info']['spi-version'] = hex(dev.read_data(0x000B))
        data  = dev.read_data(0x000C)
        data |= dev.read_data(0x000D)<<8
        status['info']['vendor'] = hex(data) 
    if args.serial:
        status['serial'] = {}
        r = dev.read_data(0x0000)
        status['serial']['soft-reset'] = bool((r & 0x01)>>0)
        status['serial']['spi-lsbf'] = bool((r & 0x02)>>1)
        status['serial']['spi-addr-asc'] = bool((r & 0x04)>>2)
        status['serial']['spi-sdo'] = bool((r & 0x08)>>3)
        r = dev.read_data(0x0001)
        status['serial']['reset-registers'] = bool((r & 0x04)>>2)
        status['serial']['buffered-read'] = bool((r & 0x40)>>6)
    if args.sysclk:
        status['sysclk'] = {}
        status['sysclk']['pll'] = {}
        r = dev.read_data(0x3001)
        status['sysclk']['calibrating'] = bool((r & 0x04)>>2)
        status['sysclk']['stable'] = bool((r & 0x02)>>1)
        status['sysclk']['locked'] = bool((r & 0x01)>>0)
        status['sysclk']['pll']['fb-div-ratio'] = dev.read_data(0x200) 
        data = dev.read_data(0x201)
        status['sysclk']['pll']['input-sel'] = (data & 0x08)>>3
        status['sysclk']['pll']['input-div'] = (data & 0x06)>>1
        status['sysclk']['pll']['freq-doubler'] = bool(data & 0x01)
        ref_freq = dev.read_data(0x202)
        ref_freq += dev.read_data(0x203) << 8
        ref_freq += dev.read_data(0x204) << 16
        ref_freq += dev.read_data(0x205) << 24
        ref_freq += dev.read_data(0x206) << 32
        status['sysclk']['pll']['ref-freq'] = ref_freq * 1E3
        per = dev.read_data(0x207)
        per += dev.read_data(0x208) << 8
        per += (dev.read_data(0x209) & 0x0F) << 16
        status['sysclk']['pll']['stab-period'] = per * 10E-3 
        
        status['sysclk']['comp'] = {}
        r = dev.read_data(0x280)
        status['sysclk']['comp']['method2-aux-dpll'] = bool((r & 0x20)>>5)
        status['sysclk']['comp']['method1-aux-dpll'] = bool((r & 0x10)>>4)
        status['sysclk']['comp']['method3-tcds'] = bool((r & 0x04)>>2)
        status['sysclk']['comp']['method2-tcds'] = bool((r & 0x02)>>1)
        status['sysclk']['comp']['method1-tcds'] = bool((r & 0x01)>>0)
        r = dev.read_data(0x281)
        status['sysclk']['comp']['method3-aux-nco1'] = bool((r & 0x40)>>6)
        status['sysclk']['comp']['method2-aux-nco1'] = bool((r & 0x20)>>5)
        status['sysclk']['comp']['method1-aux-nco1'] = bool((r & 0x10)>>4)
        status['sysclk']['comp']['method3-aux-nco0'] = bool((r & 0x04)>>2)
        status['sysclk']['comp']['method2-aux-nco0'] = bool((r & 0x02)>>1)
        status['sysclk']['comp']['method1-aux-nco0'] = bool((r & 0x01)>>0)
        r = dev.read_data(0x282)
        status['sysclk']['comp']['method3-dpll1'] = bool((r & 0x40)>>6)
        status['sysclk']['comp']['method3-dpll1'] = bool((r & 0x20)>>5)
        status['sysclk']['comp']['method1-dpll1'] = bool((r & 0x10)>>4)
        status['sysclk']['comp']['method3-dpll0'] = bool((r & 0x04)>>2)
        status['sysclk']['comp']['method2-dpll0'] = bool((r & 0x02)>>1)
        status['sysclk']['comp']['method1-dpll0'] = bool((r & 0x01)>>0)
        r = dev.read_data(0x0283) & 0x07
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
        r = dev.read_data(0x0284) & 0x0F
        status['sysclk']['comp']['source']  = sources[r]
        r = dev.read_data(0x0285)
        r += dev.read_data(0x0286) << 8
        status['sysclk']['comp']['dpll-bw'] = r /10
        sel = {
            0: 'dpll0',
            1: 'dpll1',
        }
        status['sysclk']['comp']['dpll-sel'] = sel[dev.read_data(0x0287)&0x01]
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
        status['sysclk']['comp']['method1-cutoff'] = cutoff[dev.read_data(0x0288)&0x07]
        c0 = dev.read_data(0x0289)
        c0 += dev.read_data(0x028A) << 8
        c0 += dev.read_data(0x028B) << 16
        c0 += dev.read_data(0x028C) << 24
        c0 += dev.read_data(0x028D) << 32
        status['sysclk']['comp']['method1-c0'] = c0 / pow(2,45)  
        base = 0x028E
        for cx in range (1, 6):
            cx_s  = dev.read_data(base+0)
            cx_s += dev.read_data(base+1) << 8
            cx_e  = dev.read_data(base+2)
            base += 3
            #TODO conclure

    if args.eeprom:
        status['eeprom'] = {}
        r = dev.read_data(0x3000)
        status['eeprom']['crc-fault'] = bool((r&0x08)>>3)
        status['eeprom']['fault'] = bool((r&0x04)>>2)
        status['eeprom']['busy'] = {}
        status['eeprom']['busy']['downloading'] = bool((r&0x02)>>1)
        status['eeprom']['busy']['uploading'] = bool((r&0x01)>>0)
    if args.pll:
        status['pll'] = {}
        for c in ['ch0','ch1']:
            status['pll'][c] = {}
            for a in ['digital','analog']:
                status['pll'][c][a] = {}

        r = dev.read_data(0x3001)
        status['pll']['ch1']['locked'] = bool((r&0x20)>>5)
        status['pll']['ch0']['locked'] = bool((r&0x10)>>4) 
        
        base = 0x3100
        for ch in ['ch0','ch1']:
            r = dev.read_data(base+0)
            status['pll'][ch]['analog']['calibration'] = done[(r&0x20)>>5]
            status['pll'][ch]['analog']['calibrating'] = bool((r&0x10)>>4)
            status['pll'][ch]['analog']['phase-locked'] = bool((r&0x08)>>3)
            status['pll'][ch]['digital']['freq-locked'] = bool((r&0x04)>>2)
            status['pll'][ch]['digital']['phase-locked'] = bool((r&0x02)>>1)
            
            r = dev.read_data(base+1)
            status['pll'][ch]['digital']['profile'] = (r & 0x70)>>4
            status['pll'][ch]['digital']['active'] = bool((r&0x08)>>3)
            status['pll'][ch]['digital']['switching-profile'] = bool((r & 0x04)>>2)
            status['pll'][ch]['digital']['holdover'] = bool((r&0x02) >>1)
            status['pll'][ch]['digital']['free-running'] = bool((r&0x01) >>0)

            r = dev.read_data(base+2)
            status['pll'][ch]['digital']['fast-acquisition'] = done[(r&0x20)>>5]
            status['pll'][ch]['digital']['fast-acquisitionning'] = bool((r&0x10)>>4)
            status['pll'][ch]['digital']['phase-slew'] = active[(r&0x04)>>2]
            status['pll'][ch]['digital']['freq-clamping'] = active[(r&0x02)>>1]
            status['pll'][ch]['digital']['tunning-word-history'] = available[(r&0x01)>>0]

            ftw = dev.read_data(base+3)
            ftw += dev.read_data(base+4) <<8
            ftw += dev.read_data(base+5) <<16
            ftw += dev.read_data(base+6) <<24
            ftw += dev.read_data(base+7) <<32
            ftw += (dev.read_data(base+8) & 0x1F) <<40
            status['pll'][ch]['digital']['ftw-history'] = ftw

            value = dev.read_data(base+9)
            value+= (dev.read_data(base+10) & 0x0F)<<8
            status['pll'][ch]['digital']['phase-lock-tub'] = value
            value = dev.read_data(base+11)
            value+= (dev.read_data(base+12) & 0x0F)<<8
            status['pll'][ch]['digital']['freq-lock-tub'] = value

            if ch == 'ch0':
                r = dev.read_data(base+13)
                status['pll'][ch]['cc-phase-slew'] = active[(r & 0x20)>>5]
                status['pll'][ch]['c-phase-slew'] = active[(r & 0x10)>>4]
                status['pll'][ch]['bb-phase-slew'] = active[(r & 0x08)>>3]
                status['pll'][ch]['b-phase-slew'] = active[(r & 0x04)>>2]
                status['pll'][ch]['aa-phase-slew'] = active[(r & 0x02)>>1]
                status['pll'][ch]['a-phase-slew'] = active[(r & 0x01)>>0]
                r = dev.read_data(base+14)
                status['pll'][ch]['cc-phase-error'] = bool((r & 0x20)>>5)
                status['pll'][ch]['c-phase-error'] =  bool((r & 0x10)>>4)
                status['pll'][ch]['bb-phase-error'] = bool((r & 0x08)>>3)
                status['pll'][ch]['b-phase-error'] =  bool((r & 0x04)>>2)
                status['pll'][ch]['aa-phase-error'] = bool((r & 0x02)>>1)
                status['pll'][ch]['a-phase-error'] =  bool((r & 0x01)>>0)
            else:
                r = dev.read_data(base+13)
                status['pll'][ch]['bb-phase-slew'] = active[(r & 0x08)>>3]
                status['pll'][ch]['b-phase-slew'] = active[(r & 0x04)>>2]
                status['pll'][ch]['aa-phase-slew'] = active[(r & 0x02)>>1]
                status['pll'][ch]['a-phase-slew'] = active[(r & 0x01)>>0]
                r = dev.read_data(base+14)
                status['pll'][ch]['bb-phase-error'] = bool((r & 0x08)>>3)
                status['pll'][ch]['b-phase-error'] =  bool((r & 0x04)>>2)
                status['pll'][ch]['aa-phase-error'] = bool((r & 0x02)>>1)
                status['pll'][ch]['a-phase-error'] =  bool((r & 0x01)>>0)
            base += 0x100
        
        base = 0x2100
        for ch in ['ch0','ch1']:
            r = dev.read_data(base +0)
            status['pll'][ch]['power-down'] = available[r & 0x01] 
            base += 0x100

    if args.misc:
        status['misc'] = {}
        status['misc']['aux-nco'] = {}
        status['misc']['aux-dpll'] = {}
        status['misc']['temperature'] = {}
        r = dev.read_data(0x3002)
        status['misc']['aux-nco']['nco1-phase-error'] = bool((r & 0x80)>>7)
        status['misc']['aux-nco']['nco1-phase-slewing'] = bool((r & 0x40)>>6)
        status['misc']['aux-nco']['nco0-phase-error'] = bool((r & 0x20)>>5)
        status['misc']['aux-nco']['nco0-phase-slewing'] = bool((r & 0x10)>>4)
        status['misc']['aux-dpll']['ref-status'] = (r & 0x04)>>2
        status['misc']['aux-dpll']['lock-status'] = (r & 0x02)>>1
        status['misc']['temperature']['alarm'] = bool((r & 0x01)>>0)
        temp = (dev.read_data(0x3004) & 0xFF)<< 8 
        temp |= dev.read_data(0x3003) & 0xFF
        status['misc']['temperature']['value'] = u"{:.1f} degC".format(temp * pow(2,-7))

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
        r = dev.read_data(0x0300)
        status['ref-input']['aa']['input-termination'] = coupling[(r & 0xC0)>>6]
        status['ref-input']['a']['input-termination'] = coupling[(r & 0x30)>>4]
        status['ref-input']['a']['differential'] = coupling[(r & 0x0C)>>2]
        status['ref-input']['a-aa-input-mode'] = ref_mode[r & 0x01]
        status['ref-input']['a-aa-demod-bw'] = bw[dev.read_data(0x0301) & 0x01]
        base = 0x0302
        for ref in ['a','aa']:
            r = dev.read_data(base)
            status['ref-input'][ref]['demod-polarity'] = demod_polarity[(r & 0x80)>>7]
            status['ref-input'][ref]['demod-persist-enabled'] = bool((r & 0x40)>>6)
            status['ref-input'][ref]['demod-sync-edge'] = (r & 0x30)>>4
            status['ref-input'][ref]['demod-enabled'] = bool((r & 0x80)>>3)
            status['ref-input'][ref]['demod-event-pol'] = event_pol[(r & 0x04)>>2]
            status['ref-input'][ref]['demod-sensitivity'] = r & 0x03
            base += 1
        r = dev.read_data(0x0304)
        status['ref-input']['bb']['input-termination'] = coupling[(r & 0xC0)>>6]
        status['ref-input']['b']['input-termination'] = coupling[(r & 0x30)>>4]
        status['ref-input']['b']['differential'] = coupling[(r & 0x0C)>>2]
        status['ref-input']['b-bb-input-mode'] = ref_mode[r & 0x01]
        status['ref-input']['b-bb-demod-bw'] = bw[dev.read_data(0x0305) & 0x01]
        base = 0x0306
        for ref in ['b','bb']:
            r = dev.read_data(base)
            status['ref-input'][ref]['demod-polarity'] = demod_polarity[(r & 0x80)>>7]
            status['ref-input'][ref]['demod-persist-enabled'] = bool((r & 0x40)>>6)
            status['ref-input'][ref]['demod-sync-edge'] = (r & 0x30)>>4
            status['ref-input'][ref]['demod-enabled'] = bool((r & 0x80)>>3)
            status['ref-input'][ref]['demod-event-pol'] = event_pol[(r & 0x04)>>2]
            status['ref-input'][ref]['demod-sensitivity'] = r & 0x03
            base += 1

        #base = 0x030A
        #for ref in ['0','1']:
        #    r = dev.read_data(base)
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
        #    r = dev.read_data(base)
        #    status['ref-input'][ref]['demod-polarity'] = demod_polarity[(r & 0x80)>>7]
        #    status['ref-input'][ref]['demod-persist-enabled'] = bool((r & 0x40)>>6)
        #    status['ref-input'][ref]['demod-sync-edge'] = (r & 0x30)>>4
        #    status['ref-input'][ref]['demod-enabled'] = bool((r & 0x80)>>3)
        #    status['ref-input'][ref]['demod-event-pol'] = event_pol[(r & 0x04)>>2]
        #    status['ref-input'][ref]['demod-sensitivity'] = r & 0x03
        #    base += 1

        base = 0x0400
        for ref in ['a','aa','b','bb']: # '0','1'
            rdiv =  dev.read_data(base+0)
            rdiv += dev.read_data(base+1) << 8
            rdiv += dev.read_data(base+2) << 16
            rdiv += (dev.read_data(base+3) & 0x1F) << 24
            status['ref-input'][ref]['r-div'] = rdiv+1 
            per =  dev.read_data(base+4)
            per += dev.read_data(base+5) << 8
            per += dev.read_data(base+6) << 16
            per += dev.read_data(base+7) << 24
            per += dev.read_data(base+8) << 32
            per += dev.read_data(base+9) << 40
            per += dev.read_data(base+10) << 48
            per += (dev.read_data(base+11) & 0x0F) << 56
            status['ref-input'][ref]['freq'] = pow(10,18)/per 
            t = dev.read_data(base+12)
            t += dev.read_data(base+13) << 8
            t += dev.read_data(base+14) << 16
            status['ref-input'][ref]['max-freq-deviation'] = t /10E9 /(1-t/10E9)
            status['ref-input'][ref]['mon-hysteresis'] = mon_hysteresis[dev.read_data(base+15) & 0x07]
            t = dev.read_data(base+16)
            t += dev.read_data(base+17)<<8
            t += (dev.read_data(base+18)&0x0F)<<16
            status['ref-input'][ref]['validation-time'] = '{:.3e} sec'.format(t /1000)
            j = dev.read_data(base+19)
            j += dev.read_data(base+20)
            status['ref-input'][ref]['jitter-tolerance'] = '{:.3e} sec rms'.format(j /10E9)
            base += 0x0020

        base = 0x3005
        for ref in ['a','aa','b','bb']:
            r = dev.read_data(base)
            status['ref-input'][ref]['loss-of-signal'] = bool((r&0x20)>>5)
            status['ref-input'][ref]['valid'] = bool((r&0x10)>>4)
            status['ref-input'][ref]['fault'] = bool((r&0x08)>>3)
            status['ref-input'][ref]['jitter-excess'] = bool((r&0x04)>>2)
            status['ref-input'][ref]['fast'] = bool((r&0x02)>>1)
            status['ref-input'][ref]['slow'] = bool((r&0x01)>>0)
            base += 1
    
    if args.irq:
        status['irq'] = {}
        for attr in ['sysclk', 'watchdog', 'ref', 'eeprom', 'aux-dpll', 'dpll', 'skew', 'utsp', 'aux-nco']:
            status['irq'][attr] = {}
        for ref in ['a','aa','b','bb']:
            status['irq']['ref'][ref] = {}
        for ch in [0,1]:
            status['irq']['dpll'][ch] = {}
            status['irq']['utsp'][ch] = {}
            status['irq']['aux-nco'][ch] = {}

        r = dev.read_data(0x300B)
        status['irq']['sysclk']['unlocked'] = bool((r & 0x80)>>7)
        status['irq']['sysclk']['stabled'] = bool((r & 0x40)>>6)
        status['irq']['sysclk']['locked'] = bool((r & 0x20)>>5)
        status['irq']['sysclk']['calibration'] = {}
        status['irq']['sysclk']['calibration']['start'] = bool((r & 0x10)>>4)
        status['irq']['sysclk']['calibration']['end'] = bool((r & 0x08)>>3)
        status['irq']['watchdog']['timeout'] = bool((r & 0x04)>>2)
        status['irq']['eeprom']['fault'] = bool((r & 0x02)>>1)
        status['irq']['eeprom']['complete'] = bool((r & 0x01)>>0)

        r = dev.read_data(0x300C)
        status['irq']['skew']['limit'] = bool((r & 0x20)>>5) 
        status['irq']['temperature-warning'] = bool((r & 0x10)>>4) 
        status['irq']['aux-dpll']['unfault'] = bool((r & 0x08)>>3)
        status['irq']['aux-dpll']['fault'] = bool((r & 0x04)>>2)
        status['irq']['aux-dpll']['unlock'] = bool((r & 0x02)>>1)
        status['irq']['aux-dpll']['lock'] = bool((r & 0x01)>>0)
        
        for (ref, addr) in [('a', 0x300D), ('b', 0x300E)]:
            r = dev.read_data(addr)
            status['irq']['ref'][ref+ref]['div-resync'] = bool((r & 0x80)>>7)
            status['irq']['ref'][ref+ref]['valid'] = bool((r & 0x40)>>6)
            status['irq']['ref'][ref+ref]['unfault'] = bool((r & 0x20)>>5)
            status['irq']['ref'][ref+ref]['fault'] = bool((r & 0x10)>>4)
            status['irq']['ref'][ref]['div-resync'] = bool((r & 0x08)>>3)
            status['irq']['ref'][ref]['valid'] = bool((r & 0x04)>>2)
            status['irq']['ref'][ref]['unfault'] = bool((r & 0x02)>>1)
            status['irq']['ref'][ref]['fault'] = bool((r & 0x01)>>0)

        r = dev.read_data(0x300F)
        status['irq']['skew']['update'] = bool((r & 0x10)>>4) 
        status['irq']['utsp'][1]['update'] = bool((r & 0x08)>>3) 
        status['irq']['utsp'][0]['update'] = bool((r & 0x04)>>2) 
        status['irq']['aux-nco'][1]['event'] = bool((r & 0x02)>>1) 
        status['irq']['aux-nco'][0]['event'] = bool((r & 0x01)>>0) 
        
        r = dev.read_data(0x3010)
        status['irq']['dpll'][0]['freq-unclamped'] = bool((r&0x80)>>7)
        status['irq']['dpll'][0]['freq-clamped'] = bool((r&0x40)>>6)
        status['irq']['dpll'][0]['slew-limiter-inactive'] = bool((r&0x20)>>5)
        status['irq']['dpll'][0]['slew-limiter-active'] = bool((r&0x10)>>4)
        status['irq']['dpll'][0]['freq-unlocked'] = bool((r&0x08)>>3)
        status['irq']['dpll'][0]['freq-locked'] = bool((r&0x04)>>2)
        status['irq']['dpll'][0]['phase-unlocked'] = bool((r&0x02)>>1)
        status['irq']['dpll'][0]['phase-locked'] = bool((r&0x01)>>0)
        r = dev.read_data(0x3011)
        status['irq']['dpll'][0]['ref-switch'] = bool((r&0x80)>>7)
        status['irq']['dpll'][0]['free-run'] = bool((r&0x40)>>6)
        status['irq']['dpll'][0]['holdover'] = bool((r&0x20)>>5)
        status['irq']['dpll'][0]['hitless-entered'] = bool((r&0x10)>>4)
        status['irq']['dpll'][0]['hitless-exit'] = bool((r&0x08)>>3)
        status['irq']['dpll'][0]['holdover-ftw-upd'] = bool((r&0x04)>>1)
        status['irq']['dpll'][0]['phase-step'] = bool((r&0x01)>>0)
        
    if args.watchdog:
        status['watchdog'] = {}
        status['watchdog']['period'] = dev.read_data(0x10A) & 0xFF
        status['watchdog']['period'] |= (dev.read_data(0x10B) & 0xFF)<<8

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
            div = dev.read_data( base+0 )
            div += dev.read_data(base+1 ) << 8
            div += dev.read_data(base+2 ) << 16
            div += dev.read_data(base+3 ) << 24
            status['distrib']['ch0'][pin]['q-div'] = div
            offset = dev.read_data(base +4 )
            offset += dev.read_data(base+5 ) <<8
            offset += dev.read_data(base+6 ) <<16
            offset += dev.read_data(base+7 ) <<24
            r = dev.read_data(base+8)
            offset += ((r & 0x40)>>6) << 32
            status['distrib']['ch0'][pin]['phase-offset'] = offset
            status['distrib']['ch0'][pin]['half-div'] = enabled[(r & 0x20)>>5]
            status['distrib']['ch0'][pin]['pwm/phase'] = enabled[(r & 0x10)>>4]
            status['distrib']['ch0'][pin]['slew-mode'] = slew_mode[(r & 0x08)>>3]
            status['distrib']['ch0'][pin]['max-phase-slew'] = max_phase_slew[(r & 0x07)]
            base += 9

        mod = dev.read_data(0x10C0+0)
        mod += dev.read_data(0x10C1+1) << 8
        for pin in ['a','b','c']:
            q_div = status['distrib']['ch0'][pin]['q-div']
            try:
                status['distrib']['ch0'][pin]['mod-step'] = mod /2 /q_div
            except ZeroDivisionError:
                status['distrib']['ch0'][pin]['mod-step'] = 0
        
        base = 0x10C2
        for pin in ['a','b','c']:
            mod = dev.read_data(base+0)
            mod += dev.read_data(base+1) << 8
            mod += dev.read_data(base+2) << 16
            mod += (dev.read_data(base+3) &0x0F) << 24
            status['distrib']['ch0'][pin]['mod-counter'] = mod
            base += 6

        r = dev.read_data(0x10CE) & 0x03
        status['distrib']['ch0']['pll']['fb-div-sync-edge'] = r 

        base = 0x10CF
        for pin in ['a','b','c']:
            r = dev.read_data(base) & 0x0F
            status['distrib']['ch0'][pin]['n-shot-mod'] = shot_mod[(r & 0x08)>>3]
            status['distrib']['ch0'][pin]['single-pulse-modulation'] = single_pulse_mod[(r & 0x04)>>2]
            status['distrib']['ch0'][pin]['modulation-polarity'] = mod_polarity[(r & 0x02)>>1]
            status['distrib']['ch0'][pin]['modulation'] = enabled[r & 0x01]
            base += 1

        r = dev.read_data(0x10D2)
        status['distrib']['ch0']['pll']['n-shot-gap'] = r
        r = dev.read_data(0x10D3)
        status['distrib']['ch0']['pll']['n-shot-request-mode'] = n_shot_mod[(r & 0x40)>>6]
        status['distrib']['ch0']['pll']['n-shots'] = r & 0x3F

        r = dev.read_data(0x10D4)
        status['distrib']['ch0']['bb']['prbs'] = enabled[(r&0x80)>>7] 
        status['distrib']['ch0']['bb']['n-shot'] = enabled[(r&0x40)>>6]
        status['distrib']['ch0']['b']['prbs'] = enabled[(r&0x20)>>5]
        status['distrib']['ch0']['b']['n-shot'] = enabled[(r&0x10)>>4]
        status['distrib']['ch0']['aa']['prbs'] = enabled[(r&0x08)>>3] 
        status['distrib']['ch0']['aa']['n-shot'] = enabled[(r&0x04)>>2]
        status['distrib']['ch0']['a']['prbs'] = enabled[(r&0x02)>>1]
        status['distrib']['ch0']['a']['n-shot'] = enabled[r&0x01]
        r = dev.read_data(0x10D5)
        status['distrib']['ch0']['cc']['prbs'] = enabled[(r&0x08)>>3]
        status['distrib']['ch0']['cc']['n-shot'] = enabled[(r&0x04)>>2]
        status['distrib']['ch0']['c']['prbs'] = enabled[(r&0x02)>>1]
        status['distrib']['ch0']['c']['n-shot'] = enabled[r&0x01]
        r = dev.read_data(0x10D6)
        status['distrib']['ch0']['pll']['nshot-2-mod-retime'] = retime_to_mod[(r & 0x10)>>4]
        status['distrib']['ch0']['pll']['nshot-retiming'] = retiming[r & 0x01]

        base = 0x10D7
        for pin in ['a','b','c']:
            r = dev.read_data(base)
            status['distrib']['ch0'][pin]['mute-retiming'] = enabled[(r & 0x20)>>5]
            status['distrib']['ch0'][pin]['mode'] = modes[(r & 0x18)>>3]
            status['distrib']['ch0'][pin]['current'] = currents[(r & 0x03)>>1]
            status['distrib']['ch0'][pin]['format'] = fmts[r & 0x01]
            base += 1
        
        r = dev.read_data(0x310D)
        status['distrib']['ch0']['cc']['phase-slewing'] = enabled[(r & 0x20)>>5]
        status['distrib']['ch0']['c']['phase-slewing'] = enabled[(r & 0x10)>>4]
        status['distrib']['ch0']['bb']['phase-slewing'] = enabled[(r & 0x08)>>3]
        status['distrib']['ch0']['b']['phase-slewing'] = enabled[(r & 0x04)>>2]
        status['distrib']['ch0']['aa']['phase-slewing'] = enabled[(r & 0x02)>>1]
        status['distrib']['ch0']['a']['phase-slewing'] = enabled[r & 0x01]
        
        r = dev.read_data(0x310E)
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
            div = dev.read_data( base+0 )
            div += dev.read_data(base+1 ) << 8
            div += dev.read_data(base+2 ) << 16
            div += dev.read_data(base+3 ) << 24
            status['distrib']['ch1'][pin]['q-div'] = div
            offset = dev.read_data(base +4 )
            offset += dev.read_data(base+5 ) <<8
            offset += dev.read_data(base+6 ) <<16
            offset += dev.read_data(base+7 ) <<24
            r = dev.read_data(base+8)
            offset += ((r & 0x40)>>6) << 32
            status['distrib']['ch1'][pin]['phase-offset'] = offset
            status['distrib']['ch1'][pin]['half-div'] = enabled[(r & 0x20)>>5]
            status['distrib']['ch1'][pin]['pwm/phase'] = enabled[(r & 0x10)>>4]
            status['distrib']['ch1'][pin]['slew-mode'] = slew_mode[(r & 0x08)>>3]
            status['distrib']['ch1'][pin]['max-phase-slew'] = max_phase_slew[(r & 0x07)]
            base += 9

        mod = dev.read_data(0x14C0+0)
        mod += dev.read_data(0x14C1+1) << 8
        for pin in ['a','b']:
            q_div = status['distrib']['ch1'][pin]['q-div']
            try:
                status['distrib']['ch1'][pin]['mod-step'] = mod /2 /q_div
            except ZeroDivisionError:
                status['distrib']['ch1'][pin]['mod-step'] = 0
        
        base = 0x14C2
        for pin in ['a','b']:
            mod = dev.read_data(base+0)
            mod += dev.read_data(base+1) << 8
            mod += dev.read_data(base+2) << 16
            mod += (dev.read_data(base+3) &0x0F) << 24
            status['distrib']['ch1'][pin]['mod-counter'] = mod
            base += 6

        r = dev.read_data(0x14CE) & 0x03
        status['distrib']['ch1']['pll']['fb-div-sync-edge'] = r 

        base = 0x14CF
        for pin in ['a','b']:
            r = dev.read_data(base) & 0x0F
            status['distrib']['ch1'][pin]['n-shot-mod'] = shot_mod[(r & 0x08)>>3]
            status['distrib']['ch1'][pin]['single-pulse-modulation'] = single_pulse_mod[(r & 0x04)>>2]
            status['distrib']['ch1'][pin]['modulation-polarity'] = mod_polarity[(r & 0x02)>>1]
            status['distrib']['ch1'][pin]['modulation'] = enabled[r & 0x01]
            base += 1

        r = dev.read_data(0x14D2)
        status['distrib']['ch1']['pll']['n-shot-gap'] = r
        r = dev.read_data(0x14D3)
        status['distrib']['ch1']['pll']['n-shot-request-mode'] = n_shot_mod[(r & 0x40)>>6]
        status['distrib']['ch1']['pll']['n-shots'] = r & 0x3F

        r = dev.read_data(0x14D4)
        status['distrib']['ch1']['bb']['prbs'] = enabled[(r&0x80)>>7] 
        status['distrib']['ch1']['bb']['n-shot'] = enabled[(r&0x40)>>6]
        status['distrib']['ch1']['b']['prbs'] = enabled[(r&0x20)>>5]
        status['distrib']['ch1']['b']['n-shot'] = enabled[(r&0x10)>>4]
        status['distrib']['ch1']['aa']['prbs'] = enabled[(r&0x08)>>3] 
        status['distrib']['ch1']['aa']['n-shot'] = enabled[(r&0x04)>>2]
        status['distrib']['ch1']['a']['prbs'] = enabled[(r&0x02)>>1]
        status['distrib']['ch1']['a']['n-shot'] = enabled[r&0x01]
        r = dev.read_data(0x14D6)
        status['distrib']['ch1']['pll']['nshot-2-mod-retime'] = retime_to_mod[(r & 0x10)>>4]
        status['distrib']['ch1']['pll']['nshot-retiming'] = retiming[r & 0x01]

        base = 0x14D7
        for pin in ['a','b']:
            r = dev.read_data(base)
            status['distrib']['ch1'][pin]['mute-retiming'] = enabled[(r & 0x20)>>5]
            status['distrib']['ch1'][pin]['mode'] = modes[(r & 0x18)>>3]
            status['distrib']['ch1'][pin]['current'] = currents[(r & 0x03)>>1]
            status['distrib']['ch1'][pin]['format'] = fmts[r & 0x01]
            base += 1
        
        r = dev.read_data(0x320D)
        status['distrib']['ch1']['bb']['phase-slewing'] = enabled[(r & 0x08)>>3]
        status['distrib']['ch1']['b']['phase-slewing'] = enabled[(r & 0x04)>>2]
        status['distrib']['ch1']['aa']['phase-slewing'] = enabled[(r & 0x02)>>1]
        status['distrib']['ch1']['a']['phase-slewing'] = enabled[r & 0x01]
        
        r = dev.read_data(0x320E)
        status['distrib']['ch1']['bb']['phase-ctrl-error'] = bool((r & 0x08)>>3)
        status['distrib']['ch1']['b']['phase-ctrl-error'] = bool((r & 0x04)>>2)
        status['distrib']['ch1']['aa']['phase-ctrl-error'] = bool((r & 0x02)>>1)
        status['distrib']['ch1']['a']['phase-ctrl-error'] = bool((r & 0x01)>>0)

        base = 0x2100
        for ch in ['ch0','ch1']:
            r = dev.read_data(base+0)
            status['distrib'][ch]['reset'] = bool((r & 0x04)>>2)
            status['distrib'][ch]['muted'] = bool((r & 0x02)>>1)
            r = dev.read_data(base+1)
            status['distrib'][ch]['outa']['reset'] = bool((r & 0x20)>>5)
            status['distrib'][ch]['outa']['power-down'] = bool((r & 0x10)>>4)
            status['distrib'][ch]['outa']['-']['muted'] = bool((r & 0x08)>>3)
            status['distrib'][ch]['outa']['+']['muted'] = bool((r & 0x04)>>2)
            r = dev.read_data(base+2)
            status['distrib'][ch]['outb']['reset'] = bool((r & 0x20)>>5)
            status['distrib'][ch]['outb']['power-down'] = bool((r & 0x10)>>4)
            status['distrib'][ch]['outb']['-']['muted'] = bool((r & 0x08)>>3)
            status['distrib'][ch]['outb']['+']['muted'] = bool((r & 0x04)>>2)
            if ch == 'ch0':
                r = dev.read_data(base+2)
                status['distrib'][ch]['outc']['reset'] = bool((r & 0x20)>>5)
                status['distrib'][ch]['outc']['power-down'] = bool((r & 0x10)>>4)
                status['distrib'][ch]['outc']['-']['muted'] = bool((r & 0x08)>>3)
                status['distrib'][ch]['outc']['+']['muted'] = bool((r & 0x04)>>2)
            base += 0x100
 
    if args.ccdpll:
        status['ccdpll'] = {}
        status['ccdpll']['ccs'] = {}
        status['ccdpll']['lock-detector'] = {}
        r = dev.read_data(0x0D00)
        r += dev.read_data(0x0D01) << 8
        status['ccdpll']['lock-detector']['threshold'] = r * pow(10,-12)
        status['ccdpll']['lock-detector']['fill'] = dev.read_data(0x0D02) 
        status['ccdpll']['lock-detector']['drain'] = dev.read_data(0x0D03) 
        r = dev.read_data(0x0D04)
        r += dev.read_data(0x0D05) << 8
        status['ccdpll']['lock-detector']['delay'] = r 

        sources = {
            0: 'REFA',
            1: 'REFAA',
            2: 'REFB',
            3: 'REFBB',
            6: 'aux-ref0',
            7: 'aux-ref1',
            11: 'aux-ref2',
            12: 'aux-ref3',
            30: 'local timescale immediate sync',
            31: 'None',
        }
        tagging = {
            0: 'normal',
            1: 'tagged',
        }

        base = 0x0D10
        for cr in ['cr0','cr1']:
            status['ccdpll'][cr] = {}
            r = dev.read_data(base+0)
            status['ccdpll'][cr]['enabled'] = bool((r&0x80)>>7)
            status['ccdpll'][cr]['ts-source'] = sources[r & 0x1F]

            r = dev.read_data(base +1)
            status['ccdpll'][cr]['ccs'] = {}
            status['ccdpll'][cr]['ccs']['tagging'] = tagging[(r & 0x80)>>7]
            status['ccdpll'][cr]['ccs']['source-sync'] = sources[(r & 0x1F)>>0]

            num = dev.read_data(base +2)
            num+= dev.read_data(base +3) <<8
            num+= dev.read_data(base +4) <<16
            num+= dev.read_data(base +5) <<24
            denom = dev.read_data(base +6)
            denom+= dev.read_data(base +7) <<8
            denom+= dev.read_data(base +8) <<16
            denom+= dev.read_data(base +9) <<24
            denom+= dev.read_data(base +10) <<32
            status['ccdpll'][cr]['numerator'] = num
            status['ccdpll'][cr]['denominator'] = denom
            skew = dev.read_data(base +11)
            skew+= dev.read_data(base +12)<<8
            skew+= dev.read_data(base +13)<<16
            status['ccdpll'][cr]['skew'] = skew * pow(2,-48)
            base += 0x010

        t = dev.read_data(0x0D30)
        t+= dev.read_data(0x0D31) <<8
        t+= dev.read_data(0x0D32) <<16
        t+= dev.read_data(0x0D33) <<24
        status['ccdpll']['ccs']['offset'] = t*pow(2,-48)

        skew = dev.read_data(0x0D34)
        skew+= dev.read_data(0x0D35)<<8
        skew+= dev.read_data(0x0D36)<<16
        status['ccdpll']['ccs']['skew-limit'] = '{:.3e} ppm'.format(skew * pow(2,-16))

        status['ccdpll']['ccs']['guard'] = {}
        guard = dev.read_data(0x0D37)
        guard+= dev.read_data(0x0D38)<<8
        status['ccdpll']['ccs']['guard']['latency'] = guard * pow(2,-16)
        guard = dev.read_data(0x0D39)
        guard+= dev.read_data(0x0D3A)<<8
        guard+= (dev.read_data(0x0D3B) & 0x0F)<<16
        status['ccdpll']['ccs']['guard']['adjustment'] = guard * pow(2,-12)
        status['ccdpll']['ccs']['guard']['bypass-lock'] = bool(dev.read_data(0x0D3C)&0x01)

        r = dev.read_data(0x0D40)
        states = {
            0: 'normal',
            1: 'triggered by event',
        }
        slew_status = {
            0: 'not active',
            1: 'actively limiting',
        }
        valid = {
            0: 'invalid',
            1: 'valid',
        }
        primary = {
            0: "primary",
            1: "secondary",
        }
        status['ccdpll']['ccs']['guard']['status'] = states[(r & 0x80)>>7] 
        status['ccdpll']['ccs']['slew-limiter-status'] = slew_status[(r & 0x40)>>6] 
        status['ccdpll']['cr1']['source'] = valid[(r & 0x20)>>5] 
        status['ccdpll']['cr0']['source'] = valid[(r & 0x10)>>4]
        status['ccdpll']['active-source'] = primary[(r & 0x80)>>3]
        status['ccdpll']['ready'] = bool((r & 0x04)>>2)
        status['ccdpll']['phase-locked'] = bool((r & 0x02)>>1)
        status['ccdpll']['active'] = bool((r & 0x01)>>0)

    if args.uts:
        dev.io_update() # triggers UTPSx latching, that
            # we deal with at the very end

        status['uts'] = {}
        base = 0x0E00
        offset = 0x05
        formats = {
            0: 'normal',
            1: 'ptp',
        }
        sources = {
            0: 'REFA',
            1: 'REFAA',
            2: 'REFB',
            3: 'REFBB',
            4: 'dpll0',
            5: 'dpll1',
            6: 'aux-ref0',
            7: 'aux-ref1',
            8: 'aux-nco0',
            9: 'aux-nco1',
            11: 'aux-ref2',
            12: 'aux-ref3',
            13: 'iuts0',
            14: 'iuts1',
        }

        for c in range (9):
            status['uts'][str(c)] = {}
            r = dev.read_data(base + c*offset) & 0x0F
            status['uts'][str(c)]['format'] = formats[(r & 0x02)>>1] 
            status['uts'][str(c)]['enabled'] = bool((r&0x01)>>0)
            flags = (r & 0x1C)>>2
            (invalid, fault, unlocked, fmt, tag) = (False,False,False,False,False)
            if flags == 0:
                tag = True
                invalid = True
                unlocked = True
            elif flags == 1:
                tag = True
                fault = True
                unlocked = True
            elif flags == 2:
                fmt = True
                invalid = True
                unlocked = True
            elif flags == 3:
                fmt = True
                fault = True
                unlocked = True
            elif flags == 4:
                fault = True
                invalid = True
                unlocked = True
            elif flags == 5:
                fmt = True
                tag = True
                unlocked = True
                invalid = True
            elif flags == 6:
                fmt = True
                tag = True
                unlocked = True
                fault = True
            status['uts'][str(c)]['flags'] = {}
            status['uts'][str(c)]['flags']['invalid'] = invalid
            status['uts'][str(c)]['flags']['fault'] = fault
            status['uts'][str(c)]['flags']['unlocked'] = fault
            status['uts'][str(c)]['flags']['format'] = fmt
            status['uts'][str(c)]['flags']['tag'] = tag

            r = dev.read_data(base+1 + c*offset)
            status['uts'][str(c)]['tagged-timestamps'] = bool((r&0x10)>>4)
            status['uts'][str(c)]['source'] = sources[(r & 0x1F)]

            v = dev.read_data(base+2 +c*offset)
            v += dev.read_data(base+3 +c*offset) << 8
            v += dev.read_data(base+4 +c*offset) << 16
            status['uts'][str(c)]['reading'] = sign_extend(v,48) * pow(2,-48) # 1 bit = 1sec/2^48

        r = dev.read_data(0x0E2D)
        status['uts']['fifo'] = {}
        status['uts']['fifo']['overfill'] = bool((r & 0x80)>>7)
        status['uts']['fifo']['count'] = r & 0x7F
        r = dev.read_data(0x0E2E)
        status['uts']['fifo']['flags'] = (r & 0xE0)>>5
        status['uts']['fifo']['source'] = sources[(r & 0x1F)]
        v0 = dev.read_data(0x0E2F)
        v0 += dev.read_data(0x0E30) << 8 
        v0 += dev.read_data(0x0E31) << 16 
        v0 += dev.read_data(0x0E32) << 24 
        v0 += dev.read_data(0x0E33) << 32 
        v0 += dev.read_data(0x0E34) << 40 
        v1 = dev.read_data(0x0E35) 
        v1 += dev.read_data(0x0E36) << 8
        v1 += dev.read_data(0x0E37) << 16 
        v1 += dev.read_data(0x0E38) << 24 
        v1 += dev.read_data(0x0E39) << 32 
        v1 += dev.read_data(0x0E3A) << 40 
        status['uts']['fifo']['timecode'] = {}
        status['uts']['fifo']['timecode']['s'] = v1
        if status['uts']['0']['format'] == 'ptp':
            ns = sign_extend(v0 & 0x3FFFFFFFFFFF, 48)
            status['uts']['fifo']['timecode']['ns'] = ns * pow(2,-16)
        else:
            ns = sign_extend(v0, 48)
            status['uts']['fifo']['timecode']['ns'] = ns * pow(2,-48)

        base = 0x3A14
        for ch in range(2):
            status['uts'][str(ch)]['output'] = {}
            itg = dev.read_data(base)
            itg+= dev.read_data(base+1)<<8
            itg+= dev.read_data(base+2)<<16
            itg+= dev.read_data(base+3)<<24
            itg+= dev.read_data(base+4)<<32
            fract = dev.read_data(base+5)
            fract+= dev.read_data(base+6)<<8
            fract+= dev.read_data(base+7)<<16
            fract+= dev.read_data(base+8)<<24
            fract+= dev.read_data(base+9)<<32
            t0 = 1 # TODO retrieve time scale 
            status['uts'][str(ch)]['output']['integer'] = itg * t0 
            status['uts'][str(ch)]['output']['fractionnal'] = fract * t0 * pow(2,-40)
            status['uts'][str(ch)]['missed'] = dev.read_data(base+10)
            status['uts'][str(ch)]['overdue'] = bool(dev.read_data(base+11) & 0x01)
            base += 12

    if args.iuts:
        status['iuts'] = {}
        base = 0x0F00
        offset = 0x04
        for i in range (2):
            status['iuts'][str(i)] = {}
            r = dev.read_data(base + offset * i)
            status['iuts'][str(i)]['bypass-ccdpll-lock'] = bool((r & 0x02)>>1)
            status['iuts'][str(i)]['valid'] = bool((r & 0x01)>>0)
            v = dev.read_data(base+1 + offset * i)
            v += dev.read_data(base+2 + offset * i) << 8
            v += dev.read_data(base+2 + offset * i) << 24
            status['iuts'][str(i)]['reading'] = sign_extend(v,32) * pow(2,-48)
        
        r = dev.read_data(0x0F09)
        formats = {
            0: 'normal',
            1: 'ptp',
        }
        destinations = {
            13: 'iuts0',
            14: 'iuts1',
            30: 'ccs sync0 timecode',
            31: 'ccs sync1 timecode',
        }
        status['iuts']['format'] = formats[(r & 0x80)>>7] 
        try:
            status['iuts']['destination'] = destinations[(r & 0x1F)]
        except KeyError:
            status['iuts']['destination'] = 'unknown/default' 
        v0 = dev.read_data(0x0F0A)
        v0 += dev.read_data(0x0F0B) << 8
        v0 += dev.read_data(0x0F0C) << 16
        v0 += dev.read_data(0x0F0D) << 24
        v0 += dev.read_data(0x0F0E) << 32
        v0 += dev.read_data(0x0F0F) << 40
        v1 = dev.read_data(0x0F10)
        v1 += dev.read_data(0x0F11) << 8
        v1 += dev.read_data(0x0F12) << 16
        v1 += dev.read_data(0x0F13) << 24
        v1 += dev.read_data(0x0F14) << 32
        v1 += dev.read_data(0x0F15) << 40
        status['iuts']['timecode'] = {}
        status['iuts']['timecode']['s'] = v0
        if status['iuts']['format'] == 'ptp':
            ns = sign_extend(v0 & 0x3FFFFFFFFFFF, 48)
            status['iuts']['timecode']['ns'] = ns *pow(2,-16)
        else:
            ns = sign_extend(v0, 48)
            status['iuts']['timecode']['ns'] = ns *pow(2,-48)
    
        r = dev.read_data(0x3023)
        status['iuts']['0']['valid'] = bool((r&0x02)>>1)
        status['iuts']['1']['valid'] = bool((r&0x01)>>0)

    #print("======== TOTAL ===============")
    #print(json.dumps(status, sort_keys=True, indent=2))
    #print("==============================")
 
    if args.filter_by_key:
        filters = args.filter_by_key.split(",")
        for _filter in filters:
            if _filter == filters[0]: # first filter
                # => create work structure
                filtered = {}
            for category in status.keys(): # filter all categories
                if _filter == filters[0]: # first filter
                    # => create work structure
                    filtered[category] = {}
                    # and work from status report
                    data = filter_by_key(status[category], _filter)
                else:
                    # work from already filtered data
                    data = filter_by_key(filtered[category], _filter)

                if len(data) == 0: # not a single match
                    # assumes incorrect key filter 
                    # ==> preserve complete data set
                    filtered[category] = status[category].copy()
                else:
                    filtered[category] |= data
    else: # plain copy
        filtered = status.copy()
                
    if args.filter_by_value:
        filters = args.filter_by_value.split(",")
        print("Filter by value is work in progress")
        #_filtered = {} # next dataset
        #for _filter in filters:
        #    # works on previously filtered dataset
        #    for category in filtered.keys(): 
        #        if not category in _filtered:
        #            _filtered[category] = {} # create work struct
        #        data = filter_by_value(filtered[category], _filter) 
        #        if len(data) > 0:
        #            _filtered[category] |= data 
        #filtered = _filtered.copy() # replace by possibily stripped dataset

    if args.unpack:
        filtered = unpack(filtered)

    print(json.dumps(filtered, sort_keys=True, indent=2))
    
if __name__ == "__main__":
    main(sys.argv[1:])
