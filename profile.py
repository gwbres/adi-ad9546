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

def progress_bar (progress, width=100):
    """ displays progress bar,
        progress: current progress [%],
        width: `pixel` width
    """
    bar = "["
    bar += "\x1b[0;32m" # green
    r = 100 // width
    for i in range (width):
        if progress >= i * r:
            bar += "█"
        else:
            bar += " "
    bar += "\x1b[0m"    # stop
    bar += "]    {}%".format(progress)
    sys.stdout.write('\r' + bar)
    sys.stdout.flush()

def main (argv):
    parser = argparse.ArgumentParser(description="Load /dump a profile into/from AD9545,46 chipset")
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
        "--load", 
        metavar="filepath",
        type=str, 
        help="Load given profile")
    parser.add_argument(
        "--dump", 
        metavar="filepath", 
        type=str, 
        help="Dump current profile")
    parser.add_argument(
        "--chip", 
        metavar="{}".format(str(KNOWN_DEVICES)),
        type=str,
        choices=KNOWN_DEVICES,
        default=KNOWN_DEVICES[0],
        help="Accurately describe the chip when --dumping a profile"
    )
    parser.add_argument(
        "--quiet",
        default=False,
        action="store_true",
        help="Disable progress bar",
    )
    args = parser.parse_args(argv)

    handle = SMBus()
    handle.open(int(args.bus))
    address = args.address

    progress = 0
    update_perc = 5

    if args.load:
        with open(args.load, encoding="utf-8-sig") as f:
            data = json.load(f)
            regmap = data["RegisterMap"]
            N = len(regmap)
            for addr in regmap:
                value = int(regmap[addr], 16) & 0xFF # 1 byte from hex()
                # 2 address bytes
                _addr = int(addr, 16)
                msb = (_addr & 0xFF00)>>8
                lsb = _addr & 0xFF
                handle.write_i2c_block_data(address, msb, [lsb, value])
                if not args.quiet:
                    progress += 100 / N
                    if int(progress) % update_perc:
                        progress_bar(int(progress),width=50)
            handle.write_i2c_block_data(address, 0x00, [0x0F, 0x01]) # I/O update

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
        N = REGMAP[1]+1
        for i in range (REGMAP[0],N):
            # 2 address bytes
            (msb, lsb) = ((i & 0xFF00)>>8, i & 0xFF)
            handle.write_i2c_block_data(address, msb, [lsb])
            # 1 data byte
            data = handle.read_byte(address)
            struct["RegisterMap"]["0x{:04X}".format(i)] = "0x{:02X}".format(data)
            if not args.quiet:
                progress += 100 / N
                if int(progress) % update_perc:
                    progress_bar(int(progress),width=50)
        struct = json.dumps(struct, sort_keys=True, indent=4)
        with open(args.dump, "w") as fd:
            fd.write(struct)

if __name__ == "__main__":
    main(sys.argv[1:])
