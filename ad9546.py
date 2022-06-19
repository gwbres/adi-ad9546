#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# AD9546 is the main class to manage and interact with the device 
#################################################################
import math
from smbus import SMBus

def sign_extend (value, length):
    """ sign extends given integer number to desired length """
    binary = bin(value)[2:]
    if binary[0] == '1':
        l = length - len(binary) 
        for i in range(l):
            binary = '1' + binary
        return int(binary,2)
    return value

def single_bit_mask (mask):
    """
    Returns true if given mask has a unique bit asserted
    """
    return bin(mask).count('1') == 1 

def binary_shift (mask):
    """
    Deduces appropriate binary shift for this bitmask
    """
    if mask == 0xFF:
        return 0
    elif single_bit_mask(mask):
        return int(math.log2(mask))
    else:
        return bin(mask).count('0') -1 #'0b'

class Interprator :
    """
    `Complex` data interprator
    """
    def __init__ (self):
        self.__loadtable()

    def interprate (self, fmt, data):
        """
        `complex` data interpratation,
        never fails
        """
        if fmt == "bool":
            return bool(data)
        elif fmt == "int":
            return int(data)
        elif "complex:" in fmt:
            fmt = fmt.split(":")[-1]
            if fmt in self.table:
                return hex(data)
            else:
                return hex(data)
        else:
            return hex(data) 

    def __loadtable (self):
        self.table = {
            "enable": {
                "disabled": 0,
                "enabled": 1,
            },
            "available": {
                "unavailable": 0,
                "available": 1,
            },
            "active": {
                "disabled": 0,
                "active": 1,
            },
            "done": {
                "idle or busy": 0,
                "done": 1,
            },
            "pin": {
                "logics": {
                    "cml": 0,
                    "hcsl": 1,
                },
                "diff-modes": {
                    "AC": 0,
                    "DC": 1,
                    "DC-LVDS": 2,
                },
                "currents": {
                    "7.5 mA": 0,
                    "12.5 mA": 1,
                    "15 mA": 2,
                },
            },
            "modes": {
                "diff": 0,
                "se": 1,
                "sedd": 2,
            },
            "autosync": {
                "manual": 0,
                "immediate": 0,
                "phase": 0,
                "freq": 0,
            },
            "unmutings": {
                "immediate": 0,
                "hitless": 1,
                "phase": 2,
                "freq": 3,
            },
            "couplings": {
                'AC 1.2V': 0,
                'DC 1.2V CMOS': 1,
                'DC 1.8V CMOS': 2,
                'internal pull-up': 3,
            },
            "bandwith" : {
                "narrow": 0,
                "wide": 1,
            },
            'slew-rate-threshold': {
                0: '0',
                1: "0.715 ppm/s",
                2: "1.430 ppm/s",
                3: "2.860 ppm/s",
                4: "5.720 ppm/s",
                5: "11.44 ppm/s",
                6: "22.88 ppm/s",
                7: "45.76 ppm/s",
            },
            'comp-sources': {
                0: 'REFA',
                1: 'REFAA',
                2: 'REFB',
                3: 'REFBB',
                6: 'aux-REF0',
                7: 'aux-REF1',
                11: 'aux-REF2',
                12: 'aux-REF3',
            },
        }

