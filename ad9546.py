#################################################################
# Guillaume W. Bres, 2022          <guillaume.bressaix@gmail.com>
#################################################################
# Class and macros to interact with AD9546 chipsets
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

def binary_shift (mask):
    """
    Deduces appropriate binary shift for this bitmask
    """
    return int(math.log2(mask))

def BuildRegMap():
    """
    Builds memory map descriptor
    """
    return {
        'chip': [{
            'type': {
                # cast(), when interprating this register's data
                # hex() is default value and can be omitted
                'cast': hex, 
                # reg addr : for HW access
                # might involve several accesses [array] 
                'addr': 0x0003,
                # to store current value
                'value': None,
            }, # chip::type
            'code': {
                "addr": [0x0004, 0x0005, 0x0006],
                'value': None,
            }, # chip::code
            'vendor': {
                'addr': [0x0C, 0x0D],
                'value': None,
            }, # chip::vendor
        }], # chip::
        'serial': [{
            'soft-reset': {
                'cast': bool,
                'addr': 0x0B,
                'mask': 0x01,
                'value': None,
            }, # serial::softreset
            'spi': [{
                'version': {
                    'addr': 0x0B,
                    'value': None,
                }, # serial::spi::version
                'lbsf': {
                    'cast': bool,
                    'addr': 0x0B,
                    'mask': 0x02,
                    'value': None,
                }, # serial::spi::lbsf
                'addr-asc': {
                    'cast': bool,
                    'addr': 0x0B,
                    'mask': 0x04,
                    'value': None,
                }, # serial::spi::addr-asc
                'sdo': {
                    'cast': bool,
                    'addr': 0x0B,
                    'mask': 0x08,
                    'value': None,
                }, # serial::spi::sdo
            }],
        }], # serial::
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
        when provided a /dev/i2c-x entry
        """
        self.loadRegMap()
        # creates bus handle
        self.__handle(bus, address=address)

    def __handle (self, bus, address=None):
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
    
    def __fake (self):
        """
        Returns true if HW access is emulated
        """
        return self.bus == "fake"

    def open (self):
        """
        Opens device for Rd/Wr operations
        TODO: manage SPI case
        """
        if not self.__fake():
            if self.uses_i2c():
                self.handle.open(self.bus)

    def close (self):
        """
        Closes supposedly opened device
        TODO: manage SPI case
        """
        if not self.__fake():
            self.handle.close()
    
    def loadRegMap (self):
        """
        Builds internal regmap,
        to be later used when addressing device
        """
        self.regmap = BuildRegMap()

    def __write_data (self, addr, data):
        """ 
        Writes data (uint8_t) to given address (uint16_t)
        TODO: manage SPI low level case
        """
        msb = (addr & 0xFF00)>>8
        lsb = addr & 0xFF
        if self.uses_i2c():
            self.handle.write_i2c_block_data(self.slv_addr, msb, [lsb, data & 0xFF])

    def __read_data (self, addr):
        """ 
        Reads data (uint8_t) at given address (uint16_t) 
        TODO: manage SPI low level case
        """
        msb = (addr & 0xFF00)>>8
        lsb = addr & 0xFF
        if self.__fake():
            import random
            return random.randint(0, 255)
        else:
            if self.uses_i2c():
                self.handle.write_i2c_block_data(self.slv_addr, msb, [lsb])
                data = self.handle.read_byte(self.slv_addr)
            return data

    def io_update (self):
        """ 
        Performs `I/O update` operation. 
        Refer to device datasheet 
        """
        self.write_data(0x000F, 0x01)
    
    def read_reg (self, reg):
        """
        Reads given reg from regmap
        """
        reg = reg.split(":")
        if len(reg) == 2:
            (category, reg) = (reg[0],reg[1])
            pointer = self.regmap[category][reg]
        else:
            (category, reg) = (reg[0],reg[1])
            pointer = self.regmap[category][reg]
        
        addr = self.regmap[category][reg]["addr"]
        if type(addr) is int:
            addr = [addr,] # permits simplified declaration
        # bit masking
        masks = None
        if "mask" in self.regmap[category][reg]:
            masks = self.regmap[category][reg]["mask"]
            if type(masks) is int:
                masks = [masks,]
        # interpretation
        if "cast" in self.regmap[category][reg]:
            cast = self.regmap[category][reg]["cast"]
        else:
            cast = hex # default cast()

        data = 0
        for i in range (0, len(addr)):
            raw = self.__read_data(addr[i])
            if masks is not None:
                raw &= masks[i]
            data |= raw << (8*i)
        return cast(data)

    def update (self):
        """
        Reads all known register
        """
        pass

    def apply (self):
        """
        Applies all register values
        """
        pass
