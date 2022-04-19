#! /usr/bin/env python3
import sys
import json
import fcntl
import argparse

IOCTL_I2C_SLAVE = 0x0703

KNOWN_DEVICES = [
    "ad9548",
    "ad9546",
    "ad9545",
]

RANGES = {
    "ad9548": [0x00, 0x0E3F], 
    "ad9546": [0x00, 0x3A3B], 
    "ad9545": [0x00, 0x3A3B], 
}

def main (argv):
    
    parser = argparse.ArgumentParser(description="Load / dump a profile into AD95xx chipsets")
    parser.add_argument("-b", "--bus", metavar="bus", type=int, default=0, help="I2C bus #")
    parser.add_argument("-a", "--address", metavar="address", type=lambda x: int(x,0), help="I2C slave address (hex)")
    parser.add_argument("-c", "--chip", metavar="chip", type=str, choices=KNOWN_DEVICES, help="Select A&D chip")
    parser.add_argument("-v", "--verbose", metavar="verbose", type=bool, default=False)
    parser.add_argument("-l", "--load", metavar="load", type=str, help="Load given profile")
    parser.add_argument("-d", "--dump", metavar="dump", type=str, help="Dump current profile")
    args = parser.parse_args(argv)

    i2c_handle = open("/dev/i2c-{}".format(args.bus), "wb", buffering=0)
    fnctl.ioctl(i2c_handle, IOCTL_I2C_SLAVE, args.address)
    
    if args.load:
        with open(args.load, encoding="utf-8-sig") as f:
            data = json.load(f)
            regmap = data["RegisterMap"]
            for addr in regmap:
                _addr = int(addr, 16) # hex() 
                value = int(regmap[addr], 16) # hex()
                # 2 address bytes
                (msb, lsb) = ((_addr & 0xFF00)>>8, _addr & 0x00FF)
                i2c_handle.write(bytearray[msb, lsb, value])

    if args.dump:
        rg = RANGES[args.chipset]
        # create a json struct
        struct = {}
        struct[args.chipset] = {}
        struct[args.chipset]["_gui_version"] = "1.0.0.0"
        struct[args.chipset]["_die_version"] = "4198933" # ??
        struct[args.chipset]["notes"] = {}
        struct[args.chipset]["bitfields"] = {}
        struct[args.chipset]["read only"] = {}
        struct[args.chipset]["wizard"] = {}
        struct["wizard"] = {} 
        struct["wizard"]["version"] = "1.0.0.0"
        struct["RegisterMap"] = {}
        for i in range (r[0],r[1]+1):
            # 2 address bytes
            (msb, lsb) = ((i & 0xFF00)>>8, i & 0x00FF)
            i2c_handle.write(bytearray[msb, lsb])
            # 1 data byte
            data = i2c_handle.read(1)
            struct["RegisterMap"][hex(i)] = data
        json.dumps(struct, sort_keys=True, indent=4)

if __name__ == "__main__":
    main(sys.argv[1:])
