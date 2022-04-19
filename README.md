# ADI clock tool 

Set of tools to interact & program AD954x chips by Analog Devices.    
These scripts are not Windows compatible.   
These scripts only interact with the chip through `i2c`, `spi` is not avaiable yet.

These toolsuites are developped & tested against an AD9545, some features
may behave differently on other chipsets

## Install libraries

```shell
python setup.py install
```

## API

* Each application comes with an `-h` help menu
* I2C bus is expected, 
specify which bus is used (`/dev` entry) with -b/ --bus flags, default is set to 0
* Slave address: mandatory, specify chiset slave adress with -a/--address as `hex` format

## Load a register map

Register map (`profiles`) can be created using A&D interfaces

* Load a register map

```shell
profile.py -b 0 -a 0x55 --load /tmp/map.json
profile.py -b 1 -a 0xAA -l /tmp/map.json
```

* Dump current map into A&D application compatible format

```shell
profile.py -b 0 -a 0x55 --dump /tmp/map.json
profile.py -b 0 -a 0x55 -d /tmp/map.json
```

## Chipset initialization

Initializes chipset for nominal operation.   
This macro is intended to be called once per configuration (like boot time).  

## Chipset calibration

Calibrates chipset for nominal operation.   
This macro is intended to be called once per session. 

## Chipset status

Returns status in a readable & loadable format

```shell
status.py /tmp/status.json
```
