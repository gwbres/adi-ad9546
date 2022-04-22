# ADI-AD9546 

Set of tools to interact & program AD9546,AD9545 integrated circuits, by Analog Devices.

These scripts are not Windows compatible.   

## Install 

```shell
python setup.py install
```

## Dependencies

* python-smbus

Install requirements with

```shell
pip3 install -r requirements.txt
```

## API

* Each application comes with an `-h` help menu.  
Refer to help menu for specific information

## AD9545,46

The two chip share similar functionnalities, except that
AD9546 is more capable than 45.   
Therefore, both can share the following tools, but it is up to the user
to restrict to supported operations, when operating an AD9545.

## Register map profiles

Profiles describe the register map entirely.  
It is possible to create a register map profile using the official A&D graphical tool (`export` feature).  

One can load such a profile (.json format) with the `profile.py` utility.   
`i2c` bus number (integer number) and slave address (hex) must be specified:

```shell
profile.py -h

# loading the AD9546 example profile (on bus #0 @0x48)
profile.py 0 0x48 --load example.json

# loading another profile (on bus #1 0x4A)
profile.py 1 0x4A --load /tmp/map.json
```

A&D graphical interface can load a register map (`import` feature).   
One can dump the current chipset map with 

```shell
profile.py 0 0x55 --dump map.json
profile.py 1 0xAA --dump /tmp/map.json
```

* Disable the progress bar (quiet stdout) with the `--quiet` flag:
```shell
profile.py 0 0x55 --quiet --load map.json
profile.py 1 0xAA --quiet --dump map.json
```

## Status script

`status.py` is a read only tool, to interact with the integrated chip.  
`i2c` bus number (integer number) and slave address (hex) must be specified.

Use the `help` menu to learn how to use this script:
```shell
status.py -h
usage: status.py [-h] 
    [--info]
    [--serial]
    [--sysclk-pll] [--sysclk-comp]
    [--pll] [-pll0] [--pll1]
    [--refa] [-refaa] [--refb] [--refbb] 
    [--irq] 
    [--iuts] 
    [--temp] 
    [--eeprom] 
    [--misc] 
    bus address

Clock status reporting

positional arguments:
  bus           I2C bus
  address       I2C slv address

optional arguments:
  -h, --help    show this help message and exit
  --info         Device general infos (SN#, ..)
  --serial       Serial port status (I2C/SPI)
  --sysclk-pll   Sys clock synthesis pll
  --sysclk-comp  Sys clock compensation
  --pll          Shared Pll global info
  --pll0         Pll0 specific infos
  --pll1         Pll1 specific infos
  --refa         REF-A signal info
  --refaa        REF-AA signal info
  --refb         REF-B signal info
  --refbb        REF-BB signal info
  --irq          IRQ registers
  --iuts         Report IUTS Status
  --temp         Internal temperature sensor
  --eeprom       EEPROM controller status
  --misc         Auxilary NCOs, DPll and Temp info
```

Several part of the integrated chips can be monitored at once.
Output format is `json` and is streamed to `stdout`.
Example of use:

```shell
# Grab general / high level info (bus=0, 0x4A):
status.py --info --serial --pll 0 0x4A

# General clock infos + ref-a status (bus=1, 0x48):
status.py --pll --sysclk-pll --refa 1 0x48

# IRQ status register
status.py --irq 0 0x4A

# dump status to a file
status.py --info --serial --pll 0 0x4A > /tmp/status.json

# call status.py from another python script;
# evaluate json content (dict) directly from `stdout`
import subprocess
args = ['status.py', '--info', '0', '0x4A']
ret = subprocess.run(args)
if ret.exitcode == 0: # OK
   # grab `stdout`
   status = ret.stdout.decode('utf-8') 
   # build structure directly
   status = eval(status)
   status['info']['vendor'] # eval() is way cool!
```

## Calibration script

`calib.py` allows easy & quick chipset (re)calibration.   

It is required to perform a calibration at boot time.  
It is required to perform an analog Pll (re)calibration anytime
we recover from a sys clock power down.

* Perform a sys clock recalibration

```shell
calib.py 0 0x4A --sysclk
```

* Recalibrate Analog Plls

```shell
calib.py 0 0x4A --pll
```

* Perform full recalibration

```shell
calib.py 0 0x4A --sysclk --pll
```

## Reset script

To quickly reset the device

* `--soft` : performs a soft reset
* `--sans` : same thing but maintains current registers value 
* `--watchdog` : resets internal watchdog timer
* `-h` for more infos

## Power down script

`power-down.py` perform and recover power down operations.   
Useful to power down non needed channels and internal cores. 

The `--all` flag addresses all internal cores.  
Otherwise, select internal units with related flag

* Power down device entirely
```shell
power-down.py 0 0x4A --all
```
* Recover a complete power down operation
```shell
power-down.py 0 0x4A --all --clear
```

* Wake `-a` references up and put `-b` reference channels to sleep:
```shell
power-down.py 0 0x4A --refb --refbb --refaa
power-down.py 0 0x4A --clear --refa 
```

## IRQ events

`status.py --irq` allows reading the current asserted IRQ flags.  

Clear them with `irq.py`:

* `--all`: clear all flags
* `--pll`: clear all PLL (PLL0 + PLL1 + digital + analog) related events 
* `--pll0`: clear PLL0 (digital + analog) related events 
* `--pll1`: clear PLL1 (digital + analog) related events 
* `--other`: clear events that are not related to the pll subgroup
* `--sysclk`: clear all sysclock related events 
* `-h`: for other known flags

## Misc

`status.py --temp` returns the internal temperature sensor reading.  
`misc.py` allows programming a temperature alarm threshold:

```shell
misc.py --temp-thres-low=-10 # [°C]
misc.py --temp-thres-high=80 # [°C]
status.py --temp 0 0x48 # current reading [°C] 
```

Warning events are retrieved with the `irq.py` utility, refer to related section.

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
