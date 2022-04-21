# ADI-AD9546 

Set of tools to interact & program AD9546,AD9545 integrated circuits, by Analog Devices.

These scripts are not Windows compatible.   

## Install libraries

```shell
python setup.py install
```

## API

* Each application comes with an `-h` help menu

## AD9545,46

The two chip share similar functionnalities, except that
AD9546 is more capable than 45.   
Therefore, both can share the following tools, but it is up to the user
to access the proper restricted register, when using against an AD9545 chip.

## Profiles & Register map

Profiles entirely describe the register map.
Profiles can be created with A&D official graphical interfaces (`->export`).

One can load such a profile (.json file) with the `profile.py` utility.   
`i2c` bus number (integer number) and slave address (hex) must be specified. 

```shell
profile.py -h

# loading the AD9546 example profile (on bus #0 @0x48)
profile.py 0 0x48 --load example.json

# loading another profile (on bus #1 0x4A)
profile.py 1 0x4A -l /tmp/map.json
```

A&D graphical interface can load a register map (`->import`).   
One can dump the current chipset content with 

```shell
profile.py 0 0x55 --dump /tmp/map.json
profile.py 0 0xAA -d /tmp/map.json
```

## Status script

`status.py` is a read only tool, to interact with the integrated chip.  
`i2c` bus number (integer number) and slave address (hex) must be specified.

Use the `help` menu to learn how to use this script:
```shell
status.py -h
```

Several part of the integrated chips can be monitored at once.
Output format is `json` and is streamed to `stdout`.
Example of use:

```shell
# Grab general / high level info (bus=0, 0x4A):
status.py -info -serial -pll 0 0x4A
# General clock info + ref-a is used (bus=1, 0x48):
status.py -pll -sysclk-pll -refa 1 0x48
# IRQ status register
status.py -irq 0 0x4A

# dump status to a file
status.py -info -serial -pll 0 0x4A > /tmp/status.json

# call status.py from another python script;
# evaluate json content (dict) directly from `stdout`
import subprocess
args = ['status.py', '-info', '0', '0x4A']
ret = subprocess.run(args)
if ret.exitcode == 0: # OK
   # grab `stdout`
   status = ret.stdout.decode('utf-8') 
   # build structure directly
   status = eval(status)
   status['info']['vendor'] # eval() is way cool!
```

## Clock ops

Clock ops perform macro operations, meaning, operations
that are unlocked by A&D kernel drivers official support.    
Therefore, it is expected to use `clock-ops.py` along `ad9545` official driver loaded & deployed
properly.

Determine which operations are available for which clock:

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
