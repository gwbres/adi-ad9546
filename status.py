#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# status.py
# small script to quickly monitor an AD9545,46 
#################################################################
import sys
import math
import argparse
from smbus import SMBus
from pprint import pprint

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
        ("sysclk-pll",  "Sys clock pll core focus"),
        ("sysclk-comp", "Sys clock compensation core infos"),
        ("pll", "Pll (APll+DPll+CH0/CH1) info"),
        ("pll-ch0", "APll + DPll CH0 infos"),
        ("q-ch0", "Qxx CH0 infos"),
        ("pll-ch1", "APll + DPll CH1 infos"),
        ("q-ch1", "Qxx CH1 infos"),
        ("ref-input",  "REFx signal info"),
        ("irq", "IRQ registers"),
        ("watchdog", "Watchdog timer period"),
        ('distrib', 'Clock distribution related infos'),
        ("iuts", None),
        ("temp", "Reads temperature sensor [°C]"),
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
    args = parser.parse_args(argv)

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    status = {}
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
    if args.sysclk or args.sysclk_pll:
        status['sysclk'] = {}
        status['sysclk']['pll'] = {}
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
    if args.sysclk or args.sysclk_comp:
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
        bitfields = [
            ('pll1-locked', 0x20),
            ('pll0-locked', 0x10),
            ('sys-clock-calibrating', 0x04),
            ('sys-clock-stable', 0x02),
            ('sys-clock-locked', 0x01),
        ]
        read_reg(handle, address, status, 'pll', 0x3001, bitfields)
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
        for ref in ['a','aa','b','bb']:
            status['ref-input'][ref] = {}
        for ref in ['ref0-aux', 'ref1-aux', 'ref2-aux', 'ref3-aux']:
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

        base = 0x030A
        for ref in ['ref0-aux','ref1-aux']:
            r = read_data(handle, address, base)
            status['ref-input'][ref]['demod-polarity'] = demod_polarity[(r & 0x80)>>7]
            status['ref-input'][ref]['demod-persist-enabled'] = bool((r & 0x40)>>6)
            status['ref-input'][ref]['demod-sync-edge'] = (r & 0x30)>>4
            status['ref-input'][ref]['demod-enabled'] = bool((r & 0x80)>>3)
            status['ref-input'][ref]['demod-event-pol'] = event_pol[(r & 0x04)>>2]
            status['ref-input'][ref]['demod-sensitivity'] = r & 0x03
            base += 1
        
        base = 0x030E
        for ref in ['ref2-aux','ref3-aux']:
            r = read_data(handle, address, base)
            status['ref-input'][ref]['demod-polarity'] = demod_polarity[(r & 0x80)>>7]
            status['ref-input'][ref]['demod-persist-enabled'] = bool((r & 0x40)>>6)
            status['ref-input'][ref]['demod-sync-edge'] = (r & 0x30)>>4
            status['ref-input'][ref]['demod-enabled'] = bool((r & 0x80)>>3)
            status['ref-input'][ref]['demod-event-pol'] = event_pol[(r & 0x04)>>2]
            status['ref-input'][ref]['demod-sensitivity'] = r & 0x03
            base += 1

        base = 0x0400
        for ref in ['a','aa','b','bb']:
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
            read_reg(handle, address, status['ref-input'], ref, base, bitfields)
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
    if args.pll_ch0:
        bitfields = [
            ('apll0-calib-done', 0x20),
            ('apll0-calib-busy', 0x10),
            ('apll0-phase-locked', 0x08),
            ('dpll0-freq-locked', 0x04),
            ('dpll0-phase-locked', 0x02),
            ('dpll0-locked', 0x02),
        ]
        read_reg(handle, address, status, 'pll-ch0', 0x3100, bitfields)
        data = read_data(handle, address, 0x3101)
        status['pll-ch0']['dpll0-profile'] = (data & 0x20)>>8
        status['pll-ch0']['dpll0-active'] = (data & 0x08)>>3
        status['pll-ch0']['dpll0-profile-switch'] = (data & 0x04)>>2
        status['pll-ch0']['dpll0-holdover'] = (data & 0x02)>>1
        status['pll-ch0']['dpll0-freerun'] = (data & 0x01)
        bitfields = [
            ('dpll0-fast-acq-complete',0x10),
            ('dpll0-fast-acq',0x08),
            ('dpll0-limiting-phase-slew',0x04),
            ('dpll0-clamping-freq',0x02),
            ('dpll0-tuning-history-avail',0x01),
        ]
        read_reg(handle, address, status, 'pll-ch0', 0x3102, bitfields)
    if args.pll_ch1:
        bitfields = [
            ('apll1-calib-done', 0x20),
            ('apll1-calib-busy', 0x10),
            ('apll1-phase-locked', 0x08),
            ('dpll1-freq-locked', 0x04),
            ('dpll1phase-locked', 0x02),
            ('dpll1-locked', 0x02),
        ]
        read_reg(handle, address, status, 'pll-ch1', 0x3200, bitfields)
        data = read_data(handle, address, 0x3201)
        status['pll-ch1']['dpll1-profile'] = (data & 0x20)>>8
        status['pll-ch1']['dpll1-active'] = (data & 0x08)>>3
        status['pll-ch1']['dpll1-profile-switch'] = (data & 0x04)>>2
        status['pll-ch1']['dpll1-holdover'] = (data & 0x02)>>1
        status['pll-ch1']['dpll1-freerun'] = (data & 0x01)
        bitfields = [
            ('dpll1-fast-acq-complete',0x10),
            ('dpll1-fast-acq',0x08),
            ('dpll1-limiting-phase-slew',0x04),
            ('dpll1-clamping-freq',0x02),
            ('dpll1-tuning-history-avail',0x01),
        ]
        read_reg(handle, address, status, 'pll-ch1', 0x3202, bitfields)
    if args.q_ch0:
        bitfields = [
            ('q0cc-phase-slew', 0x20),
            ('q0c-phase-slew', 0x10),
            ('q0bb-phase-slew', 0x08),
            ('q0b-phase-slew', 0x04),
            ('q0aa-phase-slew', 0x02),
            ('q0a-phase-slew', 0x01),
        ]
        read_reg(handle, address, status, 'q-ch0', 0x310D, bitfields)
        bitfields = [
            ('q0cc-phase-ctrl-err', 0x20),
            ('q0c-phase-ctrl-err', 0x10),
            ('q0bb-phase-ctrl-err', 0x08),
            ('q0b-phase-ctrl-err', 0x04),
            ('q0aa-phase-ctrl-err', 0x02),
            ('q0a-phase-ctrl-err', 0x01),
        ]
        read_reg(handle, address, status, 'q-ch0', 0x310E, bitfields)
    if args.q_ch1:
        bitfields = [
            ('q1bb-phase-slew', 0x08),
            ('q1b-phase-slew', 0x04),
            ('q1aa-phase-slew', 0x02),
            ('q1a-phase-slew', 0x01),
        ]
        read_reg(handle, address, status, 'q-ch1', 0x320D, bitfields)
        bitfields = [
            ('q1bb-phase-ctrl-err', 0x08),
            ('q1b-phase-ctrl-err', 0x04),
            ('q1aa-phase-ctrl-err', 0x02),
            ('q1a-phase-ctrl-err', 0x01),
        ]
        read_reg(handle, address, status, 'q-ch1', 0x320E, bitfields)
    if args.temp:
        temp = (read_data(handle, address, 0x3004) & 0xFF)<< 8 
        temp |= read_data(handle, address, 0x3003) & 0xFF
        status['temp'] = {}
        status['temp']['reading'] = temp * pow(2,-7)

    if args.distrib:
        status['distrib'] = {}
        for ch in ['ch0','ch1']:
            status['distrib'][ch] = {}
            pins = ['a','aa','b','bb']
            if ch == 'ch0':
                pins.append('c')
                pins.append('cc')
            for pin in pins:
                status['distrib'][ch][pin] = {}
        
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
        
        r = read_data(handle, address, 0x10D7)
        status['distrib']['ch0']['a']['format'] = fmts[r & 0x01]
        status['distrib']['ch0']['a']['current'] = currents[(r & 0x03)>>1]
        status['distrib']['ch0']['a']['mode'] = modes[(r & 0x04)>>3]
        r = read_data(handle, address, 0x10D8)
        status['distrib']['ch0']['b']['format'] = fmts[r & 0x01]
        status['distrib']['ch0']['b']['current'] = currents[(r & 0x03)>>1]
        status['distrib']['ch0']['b']['mode'] = modes[(r & 0x04)>>3]
        r = read_data(handle, address, 0x10D9)
        status['distrib']['ch0']['c']['format'] = fmts[r & 0x01]
        status['distrib']['ch0']['c']['current'] = currents[(r & 0x03)>>1]
        status['distrib']['ch0']['c']['mode'] = modes[(r & 0x04)>>3]
    pprint(status)
    
if __name__ == "__main__":
    main(sys.argv[1:])
