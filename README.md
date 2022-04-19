# ADI-AD9546 

Set of tools to interact & program AD9546,AD9545 chips by Analog Devices.    

These scripts are not Windows compatible.   

## Install libraries

```shell
python setup.py install
```

## API

* Each application comes with an `-h` help menu

## Profiles & Register map

Profiles entirely describe a chip.   
Profiles can be created using A&D graphical interfaces.

`i2c` bus must be specified with `-b` (integer number).  
Chip slave address on the `i2c` bus must be specified with `--address` or `-a` (hex).  

* Load such a register map

```shell
profile.py -b 0 -a 0x55 --load /tmp/map.json
profile.py -b 1 -a 0xAA -l /tmp/map.json
```

A&D graphical interface can load a register map.

* Dump current settings into compatible format

```shell
profile.py -b 0 -a 0x55 --dump /tmp/map.json
profile.py -b 0 -a 0x55 -d /tmp/map.json
```

## Clock ops

Clock ops perform macro operations, meaning, operations
that are unlocked by A&D kernel drivers official support.    
Therefore, it is expected to use `clock-ops.py` along `ad9545` official driver loaded & deployed
properly.

Determine which operations are available for which clock, 
for a given chipset (does not require a driver access):

```shell
clock_ops.py --list
```

Most operation require a channel to be specified, specify them with `--channel`
or `-n`:
```shell
clock_ops.py --clock=sysclk --channel
```

For each clock, specify a channel with a --channel n integer number

* Enable sys clock
* Enable refclock

This you can do with basic clock operations:
* set up (control, status) the sys clock 
* set up each internal clock, including synthesis process control:
 * clock tree control (parent)
 * instantenous phase control
 * frequency control

Most advanced features are not available to `clock ops`,
you need to move to the `advanced` ops.

## Advanced ops

Examples of advanced usages down below.

### Chipset initialization

Initializes chipset for nominal operation.   
This macro is intended to be called once per configuration (like boot time).  

### Chipset calibration

Calibrates chipset for nominal operation.   
This macro is intended to be called once per session. 

## Chipset status

Returns status in a readable & loadable format

```shell
status.py /tmp/status.json
```
