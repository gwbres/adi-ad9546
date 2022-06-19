#! /usr/bin/env python3
from ad9546 import *

def main ():
    dev = AD9546("fake")

    # regmap maccros testbench
    # [1] unique register (simple)
    #     search by address & regname produces same result
    print("==============================================")
    print("Test simple registers search / indentification")
    r = AD9546.RegistersByAddress(dev.regmap, 0x3)[0]
    assert(r == AD9546.RegisterAttributes(dev.regmap, "type"))
    r = AD9546.RegistersByAddress(dev.regmap, 0xB)[0]
    assert(r == AD9546.RegisterAttributes(dev.regmap, "soft-reset"))
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
    print("================== PASSED ====================\n")

    # tests update()
    dev.update()
    
    # modify one attribute randomly
    # tests apply()
    dev.apply()

    # testbench
    dev.update()
    
if __name__ == "__main__":
    main()
