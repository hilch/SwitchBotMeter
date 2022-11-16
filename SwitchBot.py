#!/usr/bin/env python3
#
# read out Switch Bot Meter
# https://github.com/hilch/SwitchBotMeter
#
#
# SwitchBot API https://github.com/OpenWonderLabs/SwitchBotAPI-BLE
#
# Inspired by [sbm2web.py by Thomas Rudolph](https://cc2.tv/halde/sbm2web.pyskript)
#

import asyncio
import math
from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData

class Scanner():
 
    def __init__(self, updateEvent : callable, names : dict = {} ):
        '''
        updateEvent : callable to receive information
        names : dict with { <mac_address> : <name> }
        '''
        self.__updateEvent = updateEvent
        self.__names = names
        self.__stop_event = asyncio.Event()

    def __update(self, adv_data : AdvertisementData):
        self.__temp = 0.0
        self.__hum = 0
        self.__batt = 0
        self.__dew = 0.0
        self.__unit = ''          
        self.__rssi = int(adv_data.rssi) 
           
        try:
            data = adv_data.service_data['0000fd3d-0000-1000-8000-00805f9b34fb']
            # Get temperature and related characteristics
            if data[0]  == 0x54:
                self.__device = 'WoSensorTH' # SwitchBot Meter TH51
                # Absolute value of temp
                self.__temp = (data[4] & 0b01111111) + ((data[3] & 0b00001111) / 10 )  
                if not (data[4] & 0b10000000):  # Is temp negative?
                        self.__temp = -self.__temp
                # unit set by user
                self.__unit = 'F' if data[5] & 0b10000000 else 'C'               
                # relative humidity in %
                self.__hum = data[5] & 0b01111111
                # battery health in %
                self.__batt = data[2] & 0b01111111  
                # Fahrenheit ?
                if self.__unit == 'F':
                    self._temp = self.__celsius2fahrenheit(self._temp)
                # dew point in degree
                # https://en.wikipedia.org/wiki/Dew_point
                a = 6.1121 # millibars
                b = 17.368 if self.__temp >= 0.0 else 17.966
                c = 238.88 if self.__temp >= 0.0 else 247.15 # °C;
                ps = a * math.exp(b*self.__temp/(c+self.__temp)) # saturated water vapor pressure [millibars]
                pa = self.__hum/100.0 * ps # actual vapor pressure [millibars]
                dp = c*math.log(pa/a) / ( b - math.log(pa/a) )
                if self.__unit == 'C':
                    self.__dew = round( dp, 1)
                else:
                    self.__dew =  round( self.__celsius2fahrenheit(dp), 1)  # Convert to F
            else:
                self.__device = 'unknown'
        except KeyError:
            self.__device = 'unknown'

    def __celsius2fahrenheit(self, celsius):
        return  celsius * 1.8 + 32.0

    def __delete__(self):
        self.__stop_event.set()

    async def scan(self):  

        def callback( device, advertising_data ):
            self.__update( advertising_data ) 
            if self.__device == 'WoSensorTH': 
                                 
                if callable( self.__updateEvent ):
                    self.__updateEvent( {
                        "device" : self.__device,
                        "address" : device.address,
                        "name" : self.__names.get(device.address, device.address),
                        "RSSI" : self.__rssi,
                        "temperature" : self.__temp,
                        "unit" : self.__unit,
                        "humidity" : self.__hum,
                        "dew_point" : self.__dew,
                        "battery" : self.__batt
                    }) 
            else: # other devices
                pass

        async with BleakScanner(callback) as scanner:
            # Important! Wait for an event to trigger stop, otherwise scanner
            # will stop immediately.
            await self.__stop_event.wait()



if __name__ == '__main__':
    
    def event( response : dict ):
        print( response )

    sm = Scanner( updateEvent= event )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sm.scan())
    loop.close()