#! /usr/bin/env python3
from ad9546 import *

def read_registers (device, regmap): 
    for key in regmap:
        print(regmap[key])
        if type(regmap[key]) is dict: 
            continue
        #    r = dev.read_reg(regmap[key])
        #    print("{} - {}".format(key, r))
        else:
            read_registers(device, regmap[key])

def main ():
    dev = AD9546("fake", 0)
    print(dev.regmap)
    # read all registers
    read_registers(dev, dev.regmap)

    # tests apply()
    dev.apply()
    
    # tests update()
    dev.update()

if __name__ == "__main__":
    main()
