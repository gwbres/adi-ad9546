#! /usr/bin/env python3
import sys
import json
import math
import argparse
from smbus import SMBus
from pprint import pprint

IOCTL_I2C_SLAVE = 0x0703
REGMAP = [0x00, 0x3A3B]
KNOWN_DEVICES = ["ad9545","ad9546"]

def read_data (handle, dev, addr):
    lsb = addr & 0xFF
    msb = addr & (0xFF00)>>8
    handle.write_i2c_block_data(dev, msb, [lsb])
    data = handle.read_i2c_block_data(dev, 0, 1)[0]
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
    parser = argparse.ArgumentParser(description="Clock status reporting")
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
        ("sysclk-pll",  "Sys clock synthesis pll"),
        ("sysclk-comp", "Sys clock compensation"),
        ("pll", "Shared Pll global info"),
        ("pll0", "Pll0 core infos"),
        ("pll1", "Pll1 core infos"),
        ("pll-ch0", "APll0 + DPll0 infos"),
        ("pll-ch1", "APll1 + DPll1 infos"),
        ("refa",  "REF-A signal info"),
        ("refaa", "REF-AA signal info"),
        ("refb",  "REF-B signal info"),
        ("refbb", "REF-BB signal info"),
        ("irq", "IRQ registers"),
        ("iuts", None),
        ("temp", "Internal temperature sensor"),
        ("eeprom", "EEPROM controller status"),
        ("misc", "Auxilary NCOs, DPll and Temp info"),
    ]
    for (flag, helper) in flags:
        _helper = helper if helper is not None else "Report {} Status".format(flag.upper())
        parser.add_argument(
            "-{}".format(flag), 
            action="store_true",
            help=_helper,
        )
    args = parser.parse_args(argv)

    # open device
    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)

    status = {}
    if args.info:
        status['info'] = {}
        status['info']['chip-type'] = hex(read_data(handle, address, 0x0003) & 0x0F)
        
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
    if args.sysclk_pll:
        status['sysclk-pll'] = {}
        data = read_data(handle, address, 0x200) 
        status['sysclk-pll']['fb-div-ratio'] = data
        data = read_data(handle, address, 0x201) 
        status['sysclk-pll']['input-path-sel'] = int((data & 0x04) >>3)
        status['sysclk-pll']['input-div-ratio'] = int((data & 0x06)>>1)
        status['sysclk-pll']['freq-doubler'] = int(data & 0x01)
        ref_freq = read_data(handle, address, 0x202)
        ref_freq += read_data(handle, address, 0x203)
        ref_freq += read_data(handle, address, 0x204)
        ref_freq += read_data(handle, address, 0x205)
        ref_freq += read_data(handle, address, 0x206)
        status['sysclk-pll']['ref-freq'] = ref_freq
        per  = (read_data(handle, address, 0x208) & 0x0F) << 8
        per += read_data(handle, address, 0x207) & 0x0F
        status['sysclk-pll']['stability-period'] = read_data(handle, address, 0x207) & 0x0F
    if args.sysclk_comp:
        bitfields = [
            ('method2-aux-dpll', 0x20),
            ('method1-aux-dpll', 0x10),
            ('method3-tdcs', 0x04),
            ('method2-tdcs', 0x02),
            ('method1-tdcs', 0x01),
        ]
        read_reg(handle, address, status, 'sysclk-comp', 0x0280, bitfields)
        bitfields = [
            ('method3-aux-nco1', 0x40),
            ('method2-aux-nco1', 0x20),
            ('method1-aux-nco1', 0x10),
            ('method3-aux-nco0', 0x04),
            ('method2-aux-nco0', 0x02),
            ('method1-aux-nco0', 0x01),
        ]
        read_reg(handle, address, status, 'sysclk-comp', 0x0281, bitfields)
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
    if args.refa:
        bitfields = [
            ('loss-of-signal', 0x20),
            ('valid', 0x10),
            ('fault', 0x08),
            ('jitter-excess', 0x04),
            ('fast', 0x02),
            ('slow', 0x01),
        ]
        read_reg(handle, address, status, 'refa', 0x3005, bitfields)
    if args.refaa:
        bitfields = [
            ('loss-of-signal', 0x20),
            ('valid', 0x10),
            ('fault', 0x08),
            ('jitter-excess', 0x04),
            ('fast', 0x02),
            ('slow', 0x01),
        ]
        read_reg(handle, address, status, 'refaa', 0x3006, bitfields)
    if args.refb:
        bitfields = [
            ('loss-of-signal', 0x20),
            ('valid', 0x10),
            ('fault', 0x08),
            ('jitter-excess', 0x04),
            ('fast', 0x02),
            ('slow', 0x01),
        ]
        read_reg(handle, address, status, 'refb', 0x3007, bitfields)
    if args.refbb:
        bitfields = [
            ('loss-of-signal', 0x20),
            ('valid', 0x10),
            ('fault', 0x08),
            ('jitter-excess', 0x04),
            ('fast', 0x02),
            ('slow', 0x01),
        ]
        read_reg(handle, address, status, 'refbb', 0x3008, bitfields)
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
    if args.temp:
        temp = (read_data(handle, address, 0x3004) & 0xFF)<< 8 
        temp |= read_data(handle, address, 0x3003) & 0xFF
        status['temp'] = {}
        status['temp']['reading'] = temp * pow(2,-7)

    pprint(status)
    
if __name__ == "__main__":
    main(sys.argv[1:])
