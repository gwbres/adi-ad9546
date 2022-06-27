# ADI-AD9546 

[![Python application](https://github.com/gwbres/adi-ad9546/actions/workflows/python-app.yml/badge.svg)](https://github.com/gwbres/adi-ad9546/actions/workflows/python-app.yml)
[![PyPI version](https://badge.fury.io/py/adi-ad9546.svg)](http://badge.fury.io/py/adi-ad9546)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/adi-ad9546)

Set of tools to interact & program AD9546/45 integrated circuits, by Analog Devices.

Use [these tools](https://github.com/gwbres/adi-ad9548)
to interact with AD9548/47 older chipsets.

These scripts are not Windows compatible.   
These scripts expect a `/dev/i2c-X` entry, they do not manage the device
through SPI at the moment.

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
* `i2c` bus must always be specified
* `i2c` slave address must always be specified 
* `--flag` is optionnal: action will not be performed if not requested

For complex flag values (basically involving white spaces), for example 
`ref-input --coupling`, don't forget to encapsulate with inverted commas:

```shell
ref-input.py \
    0 0x48 \ # bus #0 slave address is 0x48
    --ref a \ # simple, one word
    --coupling "AC 1.2V" # 'complex' but meaningful value
ref-input.py \
    1 0x4A  \ # bus #1 slave address is 0x4A
    --ref aa \ # simple, one word
    --coupling "internal pull-up" # 'complex' but meaningful value
```

Flag values are case sensitive and must be exactly matched.
It is not possible to pass a non supported / unknown flag value,
scripts will reject those with a runtime error.

## AD9545 / 46

These scripts are developped and tested with an AD9546 chip.   
AD9545 is pin & register compatible, so it should work.   
It is up to the user to restrain to restricted operations in that scenario.

## Utilities

* `calib.py`: calibrates core portions of the clock. Typically required
when booting or a new setup has just been loaded.
* `distrib.py`: controls clock distribution and output signals.
Includes signal paths and output pins muting operations.
* `irq.py`: IRQ clearing & masking operations 
* `misc.py`: miscellaneous operations
* `mx-pin.py`: Mx programmable I/O management 
* `pll.py`: APLLx and DPLLx cores management. Includes
free running + holdover manual forcing operation
* `power-down.py` : power saving and management utility
* `ref-input.py`: reference & input signals management
* `regmap.py`: load or dump a register map preset
* `regmap-diff.py`: loaded / dumped regmap differentiator (debug tool)
* `reset.py`: device reset operations
* `status.py` : status monitoring, includes IRQ flag reports and onboard temperature reading
* `sysclk.py` : sys clock control & management tool

See at the bottom of this page for typical configuration flows.

## Register map

`regmap.py` allows the user to quickly load an exported
register map from the official A&D graphical tool.
* Input/output is `json`
* `--quiet` to disable the stdout progress bar

```shell
regmap.py -h
# load a register map (on bus #0 @0x48)
regmap.py 0 0x48 --load test.json
```

Export current register map to open it in A&D graphical tools:
```shell
regmap.py --dump /tmp/output.json 0 0x48
```

### Register map `diff`

It is possible to use the `regmap-diff.py` tool
to differentiate (bitwise) an official A&D registermap (created with their GUI)
and a dumped one (`--dumped` with regmap.py).

```shell
# order is always: 
#  1) official (from A&D GUi) 
#  2) then dumped file
regmap-diff.py official_ad.json /tmp/output.json
```

This script is mainly used for debugging purposes.

It is equivalent to a `diff -q -Z official_ad.json /tmp/output.json`
focused on the "RegisterMap" field.
That command being impossible to use, because --dump
does not replicate 100% of the official A&D file content (too complex),
and is not focused on the "RegisterMap" field.

## Status script

`status.py` is a read only tool to monitor the chipset status current status.
That includes IRQ status reports, calibration reports, integrated
sensors and measurement readings..

* `status.py -h` to figure all known keys

Output format is `json` and is streamed to `stdout`.
Each `--flag` can be cumulated which increases the status report size/verbosity:

```shell
# Grab general / high level info (bus=0, 0x4A):
status.py 0 0x4A \
    --info --serial # general info \
    --pll # pll core (timing general info)

status.py 1 0x48 \
    --info \
    --pll --sysclk # timing cores info \
    --ref-input # input / ref. signals info

status.py 0 0x4A \
    --irq # IRQ status register 
```

Dump status report from stdout into a file

```shell
status.py --info --serial --pll 0 0x4A > /tmp/status.json
```

Output is a `json` structure. That means it can be directly
interprated into another python script. Here's an example
on how to do that:

```shell
import subprocess
args = ['status.py', '--distrib', '0', '0x4A']
# interprate filtered stdout content directly
ret = subprocess.run(args)
if ret.exitcode == 0: # syscall OK
    # direct interpratation
    struct = eval(ret.stdout.decode('utf-8'))
    print(struct["distrib"]["ch0"]["a"]["q-div"])
```

Status report depicts a lot of information depending
on the targeted internal cores. Status.py supports
filtering operations, we we'll later describe how
an efficient filter can make things easier when
grabbing data from another script

### Status report filtering

Filters are described by comma separated values.
It is possible to cummulate filter of the same kind
and of different kind. Filters are applied in
order of appearance / description.
Identifier filter is applied priori Value filter.

* `--filter-by-key`: filters result by identification keyword.
This is useful to retain fields of interests

```shell
# grab vendor field
status.py 0 0x48 \
    --info --filter-by-key vendor # single field filter

# zoom in on temperature info
status.py 0 0x48 \
    --misc --filter-by-key temperature # single field filter

# only care about CH0
status.py 0 0x48 \
    --distrib --filter-by-key ch0 # single field filter

# only care about AA path(s) 
# [CH0:AA ; CH1:AA] in this case
status.py 0 0x48 \
    --distrib --filter-by-key aa # single field filter
```

Example of cummulated filters:

```shell
# grab (vendor + chiptype) fields
status.py 0 0x48 \
    --info --filter-by-key chip-type,vendor # comma separated

# zoom in on temperature reading
status.py 0 0x48 \
    --misc --filter-by-key temperature,value # zoom in 

# Retain `aa` path from CH0
# Filter by order of appearance, 
# specifying CH0 then AA ;)
status.py 0 0x48 \
    --distrib --filter-by-key ch0,aa
```

By default, if requested keyword is not found (non effective filter),
fulldata set is preserved.

```shell
# non effective filter example:
status.py --info --filter-by-key something 0 0x48
```

* `filter-by-value`: it is possible to filter status reports
by matching values

```shell
# Return `0x456` <=> vendor field
status.py 1 0x48 \
    --info \
    --filter-by-value 0x456

# Return only deasserted values
status.py 1 0x48 \
    --distrib \
    --filter-by-value disabled 

# Event better `deasserted` value filter
status.py 1 0x48 \
    --distrib \
    --filter-by-value disabled,false,inactive
```

It is possible to combine `key` and `value` filters:

```shell
# from CH0 return only deasserted values
status.py 1 0x48 \
    --distrib \
    --filter-by-value ch0 \
    --filter-by-value disabled,false,inactive
```

### Extract raw data from status report

The `--unpack` option allows convenient 
data reduction

* if the requested filter has reduced the dataset
to a single value, we expose the raw data:

```shell
status.py 0 0x4A \
    --info --filter-by-key vendor # extract vendor info \
    --unpack # raw value

status.py 0 0x4A \
    --misc --filter-by-key temperature,value # extract t° reading \
    --unpack # raw value

# extract temperature alarm bit
status.py 0 0x4A \`
    --misc --filter-by-key temperature,alarm # extract t° alarm bit \
    --unpack # raw value
```

This is very convenient when importing data into an external script.
Here's an example in python once again:

```shell
import subprocess
args = [
    'status.py', 
    '0', '0x4A',
    '--misc', 
    '--filter-by-key', 'temperature,alarm' # extract raw bit
]
ret = subprocess.run(args)
if ret.exitcode == 0: # syscall OK
    # bool() direct cast 
    has_alarm = bool(ret.stdout.decode('utf-8'))
```

* If the status report comprises several value,
then `--unpack` simply reduces the structure to 1D.
That means we lose data because we can only have
a unique value per identifier

```shell
status.py 0 0x4A \
    --misc --filter-by-key temperature # extract temperature fields \
    --unpack
```

## Sys clock

`Sys` clock compensation is a new feature introduced in AD9546.
`sysclock.py` allows quick and easy access to these features.

To determine current `sysclock` related settings, use status.py with `--sysclock` option.

* `--freq`: to program input frequency [Hz]
* `--sel` : to select the input path (internal crystal or external XOA/B pins)
* `--div`: set integer division ratio on input frequency
* `--doubler`: enables input frequency doubler

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

Monitor internal calibration process with

```shell
status.py 1 0x4A \
    -pll --sysclk --filter-by-key calibrating
status.py 1 0x4A \
    --sysclk --irq --filter-by-key calibration 
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
When x is the `channel` and `y` is desired path.
```shell
# triggers Q0A Q0B Q1A Q1B SYNC 
distrib.py --q-sync 0 0x48

# triggers Q0A Q0B SYNC 
distrib.py --q-sync --channel 0 0 0x48

# triggers Q0B Q1B SYNC because --channel `all` is implied 
distrib.py --q-sync --path b 0 0x48
```

* `--unmute` : controls QXY unmuting opmode,
where x is the `channel` and `y` desired path.

```shell
# Q0A Q0B + Q1A Q1B `immediate` unmuting 
distrib.py --unmute immediate 0 0x48

# Q0A Q1A `phase locked` unmuting 
distrib.py --unmute phase --path a 0 0x48

# Q0B Q1B `freq locked` unmuting 
distrib.py --unmute freq --path b 0 0x48

# Q0A + Q1B `immediate` unmuting 
distrib.py --unmute immediate --path a 0 0x48
distrib.py --unmute immediate --path b 0 0x48
```

* `--pwm-enable` and `--pwm-disable`: constrols PWM modulator
for OUTxy where x is the `channel` and `y` the desired path.

* `--divider` : control integer division ratio at Qxy stage

```shell
# Sets R=48 division ratio, 
# for Q0A,AA,B,BB,C,CC and Q1A,AA,B,BB 
# because --channel=`all` and --path=`all` is implied
distrib.py --divider 48 0 0x48

# Sets Q1A,AA,B,BB R=64 division ratio
# because --path=`all` is implied
distrib.py --divider 64 --channel 1 0 0x48

# Q0A & Q0B R=23 division ratio
# requires dual assignment, because --pin {a,b} is not feasible at once
distrib.py --divider 23 --channel 0 --pin a 0 0x48
distrib.py --divider 23 --channel 0 --pin b 0 0x48
```

* `--half-divider` : enables "half divider" feature @ QXY path

* `--phase-offset` applies instantaneous phase offset to desired
output path. Maximal value is 2\*D-1 where D is previous `--divider` ratio
for given channel + pin.

```shell
# Apply Q0A,AA,B,BB,C,CC + Q1A,AA,B,BB 
# TODO
```

* `--unmuting` : controls "unmuting" behavior, meaning,
output signal can be exposed automatically depending on clock state.

* `--mute` and `--unmute` to manually enable/disable an output pin


## Reset script

To quickly reset the device

* `--soft` : performs a soft reset
* `--sans` : same thing but maintains current registers value 
* `--watchdog` : resets internal watchdog timer
* `-h` for more infos

```shell
# Resets (factory default)
reset.py --soft 1 0x48
regmap.py --load settings.json 1 0x48 
reset.py --sans 1 0x48 # settings are maintained
```

## Ref input script

`ref-input.py` to control the reference input signal,
signal quality constraints, switching mechanisms 
and the general clock state.

* `--freq` set REFxy input frequency [Hz]
* `--coupling` control REFx input coupling
`lock` must be previously acquired.
* `freq-lock-thresh` : frequency locking mechanism constraint.
* `phase-lock-thresh` : phase locking mechanism constraint.
* `phase-step-thresh` : inst. phase step threshold
* `phase-skew`: phase skew

## PLL script

`pll.py` to control both analog and digital internal PLL cores.  
`pll.py` also allows to set the clock to free run or holdover state.

* `--type`: to specify whether we are targetting an Analog PLL (APLLx) 
or a Digital PLL (APLLx). This field is only required
for operations where it is ambiguous (can be performed on both cores).  
`all` is the default value.   
`--type all` targets both APLLx and DPLLx core(s).

* `--channel` : set `x` in DPLLx or APLLx targeted cores.   
`--channel all`: is the default behavior, targets both channel 0 and 1 
of the desired type.

* `--free-run`: forces clock to free run state, `--type` is disregarded 
because `digital` is implied. 
* `--holdover`: forces clock to holdover state, `--type` is disregarded 
because `digital` is implied. 

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

## CCDPLL : Digitized Clocking Common Clock Synchronizer

CCDPLL status report:

```shell
status.py --ccdpll 1 0x48
```

CCDPLL must be configured and monitored for UTS & IUTS related operations

## User Time Stamping cores

UTS cores allow the user to timestamp input data against
a reference signal. UTS requires the CCDPPL that is
part of the Digitized clocking core to be configured.

`uts.py` controls both the UTS core and the inverse UTS core.
This is controlled by the `--type inverse` option.  
The default `--type` is "normal" for UTS management by default.  
Therefore it is mandatory to specify `inverse` for IUTS management.

UTS and IUTS status reports are reported by the status.py script:

```shell
status.py 1 0x4A \
    --uts \
    --iuts

status.py 0 0x48 \
    --uts \
    --filter-by-key fifo,0 
```

It is useful to combine this status report to the digitized
clocking status report as they are closely related

```shell
status.py 1 0x4A \
    --ccdpll \
    --uts
```

Some UTS/IUTS raw data are signed 24 or 48 bit values, this
portion of the status script should interprate those values correctly,
but it has to be confirmed / verified.

It is not clear at the moment which UTSx core (8 cores) is fed
to the UTS FIFO (unique fifo).
Therefore it is not clear to me which scaling should apply
when interprating the data contained in the UTS FIFO.   
At the moment, I hardcoded Core #0 (1st one) as the frequency source
&#10140; to clarify and improve.

### Inverse UTS management

TODO

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

`status.py --misc` returns (amongst other infos) the internal temperature sensor reading.  

* Get current reading :
```shell
status.py --misc 1 0x48
# Filter on field of interest like this
status.py --misc 1 0x48 --filter-by-key temperature,value --unpack
# Is temperature range currently exceeded
status.py --misc 1 0x48 --filter-by-key temperature,alarm --unpack
```

* Program a temperature range :

```shell
misc.py --temp-thres-low -10 # [°C]
misc.py --temp-thres-high 80 # [°C]
misc.py --temp-thres-low -30 --temp-thres-high 90
status.py --temp 0 0x48 # current reading [°C] 
```

Related warning events are then retrieved with the `irq.py` utility, refer to related section.

## Typical configuration flows

* load a profile preset, calibrate and get started

```shell
regmap.py --load profile.json --quiet 0 0x48
status.py --pll --distrib --filter-by-key ch0 0 0x48
calib.py --all 0 0x48
status.py --pll --distrib --filter-by-key ch0 0 0x48
```

* distrib operation: mute / unmute + powerdown (TODO)

* using integrated signal quality monitoring (TODO)