def BuildRegMap():
    """
    Builds memory map descriptor
    """
    return {
        'chip': {
            'type': {
                # reg addr : for HW access
                # might involve several accesses [array] 
                'addr': 0x0003,
                'access': 'ro',
            }, # chip::type
            'code': {
                "addr": [0x0004, 0x0005, 0x0006],
                'access': 'ro',
            }, # chip::code
            'vendor': {
                'addr': [0x0C, 0x0D],
                'access': 'ro',
            }, # chip::vendor
        }, # chip::
        'serial': {
            'soft-reset': {
                'addr': 0x00,
                'format': 'bool',
                'mask': 0x01,
            }, # serial::softreset
            'spi': {
                'version': {
                    'addr': 0x0B,
                    'access': 'ro',
                }, # serial::spi::version
                'lbsf': {
                    'addr': 0x00,
                    'format': 'bool',
                    'mask': 0x02,
                }, # serial::spi::lbsf
                'addr-asc': {
                    'addr': 0x00,
                    'format': 'bool',
                    'mask': 0x04,
                }, # serial::spi::addr-asc
                'sdo': {
                    'addr': 0x00,
                    'format': 'bool',
                    'mask': 0x08,
                }, # serial::spi::sdo
            }, # serial::spi::
            'reset-registers': {
                'addr': 0x01,
                'mask': 0x04,
                'format': 'bool',
            }, # serial::reset-registers
            'buffered-read' : {
                'addr': 0x01,
                'mask': 0x40,
                'format': 'bool',
            }, # seria::bufferedread
        }, # serial::
        'sysclk': {
            'pll': {
                'fb-div-ratio': {
                    'addr': 0x200,
                    'format': 'int',
                },
                'freq-doubler': {
                    'addr': 0x201,
                    'mask': 0x01,
                    'format': 'complex:enabled',
                },
                'input-sel': {
                    'addr': 0x201,
                    'mask': 0x08,
                },
                'input-div': {
                    'addr': 0x201,
                    'mask': 0x06,
                    'format': 'int',
                },
                'ref-freq': {
                    'addr': [0x202, 0x203, 0x204, 0x205, 0x206],
                    'format': 'int',
                    'scaling': 1E3, # *1E3 TODO
                },
                'stability-period': {
                    'addr': [0x207, 0x208, 0x209],
                    'mask': [0xFF, 0xFF, 0x0F],
                    'format': 'int',
                    'scaling': 10E-3 #TODO
                },
            },
            'compensation': {
                'method2-aux-dpll': {
                    'addr': 0x280,
                    'mask': 0x20,
                    'format': 'bool',
                },
                'method1-aux-dpll': {
                    'addr': 0x280,
                    'mask': 0x10,
                    'format': 'bool',
                },
                'method3-tcds': {
                    'addr': 0x280,
                    'mask': 0x04,
                    'format': 'bool',
                },
                'method2-tcds': {
                    'addr': 0x280,
                    'mask': 0x02,
                    'format': 'bool',
                },
                'method1-tcds': {
                    'addr': 0x280,
                    'mask': 0x01,
                    'format': 'bool',
                },
                'method3-aux-nco1': {
                    'addr': 0x281,
                    'mask': 0x40,
                    'format': 'bool',
                },
                'method2-aux-nco1': {
                    'addr': 0x281,
                    'mask': 0x20,
                    'format': 'bool',
                },
                'method1-aux-nco1': {
                    'addr': 0x281,
                    'mask': 0x10,
                    'format': 'bool',
                },
                'method3-aux-nco0': {
                    'addr': 0x281,
                    'mask': 0x04,
                    'format': 'bool',
                },
                'method2-aux-nco0': {
                    'addr': 0x281,
                    'mask': 0x02,
                    'format': 'bool',
                },
                'method1-aux-nco0': {
                    'addr': 0x281,
                    'mask': 0x01,
                    'format': 'bool',
                },
                'method3-dpll1': {
                    'addr': 0x282,
                    'mask': 0x40,
                    'format': 'bool',
                },
                'method2-dpll1': {
                    'addr': 0x282,
                    'mask': 0x20,
                    'format': 'bool',
                },
                'method1-dpll1': {
                    'addr': 0x282,
                    'mask': 0x10,
                    'format': 'bool',
                },
                'method3-dpll0': {
                    'addr': 0x282,
                    'mask': 0x04,
                    'format': 'bool',
                },
                'method2-dpll0': {
                    'addr': 0x282,
                    'mask': 0x02,
                    'format': 'bool',
                },
                'method1-dpll0': {
                    'addr': 0x282,
                    'mask': 0x01,
                    'format': 'bool',
                },
                'slew-rate-limiter': {
                    'threshold': {
                        'addr': 0x0283,
                        'mask': 0x07,
                        'format': 'complex:slew-rate-threshold',
                    },
                },
                'source': {
                    'addr': 0x0284,
                    'format': 'complex:comp-sources',
                    'mask': 0x0F,
                },
                'dpll': {
                    'bandwith': {
                        'addr': [0x285, 0x286],
                        'format': 'int', #/10 #TODO
                    },
                    'selector': {
                        'addr': 0x287,
                        'mask': 0x01,
                        #0 : 'dpll0', 1: "dpll1"
                        'format': 'complex:comp:dpll:selector',
                    },
                },
                "method1-cutoff": {
                    'addr': 0x288,
                    'mask': 0x07,
                    #0: '156 Hz',
                    #1: '78 Hz',
                    #2: '39 Hz',
                    #3: '20 Hz',
                    #4: '10 Hz',
                    #5: '5 Hz',
                    #6: '2 Hz',
                    #7: '1 Hz',
                    'format': 'complex:comp:cutoffs',
                },
                #TODO
                #'method1-coefficients': {
                #addr: 0x289
                #}
            },
            'locked': {
                'addr': 0x3001,
                'mask': 0x01,
                'format': 'bool',
                'access': 'ro',
            },
            'stable': {
                'addr': 0x3001,
                'mask': 0x02,
                'format': 'bool',
                'access': 'ro',
            },
            'calibrating': {
                'addr': 0x3001,
                'mask': 0x04,
                'format': 'bool',
                'access': 'ro',
            },
        }, # sysclk::
        "pll": {
            "ch0": {
                "locked": {
                    "addr": 0x3001,
                    "mask": 0x20,
                    "format": "bool",
                },
                "digital": {
                    "freq-locked": {
                        "format": "bool",
                        "addr": 0x3100,
                        "mask": 0x04,
                    },
                    "phase-locked": {
                        "format": "bool",
                        "addr": 0x3100,
                        "mask": 0x02,
                    },
                    "profile": {
                        "addr": 0x3101,
                        "mask": 0x70,
                    },
                    "active": {
                        "addr": 0x3101,
                        "format": "bool",
                        "mask": 0x08,
                    },
                    "switching-profile": {
                        "addr": 0x3101,
                        "mask": 0x04,
                    },
                    "holdover": {
                        "addr": 0x3101,
                        "mask": 0x02,
                        "format": "bool",
                    },
                    "free-running": {
                        "addr": 0x3101,
                        "mask": 0x01,
                        "format": "bool",
                    },
                    "fast-acquisition": {
                        "format": "complex:done",
                        "addr": 0x3102,
                        "mask": 0x20,
                    },
                    "fast-acquisitionning": {
                        "format": "bool",
                        "addr": 0x3102,
                        "mask": 0x10,
                    },
                    "phase-slew": {
                        "format": "complex:active",
                        "addr": 0x3102,
                        "mask": 0x04,
                    },
                    "freq-campling": {
                        "format": "complex:active",
                        "addr": 0x3102,
                        "mask": 0x02,
                    },
                    "tuning-word-history": {
                        "format": "complex:available",
                        "addr": 0x3102,
                        "mask": 0x01,
                    },
                    "ftw-history": {
                        "format": "int",
                        "addr": [0x3103, 0x3104, 0x3105, 0x3106, 0x3107, 0x3108],
                        "mask": [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x1F],
                    },
                    "phase-lock-tub": {
                        "format": "int",
                        "addr": [0x3109, 0x310A],
                        "mask": [0xFF, 0x0F],
                    },
                    "freq-lock-tub": {
                        "format": "int",
                        "addr": [0x310B, 0x310C],
                        "mask": [0xFF, 0x0F],
                    },
                },
                "analog": {
                    "calibration": {
                        "format": "complex:done",
                        "addr": 0x3100,
                        "mask": 0x20,
                    },
                    "calibrating": {
                        "format": "bool",
                        "addr": 0x3100,
                        "mask": 0x10,
                    },
                    "phase-locked": {
                        "format": "bool",
                        "addr": 0x3100,
                        "mask": 0x08,
                    },
                },
            }, # pll::ch0
            "ch1": {
                "locked": {
                    "addr": 0x3001,
                    "mask": 0x20,
                    "format": "bool",
                },
                "digital": {
                    "freq-locked": {
                        "format": "bool",
                        "addr": 0x3100+0x100,
                        "mask": 0x04,
                    },
                    "phase-locked": {
                        "format": "bool",
                        "addr": 0x3100+0x100,
                        "mask": 0x02,
                    },
                    "profile": {
                        "addr": 0x3101+0x100,
                        "mask": 0x70,
                    },
                    "active": {
                        "addr": 0x3101+0x100,
                        "format": "bool",
                        "mask": 0x08,
                    },
                    "switching-profile": {
                        "addr": 0x3101+0x100,
                        "mask": 0x04,
                    },
                    "holdover": {
                        "addr": 0x3101+0x100,
                        "mask": 0x02,
                        "format": "bool",
                    },
                    "free-running": {
                        "addr": 0x3101+0x100,
                        "mask": 0x01,
                        "format": "bool",
                    },
                    "fast-acquisition": {
                        "format": "complex:done",
                        "addr": 0x3102+0x100,
                        "mask": 0x20,
                    },
                    "fast-acquisitionning": {
                        "format": "bool",
                        "addr": 0x3102+0x100,
                        "mask": 0x10,
                    },
                    "phase-slew": {
                        "format": "complex:active",
                        "addr": 0x3102+0x100,
                        "mask": 0x04,
                    },
                    "freq-campling": {
                        "format": "complex:active",
                        "addr": 0x3102+0x100,
                        "mask": 0x02,
                    },
                    "tuning-word-history": {
                        "format": "complex:available",
                        "addr": 0x3102+0x100,
                        "mask": 0x01,
                    },
                    "ftw-history": {
                        "format": "int",
                        "addr": [0x3203, 0x3204, 0x3205, 0x3206, 0x3207, 0x3208],
                        "mask": [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x1F],
                    },
                    "phase-lock-tub": {
                        "format": "int",
                        "addr": [0x3209, 0x320A],
                        "mask": [0xFF, 0x0F],
                    },
                    "freq-lock-tub": {
                        "format": "int",
                        "addr": [0x320B, 0x320C],
                        "mask": [0xFF, 0x0F],
                    },
                },
                "analog": {
                    "calibration": {
                        "format": "complex:done",
                        "addr": 0x3100,
                        "mask": 0x20,
                    },
                    "calibrating": {
                        "format": "bool",
                        "addr": 0x3100,
                        "mask": 0x10,
                    },
                    "phase-locked": {
                        "format": "bool",
                        "addr": 0x3100,
                        "mask": 0x08,
                    },
                },
            }, # pll::ch1
        }, # pll::
        "eeprom": {
            "crc-fault": {
                "addr": 0x3000,
                "format": "bool",
                "mask": 0x08,
            }, # eeprom::crc-fault
            "fault": {
                "addr": 0x3000,
                "mask": 0x04,
                "format": "bool",
            }, # eeprom::fault
            "busy": {
                "downloading": {
                    "addr": 0x3000,
                    "format": "bool",
                    "mask": 0x02,
                }, # eeprom::busy::downloading
                "uploading": {
                    "addr": 0x3000,
                    "format": "bool",
                    "mask": 0x01,
                } # eeprom::busy::uploading
            }, # eeprom::busy
        }, # eeprom::
    }

