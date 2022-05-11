#! /usr/bin/env python3
#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# regmap.py: load/dump a register map into device
#################################################################
import sys
import json
import argparse
from ad9546 import *

REGMAP = [
    (0x0000, 0x0001),
    (0x0003, 0x0006),
    (0x000B, 0x000D),
    (0x000F, 0x0010),
    (0x0020, 0x0023),
    (0x0100, 0x011F),
    (0x0182, 0x0188),
    (0x0200, 0x0209),
    (0x0280, 0x029C),
    (0x0300, 0x0307),
    (0x030A, 0x030B),
    (0x030E, 0x030F),
    (0x0400, 0x0414),
    (0x0420, 0x0434), 
    (0x0440, 0x0454),
    (0x0460, 0x0474),
    (0x0480, 0x0494),
    (0x04A0, 0x04B4),
    (0x04C0, 0x04D4),
    (0x04E0, 0x04F4),
    (0x0800, 0x0811),
    (0x0820, 0x0831),
    (0x0840, 0x0851),
    (0x0860, 0x0871),
    (0x0880, 0x0891),
    (0x08A0, 0x08B1),
    (0x08C0, 0x08D1),
    (0x08E0, 0x08F1),
    (0x0900, 0x0911),
    (0x0920, 0x0931),
    (0x0940, 0x0951),
    (0x0960, 0x0971),
    (0x0980, 0x0991),
    (0x09A0, 0x09B1),
    (0x0C00, 0x0C17),
    (0x0D00, 0x0D05),
    (0x0D10, 0x0D1D),
    (0x0D20, 0x0D2D),
    (0x0D30, 0x0D3C),
    (0x0D40, 0x0D40),
    (0x0E00, 0x0E3A),
    (0x0F00, 0x0F15),
    (0x1000, 0x102B),
    (0x1080, 0x1083),
    (0x10C0, 0x10DC),
    (0x1100, 0x1135),
    (0x1200, 0x1217),
    (0x1220, 0x1237),
    (0x1240, 0x1257),
    (0x1260, 0x1277),
    (0x1280, 0x1297),
    (0x12A0, 0x12B7),
    (0x1400, 0x142B),
    (0x1480, 0x1483),
    (0x14C0, 0x14C9),
    (0x14CE, 0x14D0),
    (0x14D2, 0x14D4),
    (0x14D6, 0x14D8),
    (0x14DA, 0x14DC), 
    (0x1500, 0x1523),
    (0x1600, 0x1617),
    (0x1620, 0x1637),
    (0x1640, 0x1657),
    (0x1660, 0x1677),
    (0x1680, 0x1697),
    (0x16A0, 0x16B7),
    (0x2000, 0x2019),
    (0x2100, 0x2107),
    (0x2200, 0x2203),
    (0x2205, 0x2207),
    (0x2800, 0x281E),
    (0x2840, 0x285E),
    (0x2900, 0x2906),
    (0x2A00, 0x2A1A),
    (0x2C00, 0x2C07),
    (0x2D00, 0x2D02),
    (0x2D08, 0x2D0A),
    (0x2E00, 0x2E03),
    (0x2E10, 0x2E1E),
    (0x3000, 0x3023),
    (0x3100, 0x310E),
    (0x3200, 0x320E),
    (0x3A00, 0x3A3B),
]

def regmap_size():
    s = 0
    for (start, stop) in REGMAP:
        s += stop-start+1
    return s

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
    parser = argparse.ArgumentParser(description="Load /dump a regmap into AD9546 chipset")
    parser.add_argument(
        "bus",
        metavar="bus",
        type=int,
        default=0,
        help="I2C bus #")
    parser.add_argument(
        "address",
        metavar="address",
        type=str,
        help="I2C slave address (hex format)")
    parser.add_argument(
        "--load",
        metavar="filepath",
        type=str,
        help="Load given regmap")
    parser.add_argument(
        "--dump",
        metavar="filepath",
        type=str,
        help="Dump current regmap")
    parser.add_argument(
        "--chip",
        metavar="{}".format(str(KNOWN_DEVICES)),
        type=str,
        choices=KNOWN_DEVICES,
        default=KNOWN_DEVICES[0],
        help="Accurately describe the chip when --dumping a regmap"
    )
    parser.add_argument(
        "--quiet",
        default=False,
        action="store_true",
        help="Disable progress bar",
    )
    args = parser.parse_args(argv)
    # open device
    dev = AD9546(int(args.bus), int(args.address, 16))

    progress = 0
    update_perc = 5

    if args.load:
        with open(args.load, encoding="utf-8-sig") as f:
            data = json.load(f)
            regmap = data["RegisterMap"]
            size = regmap_size()
            for addr in regmap:
                value = int(regmap[addr], 16) & 0xFF # 1 byte from hex()
                # 2 address bytes
                _addr = int(addr, 16)
                dev.write_data(_addr, value)
                if not args.quiet:
                    progress += 100 / size
                    if int(progress) % update_perc:
                        progress_bar(int(progress),width=50)
            dev.io_update()

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
        size = regmap_size()
        for (start, stop) in REGMAP:
            for i in range (start, stop+1):
                data = dev.read_data(i) # reads 1 byte
                struct["RegisterMap"]["0x{:04X}".format(i)] = "0x{:02X}".format(data)
                if not args.quiet:
                    progress += 100 / size
                    if int(progress) % update_perc:
                        progress_bar(int(progress),width=50)
        struct = json.dumps(struct, sort_keys=True, indent=4)
        with open(args.dump, "w") as fd:
            fd.write(struct)

if __name__ == "__main__":
    main(sys.argv[1:])
