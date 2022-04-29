# ADI-AD9546 

[![Python application](https://github.com/gwbres/adi-ad9546/actions/workflows/python-app.yml/badge.svg)](https://github.com/gwbres/adi-ad9546/actions/workflows/python-app.yml)

Set of tools to interact & program AD9546/45 integrated circuits, by Analog Devices.

Use [these tools](https://github.com/gwbres/adi-ad9548)
to interact with AD9548/47 older chipsets.

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
* `flag` is a mandatory flag
* `--flag` is optionnal: action will not be performed if not requested

## AD9545,46

The two chip share similar functionnalities, except that
AD9546 is more capable than 45.   
Therefore, both can share the following tools, but it is up to the user
to restrict to supported operations, when operating an AD9545.

## Utilities

* `calib.py`: calibrates core portions of the clock. Typically required
when booting or a new setup has just been loaded.
* `distrib.py`: controls clock distribution and output signals
* `misc.py`: miscellaneous / optionnal stuff
* `power-down.py` : power saving and management utility, turns core sections on and off.
* `ref-input.py`: controls clock input signals 
* `regmap.py`: load or dump a register map preset
* `reset.py`: reset the device
* `status.py` : status monitoring, includes IRQ flag reports and onboard temperature reading

See at the bottom of this page for typical configuration flows.

## Register map

`regmap.py` allows the user to quickly load an exported
register map from the official A&D graphical tool.
* Supported format is `json`
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
```

There is basically a `--flag` option (reader) for pretty much all
custom scripts (writer) down below, to readback related values.

Several part of the integrated chips can be monitored at once.
Output format is `json` and is streamed to `stdout`.
Example of use:

```shell
# Grab general / high level info (bus=0, 0x4A):
status.py --info --serial --pll 0 0x4A

# General clock infos + ref-input status (bus=1, 0x48):
status.py --info --pll --sysclk --ref-input 1 0x48

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

Status (depending on sections of interest) is quiet verbose.   
To reduce the quantity of information displayed, one can use the two availlable filters:

* `--filter-by-key`: filters result by keyword identifiers.
Identifiers are passed as comma separated strings.
Filters only retain data that match the specified identifiers exactly
(case sensitive).

```shell
# Clock infos filter
status.py --info --filter-by-key vendor 0 0x48
```

It is possible to cummulate filters using comma separated description

```shell
# Retain two infos
status.py --info --filter-by-key chip-type,vendor 0 0x48

# Clock distribution status: focus on channel 0
status.py --distrib --filter-by-key ch0 0 0x48

# Retain only `a` and `b` paths among channel0
status.py --distrib --filter-by-key ch0,a,b 0 0x48
```

By default, if requested keyword is not found,
filter op is considered faulty and fulldata set is exposed.

```shell
# trying to filter general infos
status.py --info --filter-by-key something 0 0x48
```

As always, flag order does not matter.
It is possible to filter several status reports with
relevant keywords:

```shell
# Request clock distribution status report
# and ref-input status report
# -> restrict distribution status report to `ch0`  
# --> --ref-input status is untouched because it does not contain the `ch0` identifier
status.py --distrib --ref-input filter-by-key ch0 0 0x48

# Same thing idea, but we apply a filter on seperate status reports
# `ch1` only applies to `distrib`, `slow` only applies to `ref-input`
status.py --distrib --ref-input --filter-by-key ch1,slow 0 0x48
```

* `filter-by-value`: it is possible to filter status reports
on matching values too. Once again, only exactly matching keywords
are retained.

```shell
# Return `0x456` <=> vendor field
status.py --info --filter-by-value 0x456 1 0x48

# Return only deasserted values
status.py --distrib --filter-by-value disabled 1 0x48

# Optimum `deasserted` value filter, 
# using cummulated filter
status.py --distrib --filter-by-value disabled,false,inactive 1 0x48
```

It is possible to combine `key` and `value` restrictions:

```shell
# todo  
```

## Sys clock

`Sys` clock compensation is a new feature introduced in AD9546.
`sysclock.py` allows quick and easy access to these features.

To determine current `sysclock` related settings, use status.py with `--sysclock` option.

* `--freq`: to program input frequency [Hz]
* `--sel` : to select the input path (internal crystal or external XOA/B pins)
* `--div`: set integer division ratio on input frequency
* `--doubler`: enables input doubler

## Calibration script

`calib.py` allows chipset (re)calibration.   

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

* `--channel` (optionnal) describes which targetted channel.
Defaults to `all`, meaning if `--channel` is not specified, both channels (CH0/CH1)
are assigned the same value.
This script only suppports a single `--channel` assignment.

* `--path` (optionnal) describes desired signal path. 
Defaults to `all` meaning, all paths are assigned the same value (if feasible).  
This script only suppports a single `--path` assignment at a time.  
Refer to help menu for list of accepted values.

* `--pin` (optionnal) describes desired pin, when controlling an output pin.
Defaults to `all` meaning, all pins (+ and -) are assigned the same value when feasible.  
Refer to help menu for list of accepted values.

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

`ref-input.py` to control the reference input signal,
signal quality constraints, switching mechanisms 
and the general clock state.

* `--freq` set REFxy input frequency [Hz]
* `--coupling` control REFx input coupling
* `--free-run` force clock to move to free-run state
* `--holdover` force clock to move to holdover state,
`lock` must be previously acquired.

It is easier to always request a `free-run`, in the sense this
request cannot fail

* `freq-lock-thresh` : frequency locking mechanism constraint.
* `phase-lock-thresh` : phase locking mechanism constraint.
* `phase-step-thresh` : inst. phase step threshold 
* `phase-skew`: phase skew

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