class AD9546 :
    """ 
    AD9546 chipset manager
    """
    def __init__ (self, bus, address=None):
        """ 
        Creates an AD9546 device manager, 
        bus: supports 3 options
            * `/dev/i2c-x`: for I2C device
            * `/dev/spidev-x.y`: for SPI device
            * `fake`: emulates HW access, for testing purpopses
        
        address: I2C slave address, expected
        when /dev/i2c-x entry is provided
        """
        self.loadRegMap() # internal register descriptor
        self.interprator = Interprator() # data interprator
        self.__make_handle(bus, address=address) # H/W access handle

    def RegisterAttributes (mmap, reg):
        """
        Returns attributes by searching through register map
        """
        for key in mmap.keys():
            if "addr" in mmap[key]:
                if key == reg:
                    return mmap[key]
            else:
                v = AD9546.RegisterAttributes(mmap[key], reg)
                if v is not None:
                    return v
        return None

    def RegistersByAddress (mmap, addr):
        """
        Returns list of registers refering to given address
        """
        result = []
        for key in mmap.keys():
            if "addr" in mmap[key]:
                a = mmap[key]["addr"]
                if type(a) is int:
                    a = [a,]
                if addr in a:
                    result.append(mmap[key])
            else:
                found = AD9546.RegistersByAddress(mmap[key], addr)
                if len(found) > 0:
                    for item in found:
                        result.append(item)
        return result
    
    def __make_handle (self, bus, address=None):
        """
        Creates handle for bus communication,
        TODO: manage SPI case
        """
        self.bus = bus
        if bus.startswith("/dev/i2c"):
            self.handle = SMBus()
            self.slave_addr = address
        elif bus.startswith("/dev/spi"):
            raise ValueError("spi handle not managed yet")
        elif bus != "fake":
            raise ValueError("non recognized handle descriptor")

    def __str__ (self):
        """
        Exposes readable regmap
        """
        return str(self.regmap)

    def min (self, mmap=None):
        """
        Returns smallest address in table
        """
        mmap = self.regmap if mmap is None else mmap
        m = 0xFFFFF
        for key in mmap.keys():
            if "addr" in mmap[key]:
                a = mmap[key]["addr"]
                for _a in a:
                    if _a < m:
                        m = _a
            else:
                a = self.min(mmap=mmap[key])
                if a < m:
                    m = a
        return m

    def max (self, mmap=None):
        """
        Returns largest address in table
        """
        mmap = self.regmap if mmap is None else mmap
        m = 0
        for key in mmap.keys():
            if "addr" in mmap[key]:
                a = mmap[key]["addr"]
                for _a in a:
                    if _a > m:
                        m = _a
            else:
                a = self.max(mmap=mmap[key])
                if a > m:
                    m = a
        return m

    def range (self):
        """
        Returns regmap range, for convenient address
        interation
        """
        return (self.min(), self.max())

    def __iter__ (self):
        """
        Provides convenient interator over self.regmap
        """
        self.pos = 0
        return iter(list(self.regmap))
    def __next__ (self):
        raise StopIteration

    def __getitem__ (self, reg):
        return self.regmap[reg]

    def uses_i2c (self):
        """
        Returns true if we're setup for I2C comm
        """
        return type(self.handle) is SMBus
    
    def __is_fake (self):
        """
        Returns true if HW access is emulated
        """
        return self.bus == "fake"

    def open (self):
        """
        Opens device for Rd/Wr operations
        TODO: manage SPI case
        """
        if not self.__is_fake():
            if self.uses_i2c():
                self.handle.open(self.bus)

    def close (self):
        """
        Closes supposedly opened device
        TODO: manage SPI case
        """
        if not self.__is_fake():
            self.handle.close()
    
    def loadRegMap (self):
        """
        Builds internal regmap,
        to be later used when addressing device
        """
        mmap = BuildRegMap()
        self.regmap = self.rework_table(mmap)
    
    def rework_table (self, table):
        """
        recursively reworks declared table where
        fields might be ommitted
        """
        rework = table.copy()
        for key in table.keys():
            if "addr" in table[key]:
                if not "access" in table[key]:
                    rework[key]["access"] = "rw"

                if not type(table[key]["addr"]) is list:
                    rework[key]["addr"] = [table[key]["addr"],]

                l = len(rework[key]["addr"])
                if not "mask" in table[key]:
                    rework[key]["mask"] = []
                    for _ in range(0, l):
                        rework[key]["mask"].append(0xFF)
                else:
                    if not type(rework[key]["mask"]) is list:
                        rework[key]["mask"] = [table[key]["mask"],]
                        for _ in range(1, l):
                            rework[key]["mask"].append(0xFF)
                
                if not "format" in table[key]:
                    rework[key]["format"] = 'hex'
            else:
                rework[key] = self.rework_table(table[key])
        return rework

    def write_byte (self, addr, data):
        """ 
        Writes data (uint8_t) to given address (uint16_t)
        TODO: manage SPI low level case
        """
        msb = (addr & 0xFF00)>>8
        lsb = addr & 0xFF
        if self.uses_i2c():
            self.handle.write_i2c_block_data(self.slv_addr, msb, [lsb, data & 0xFF])

    def read_byte (self, addr):
        """ 
        Reads data (uint8_t) at given address (uint16_t) 
        TODO: manage SPI low level case
        """
        msb = (addr & 0xFF00)>>8
        lsb = addr & 0xFF
        if self.__is_fake():
            import random
            return random.randint(0, 255)
        else:
            if self.uses_i2c():
                self.handle.write_i2c_block_data(self.slv_addr, msb, [lsb])
                data = self.handle.read_byte(self.slv_addr)
            return data

    def update (self):
        """
        Reads all known registers to current value
        """
        (r0, end) = self.range()
        for addr in range(r0, end): # over entire mmap
            # registers for this address
            regs = AD9546.RegistersByAddress(self.regmap, addr)
            if len(regs) == 0: # unused address
                continue # avoids reading: increases update speed
            raw = self.read_byte(addr)
            print("raw: ", hex(raw))
            for reg in regs:
                if len(reg["addr"]) == 1: 
                    # this reg only involves this addr
                    mask = reg["mask"][0]
                    shift = binary_shift(mask)
                    data = (raw & mask) >> shift 
                    d = self.interprator.interprate(
                        reg["format"],
                        data)
                    print("addr:", hex(addr), "mask:", hex(mask), "shift:", shift, "data:", d)

    def apply (self):
        """
        Applies all register values
        """
        pass
    
    def io_update (self):
        """ 
        Performs special `I/O update` operation. 
        Refer to device datasheet 
        """
        self.write_data(0x000F, 0x01)
    
    def calibrate (self, sysclk=True, all=True):
        """
        Reruns a device calibration
        """
        # reset reg
        self.write_data(0x2000, 0x00)
        self.io_update()
        # assign bits
        v = 0
        if sysclk:
            value |= 0x04
        if all:
            value |= 0x02
        self.write_data(0x2000, value)
        self.io_update()
        # clear bits
        if sysclk:
            value &= 0xFB
        if all:
            value &= 0xFD
        self.write_data(0x2000, value)
        self.io_update()
