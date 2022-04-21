#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# profile.py
# small script to quickly load a profile into an AD9545,46 
#################################################################
import sys
import json
import argparse
from smbus import SMBus

REGMAP = [0x00, 0x3A3B]
KNOWN_DEVICES = ["ad9545","ad9546"]

def main (argv):
    parser = argparse.ArgumentParser(description="Load / dump a profile into AD9545,AD9546 chip")
    parser.add_argument(
        "bus", 
        metavar="bus", 
        type=int, 
        default=0, 
        help="I2C bus #")
    parser.add_argument(
        "address", 
        metavar="address", 
        type=lambda x: int(x,0), 
        help="I2C slave address (hex)")
    parser.add_argument(
        "-l", 
        "--load", 
        metavar="filepath",
        type=str, 
        help="Load given profile")
    parser.add_argument(
        "-d", 
        "--dump", 
        metavar="filepath", 
        type=str, 
        help="Dump current profile")
    parser.add_argument(
        "-c", 
        "--chip", 
        metavar="{}".format(str(KNOWN_DEVICES)),
        type=str,
        choices=KNOWN_DEVICES,
        default=KNOWN_DEVICES[0],
        help="Accurately describe the chip when --dumping a profile"
    )
    args = parser.parse_args(argv)

    handle = SMBus()
    handle.open(int(args.bus))
    address = int(args.address, 16)
    
    if args.load:
        with open(args.load, encoding="utf-8-sig") as f:
            data = json.load(f)
            regmap = data["RegisterMap"]
            for addr in regmap:
                value = int(regmap[addr], 16) # hex()
                # 2 address bytes
                msb = int(addr, 16) & 0xFF00)>>8
                lsb = int(addr, 16) & 0x00FF)
                handle.write_i2c_block_data(address, msb, [lsb])

    if args.dump:
        # create a json struct
        struct = {}
        struct[args.chip] = {}
        struct[args.chip]["_gui_version"] = "1.0.0.0"
        struct[args.chip]["_die_version"] = "4198933" # ??
        struct[args.chip]["notes"] = {}
        struct[args.chip]["bitfields"] = {}
        struct[args.chip]["read only"] = {}
        struct[args.chip]["wizard"] = {}
        struct["wizard"] = {} 
        struct["wizard"]["version"] = "1.0.0.0"
        struct["RegisterMap"] = {}
        for i in range (REGMAP[0],REGMAP[1]+1):
            # 2 address bytes
            (msb, lsb) = ((i & 0xFF00)>>8, i & 0x00FF)
            handle.write_i2c_block_data(address, msb, [lsb])
            # 1 data byte
            data = handle.read_i2c_block_data(dev, 0, 1)[0]
            struct["RegisterMap"][hex(i)] = data
        json.dumps(struct, sort_keys=True, indent=4)

if __name__ == "__main__":
    main(sys.argv[1:])
