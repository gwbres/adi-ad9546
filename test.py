#! /usr/bin/env python3
import json
from ad9546 import *

def main ():
    dev = AD9546("fake")
    #print(json.dumps(dev.regmap, sort_keys=True, indent=2))
    #return 0
    
    print("==============================================")
    print("             MMAP special methods             ")
    assert(dev.range() == (0x0, 0x320C))
    print("================== PASSED ====================\n")

    print("==============================================")
    print("Test simple registers search / indentification")
    r = AD9546.RegistersByAddress(dev.regmap, 0x3)[0]
    assert(r == AD9546.RegisterAttributes(dev.regmap, "type"))
    print("================== PASSED ====================\n")

    print("==============================================")
    print("Test complex register search / indentification")
    a = AD9546.RegistersByAddress(dev.regmap, 0x4)
    b = AD9546.RegistersByAddress(dev.regmap, 0x5)
    c = AD9546.RegistersByAddress(dev.regmap, 0x6)
    assert(a == b)
    assert(b == c)
    assert(c == a)

    a = AD9546.RegistersByAddress(dev.regmap, 0xC)
    b = AD9546.RegistersByAddress(dev.regmap, 0xD)
    assert(a == b)

    r = AD9546.RegistersByAddress(dev.regmap, 0xB)
    print(r)
    print("================== PASSED ====================\n")

    print("==============================================")
    print("                   Update()                   ")
    dev.update()
    # modify one attribute randomly
    # tests apply()
    dev.apply()
    # testbench
    dev.update()
    print("================== PASSED ====================\n")
    
if __name__ == "__main__":
    main()
