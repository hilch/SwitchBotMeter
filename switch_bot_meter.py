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

class SwitchBotMeter():
 
    def __init__(self, adv_data : AdvertisementData):
        self.update(adv_data)


    def update(self, adv_data : AdvertisementData):
        self.__t = 0
        self.__h = 0
        self.__b = 0
        self.__u = ''          
        self.__rssi = int(adv_data.rssi) 
           
        try:
            data = adv_data.service_data['0000fd3d-0000-1000-8000-00805f9b34fb']
            # Get temperature and related characteristics
            if data[0]  == 0x54:
                self.__device = 'WoSensorTH' # SwitchBot Meter TH51
                self.__t = (data[4] & 0b01111111) + ((data[3] & 0b00001111) / 10 )  # Absolute value of temp
                if not (data[4] & 0b10000000):  # Is temp negative?
                        self.__t = -self.__t
                self.__u = 'F' if data[5] & 0b10000000 else 'C'               
                # # Get other info
                self.__h = data[5] & 0b01111111
                self.__b = data[2] & 0b01111111 
            else:
                self.__device = 'unknown'
        except KeyError:
            self.__device = 'unknown'


    def __celsius2fahrenheit(self, t):
        return t * 1.8 + 32.0


    def __repr__(self) -> str:
        return self.__device + self.__str__


    def __str__(self) -> str:
        return f'T={self.temperature}{self.unit} / H={self.humidity}%  / Dew={self.dew_point}{self.unit}  / Batt={self.battery}% / RSSI={self.rssi}dBm'


    @property
    def device(self) -> str:
        return self.__device


    @property
    def temperature(self) -> float:
        '''
        temperature
        '''
        if self.__u == 'C':
            return self.__t
        else:
            return round( self.__celsius2fahrenheit(self.__t), 1)  # Convert to F


    @property
    def humidity(self) -> float:
        '''
        relative humidity %
        '''
        return self.__h


    @property
    def unit(self) -> str:
        '''
        temperature scale [C]elsius / [F]ahrenheit
        '''
        return self.__u


    @property
    def dew_point(self) -> float:
        '''
        dew point 
        https://en.wikipedia.org/wiki/Dew_point
        '''     
        a = 6.1121 # millibars
        b = 17.368 if self.__t >= 0.0 else 17.966
        c = 238.88 if self.__t >= 0.0 else 247.15 # °C;
        ps = a * math.exp(b*self.__t/(c+self.__t)) # saturated water vapor pressure [millibars]
        pa = self.__h/100.0 * ps # actual vapor pressure [millibars]
        dp = c*math.log(pa/a) / ( b - math.log(pa/a) )
        if self.__u == 'C':
            return round(dp,1)
        else:
            return round( self.__celsius2fahrenheit(dp), 1)  # Convert to F

    @property
    def battery(self) -> int:
        '''
        battery health
        '''
        return self.__b

    @property
    def rssi(self) -> int:
        '''
        Radio Receive Signal Strength in dBm        
        '''
        return self.__rssi



async def main():  
    stop_event = asyncio.Event()

    # TODO: add something that calls stop_event.set()

    def callback(device, advertising_data ):
        sm = SwitchBotMeter( advertising_data )  

        if sm.device == 'WoSensorTH': 
            print(f'{device.address} : {str(sm)}' )
        else: # other devices
            pass

    async with BleakScanner(callback) as scanner:
        ...
        # Important! Wait for an event to trigger stop, otherwise scanner
        # will stop immediately.
        await stop_event.wait()

        # scanner stops when block exits
        ...


if __name__ == '__main__':
    asyncio.run(main())
