# ADI-AD9546 

[![Python application](https://github.com/gwbres/adi-ad9546/actions/workflows/python-app.yml/badge.svg)](https://github.com/gwbres/adi-ad9546/actions/workflows/python-app.yml)

Set of tools to interact & program AD9546,AD9545 integrated circuits, by Analog Devices.

Use these tools to interact with older chipsets [AD9548/47](https://github.com/gwbres/adi-ad9548)

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
Refer to help menu for specific information. 
* Flags order does not matter
* `flag` is mandatory
* `--flag` describe an optionnal flag, action will not be performed if not passed

## AD9545,46

The two chip share similar functionnalities, except that
AD9546 is more capable than 45.   
Therefore, both can share the following tools, but it is up to the user
to restrict to supported operations, when operating an AD9545.

## Utilities

* `calib.py`: is critical, calibrates clock and internal synthesizers. 
Action required depending on previous user actions and current settings. 
* `distrib.py`: is critical, controls clock distribution and output signals
* `misc.py`: miscellaneous / optionnal stuff
* `power-down.py` : power saving and management utility
* `regmap.py`: load / dump a register map preset
* `reset.py`: to quickly reset the device
* `status.py` : general status monitoring, including on board temperature,
sensors and IRQ flags

## Register map

`regmap.py` allows the user to quickly load an exported
register map from the official A&D graphical tool.
* Support format is `json`.
* `i2c` bus must be specified
* `i2c slave address` must be specified

```shell
regmap.py -h
# load a register map (on bus #0 @0x48)
regmap.py 0 0x48 --load test.json
```

Export current register map to open it in A&D graphical tools:
```shell
regmap.py --dump /tmp/output.json 0 0x48
```

* Use `--quiet` in both cases to disable the progress bar

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

* Perform complete (re)calibration

```shell
calib.py --all 0 0x4A
```

* Perform only a sys clock (re)calibration
(1st step in application note)

```shell
calib.py --sysclk 0 0x4A
```

## Clock distribution

`distrib.py` is an important utility.   
It helps configure the clock path, control output signals
and their behavior.  
To determine the chipset current configuration related to clock distribution,
one should use the status script with `--distrib` option.

Control flags:

* `--channel`: (optionnal) describes which channel we are targetting.
Defaults to `all`, meaning if `--channel` is not specified, both channels (CH0/CH1)
are assigned the same value.
This script only suppports a single `--channel` assignment.

* `--pin`: (optionnal) describes which pin (A/B) is targetted.
Defaults to `all` meaning, both A, B, (and AA,BB,C,CC when feasible) are assigned the same value.
This script only suppports a single `--pin` assignment. Therefore, one must call
this script several times to control several pins.

Action flags: the script supports as many `action` flags as desired, see the list down below.

* `--mode` set OUTxy output pin as single ended or differential
* `--format` sets OUTxy current sink/source format
* `--current` sets OUTxy pin output current [mA], where x = channel
```shell
# set channel 0 as HCSL default format
distrib.py --format hcsl --channel 0
# set channel 1 as CML format
distrib.py --format hcsl --channel 1
# set channel 0+1 as HCSL default format
distrib.py --format hcsl

# set Q0A, Q0B as differntial output
distrib.py --mode diff --channel 0

# set Q1A, as single ended pin
distrib.py --mode se --channel 1 --pin a

# set Q0A Q0B to output 12.5 mA, default output current
distrib.py --current 12.5 --channel 0
# set Q1A to output 7.5 mA, minimal current
distrib.py --current 7.5 --channel 1 --pin a
```

* `--sync-all`: sends a SYNC order to all distribution dividers.
It is required to run a `sync-all` in case the current output behavior
is not set to `immediate`.

```shell
# send a SYNC all
# SYNC all is required depending on previous actions and current configuration
distrib.py --sync-all 0 0x48
```

* `--autosync` : control given channel so called "autosync" behavior.

```shell
# set both Pll CH0 & CH1 to "immediate" behavior
distrib.py --autosync immediate 0 0x48

# set both Pll CH0 to "immediate" behavior
distrib.py --autosync immediate --channel 0 0 0x48

#  and Pll CH1 to "manual" behavior
distrib.py --autosync manual --channel 1 0 0x48
```

In the previous example, CH1 is set to manual behavior.  
One must either perform a `sync-all` operation,
a `q-sync` operation on channel 1,
or an Mx-pin operation with dedicated script, to enable this output signal.

* `--q-sync` : initializes a Qxy Divider synchronization sequence manually. 
When x is the `channel` and `y` is the desired pin.
```shell
# triggers Q0A Q0B Q1A Q1B SYNC 
distrib.py --q-sync 0 0x48

# triggers Q0A Q0B SYNC 
distrib.py --q-sync --channel 0 0 0x48

# triggers Q0B Q1B SYNC 
distrib.py --q-sync --pin b 0 0x48
```

* `--unmute` : controls QXY unmuting opmode,
where x is the `channel` and `y` the desired pin.
```shell
# Q0A Q0B + Q1A Q1B `immediate` unmuting 
distrib.py --unmute immediate 0 0x48

# Q0A Q1A `phase locked` unmuting 
distrib.py --unmute phase --pin a 0 0x48

# Q0B Q1B `freq locked` unmuting 
distrib.py --unmute freq --pin b 0 0x48

# Q0A + Q1B `immediate` unmuting 
distrib.py --unmute immediate --pin a 0 0x48
distrib.py --unmute immediate --pin b 0 0x48
```

* `--pwm-enable` and `--pwm-disable`: constrols PWM modulator
for OUTxy where x is the `channel` and `y` the desired pin.

* `--divider` : control integer division ratio at
QXY pin, where 

```shell
# Q0A,AA,B,BB,C,CC + Q1A,AA,B,BB R=48 division ratio
distrib.py --divider 48 0 0x48

# Q1A,AA,B,BB R=64 division ratio
distrib.py --divider 64 --channel 1 0 0x48

# Q0A & Q0B R=23 division ratio
distrib.py --divider 23 --channel 0 --pin a 0 0x48
distrib.py --divider 23 --channel 0 --pin b 0 0x48
```

* `--phase-offset` applies an instantaneous phase offset
to selected channel + pin.
Maximal value is 2\*D-1 where D is previous `--divider` ratio
for given channel + pin.

```shell
# Apply Q0A,AA,B,BB,C,CC + Q1A,AA,B,BB 

```

## Reset script

To quickly reset the device

* `--soft` : performs a soft reset
* `--sans` : same thing but maintains current registers value 
* `--watchdog` : resets internal watchdog timer
* `-h` for more infos

## Ref input script

`ref_input.py` to control the reference input signal,
signal quality constraints, switching mechanisms 
and the general clock state.


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

* Wake `A` reference up and put `AA,B,BB` references to sleep:
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

* Program a temperature range :

```shell
misc.py --temp-thres-low -10 # [°C]
misc.py --temp-thres-high 80 # [°C]
misc.py --temp-thres-low -30 --temp-thres-high 90
status.py --temp 0 0x48 # current reading [°C] 
```

Related warning events are then retrieved with the `irq.py` utility, refer to related section.
