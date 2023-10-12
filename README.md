# dbus-tasmota-smartmeter Service

### Purpose

This service is meant to be run on a cerbo gx with Venus OS from Victron.

The Python script cyclically reads data from a micro controller with Tasmota and an IR reader via REST API and publishes information on the dbus, using the service name com.victronenergy.grid. This makes the Venus OS work as if you had a physical Victron Grid Meter installed.

### Configuration

In the Python file, you should put the IP of your Tasmota device that hosts the REST API. In addition, you need to change the JSON attributes in lines 80-94 according to your JSON structure (see your tasmota device: http://192.168.XXX.XXX/cm?cmnd=status%2010)

### Installation

1. Copy the files to the /data folder on your venus:

   - /data/dbus-tasmota-smartmeter/dbus-tasmota-smartmeter.py
   - /data/dbus-tasmota-smartmeter/kill_me.sh
   - /data/dbus-tasmota-smartmeter/service/run

2. Set permissions for files:

   `chmod 755 /data/dbus-tasmota-smartmeter/service/run`

   `chmod 744 /data/dbus-tasmota-smartmeter/kill_me.sh`

3. Get two files from the [velib_python](https://github.com/victronenergy/velib_python) and install them on your venus:

   - /data/dbus-tasmota-smartmeter/vedbus.py
   - /data/dbus-tasmota-smartmeter/ve_utils.py

4. Add a symlink to the file /data/rc.local:

   `ln -s /data/dbus-tasmota-smartmeter/service /service/dbus-tasmota-smartmeter`

   Or if that file does not exist yet, store the file rc.local from this service on your Raspberry Pi as /data/rc.local .
   You can then create the symlink by just running rc.local:
  
   `rc.local`

   The daemon-tools should automatically start this service within seconds.

### Debugging

You can check the status of the service with svstat:

`svstat /service/dbus-tasmota-smartmeter`

It will show something like this:

`/service/dbus-tasmota-smartmeter: up (pid 10078) 325 seconds`

If the number of seconds is always 0 or 1 or any other small number, it means that the service crashes and gets restarted all the time.

When you think that the script crashes, start it directly from the command line:

`python /data/dbus-tasmota-smartmeter/dbus-tasmota-smartmeter.py`

and see if it throws any error messages.

If the script stops with the message

`dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.grid"`

it means that the service is still running or another service is using that bus name.

#### Restart the script

If you want to restart the script, for example after changing it, just run the following command:

`/data/dbus-tasmota-smartmeter/kill_me.sh`

The daemon-tools will restart the scriptwithin a few seconds.

### Hardware

In my installation at home, I am using the following Hardware:

- Many Hoymiles Inverter
- ESP8266 mini Board d1 and bitShake SmartMeterReader
- Victron MultiPlus-II - Battery Inverter (single phase)
- Cerbo GX
- Pylontech US5000 - LiFePO Battery

## Thank you

Many thanks for sharing the knowledge:

* [venus.dbus-fronius-smartmeter](https://github.com/RalfZim/venus.dbus-fronius-smartmeter)
* [multiplus-ii-ess-modene-messeinrichtung-statt-em24](https://community.victronenergy.com/articles/170837/multiplus-ii-ess-modene-messeinrichtung-statt-em24.html)