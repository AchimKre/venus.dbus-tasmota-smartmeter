#!/usr/bin/env python

##########################
# adapt form
# juf
# and
# fabian-lauer / dbus-shelly-3em-smartmeter
# and
# RalfZim / venus.dbus-fronius-smartmeter
##########################################


 
# import normal packages
import platform 
import logging
import sys
import os
import sys
if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject
import sys
import time
import requests # for http GET
 
# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService

class DbusSmartmeterService:
  def __init__(self, servicename, deviceinstance, paths, productname='Tasmota', connection='Tasmota Web service'):
    self._dbusservice = VeDbusService("{}.http_{:02d}".format(servicename, deviceinstance))
    self._paths = paths
 
    logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))
 
    # Create the management objects, as specified in the ccgx dbus-api document
    self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
    self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
    self._dbusservice.add_path('/Mgmt/Connection', connection)
 
    # Create the mandatory objects
    self._dbusservice.add_path('/DeviceInstance', deviceinstance)
    self._dbusservice.add_path('/ProductId', 45069) # found on https://www.sascha-curth.de/projekte/005_Color_Control_GX.html#experiment - should be an ET340 Engerie Meter
    self._dbusservice.add_path('/DeviceType', 345) # found on https://www.sascha-curth.de/projekte/005_Color_Control_GX.html#experiment - should be an ET340 Engerie Meter																																										   
    self._dbusservice.add_path('/ProductName', productname)
    self._dbusservice.add_path('/CustomName', productname)    
    self._dbusservice.add_path('/Latency', None)    
    self._dbusservice.add_path('/FirmwareVersion', 0.1)
    self._dbusservice.add_path('/HardwareVersion', 0)
    self._dbusservice.add_path('/Connected', 1)
    self._dbusservice.add_path('/Role', 'grid')
    self._dbusservice.add_path('/Position', 0) # normaly only needed for pvinverter
    self._dbusservice.add_path('/UpdateIndex', 0)
 
    # add path values to dbus
    for path, settings in self._paths.items():
      self._dbusservice.add_path(
        path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)
 
    # last update
    self._lastUpdate = 0
 
    # add _update function 'timer'
    gobject.timeout_add(250, self._update) # pause 250ms before the next request
    
    # add _signOfLife 'timer' to get feedback in log every 5minutes
    gobject.timeout_add(1000, self._update)
 
  def _update(self):   
  
    try:
      meter_url = "http://192.168.XXX.XXX/cm?cmnd=status%2010"
      meter_r = requests.get(url=meter_url) # request data from the Tasmota Smartmeter
      meter_data = meter_r.json() # convert JSON data
      #meter_consumption = meter_data['StatusSNS']['MT681']['DJ_TPWRCURR']['DJ_TPWRIN']['DJ_TPWROUT']
      #send data to DBus
      self._dbusservice['/Ac/Power'] = meter_data['StatusSNS']['MT681']['Power_cur'] # positive: consumption, negative: feed into grid
      self._dbusservice['/Ac/Current'] = float(meter_data['StatusSNS']['MT681']['Power_cur'] / 230 )
      self._dbusservice['/Ac/L1/Voltage'] = 230
       #self._dbusservice['/Ac/L2/Voltage'] = 230
       #self._dbusservice['/Ac/L3/Voltage'] = 230
      self._dbusservice['/Ac/L1/Current'] = float(meter_data['StatusSNS']['MT681']['Power_cur'] / 230 )
       #self._dbusservice['/Ac/L2/Current'] = 1
       #self._dbusservice['/Ac/L3/Current'] = 1
      self._dbusservice['/Ac/L1/Power'] = float(meter_data['StatusSNS']['MT681']['Power_cur'])
       #self._dbusservice['/Ac/L2/Power'] = 59
       #self._dbusservice['/Ac/L3/Power'] = 59
      self._dbusservice['/Ac/L1/Energy/Forward'] = meter_data['StatusSNS']['MT681']['Total_in']
       #self._dbusservice['/Ac/L2/Energy/Forward'] = 0.059
       #self._dbusservice['/Ac/L3/Energy/Forward'] = 0.059																				  
      self._dbusservice['/Ac/L1/Energy/Reverse'] = meter_data['StatusSNS']['MT681']['Total_out'] 
      self._dbusservice['/Ac/Energy/Forward'] = self._dbusservice['/Ac/L1/Energy/Forward']
      self._dbusservice['/Ac/Energy/Reverse'] = self._dbusservice['/Ac/L1/Energy/Reverse']
      #logging
      logging.debug("House Consumption (/Ac/Power): %s" % (self._dbusservice['/Ac/Power']))
      logging.debug("House Forward (/Ac/Energy/Forward): %s" % (self._dbusservice['/Ac/Energy/Forward']))
      logging.debug("House Reverse (/Ac/Energy/Revers): %s" % (self._dbusservice['/Ac/Energy/Reverse']))
      logging.debug("---");
       
       # increment UpdateIndex - to show that new data is available
      index = self._dbusservice['/UpdateIndex'] + 1  # increment index
      if index > 255:   # maximum value of the index
       index = 0 # overflow from 255 to 0
      self._dbusservice['/UpdateIndex'] = index

      #update lastupdate vars
      self._lastUpdate = time.time()              
    except Exception as e:
      logging.critical('Error at %s', '_update', exc_info=e)
       
     # return true, otherwise add_timeout will be removed from GObject - see docs http://library.isr.ist.utl.pt/docs/pygtk2reference/gobject-functions.html#function-gobject--timeout-add
    return True
 
  def _handlechangedvalue(self, path, value):
    logging.debug("someone else updated %s to %s" % (path, value))
    return True # accept the change
 


def main():
  #configure logging
  logging.basicConfig(      format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.INFO,
                            handlers=[
                                logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                                logging.StreamHandler()
                            ])
 
  try:
      logging.info("Start");
  
      from dbus.mainloop.glib import DBusGMainLoop
      # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
      DBusGMainLoop(set_as_default=True)
     
      #formatting 
      _kwh = lambda p, v: (str(round(v, 2)) + 'KWh')
      _a = lambda p, v: (str(round(v, 1)) + 'A')
      _w = lambda p, v: (str(round(v, 1)) + 'W')
      _v = lambda p, v: (str(round(v, 1)) + 'V')   
     
      #start our main-service
      pvac_output = DbusSmartmeterService(
        servicename='com.victronenergy.grid',
        deviceinstance=40,
        paths={
          '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh}, # energy bought from the grid
          '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh}, # energy sold to the grid
          '/Ac/Power': {'initial': 0, 'textformat': _w},
          
          '/Ac/Current': {'initial': 0, 'textformat': _a},
          '/Ac/Voltage': {'initial': 0, 'textformat': _v},
          
          '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L2/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L3/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L1/Energy/Forward': {'initial': 0, 'textformat': _kwh},
          '/Ac/L2/Energy/Forward': {'initial': 0, 'textformat': _kwh},
          '/Ac/L3/Energy/Forward': {'initial': 0, 'textformat': _kwh},
          '/Ac/L1/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
          '/Ac/L2/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
          '/Ac/L3/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
        })
     
      logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
      mainloop = gobject.MainLoop()
      mainloop.run()            
  except Exception as e:
    logging.critical('Error at %s', 'main', exc_info=e)
if __name__ == "__main__":
  main()

