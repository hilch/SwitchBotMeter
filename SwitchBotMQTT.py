#!/usr/bin/env python3
#
# read out Switch Bot Meter
# https://github.com/hilch/SwitchBotMeter
#
#
# publish SwitchBot sensor data via MQTT to Domoticz

import asyncio

import paho.mqtt.client as mqtt

from SwitchBot import Scanner

broker = 'homeserver.fritz.box'
port = 1883
topic = "domoticz/in"
username = 'admin'
password = 'xxxxxxxxxxxx'

#table with MAC and Domiticz's Idx of dummy virtual device

macs = {
    "D2:68:00:00:00:00" : "14",         # dining room
    "F3:50:00:00:00:00" : "9",          # office
    "FF:A4:00:00:00:00" : "11",         # bedroom
    "E5:12:00:00:00:00" : "15",         # bathroom
    "F9:4D:00:00:00:00" : "12",         # outdoor
    "D5:75:00:00:00:00" : "13"          # cellar
}


def on_connect(client, userdata, flags, rc):
    print("connect")

def on_connectFail(client, userdata, flags, rc):
    print("connect failed.")

def on_publish(client, userdata, flags):
    pass

 


if __name__ == '__main__':
    client = mqtt.Client(client_id="SwitchBotScanner",
                         transport="tcp")


    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_connect_fail = on_connectFail

    client.username_pw_set(username, password)
    client.connect( host = broker, port = port, keepalive= 120 )   
    client.loop_start()

   

    def event( response : dict ):
        idx = response["name"]
        temp = response["temperature"]
        hum = response["humidity"]
        hum_status = 2 # dry
        if hum > 40 and hum <= 65:
            hum_status = 0 # normal
        elif hum > 6:
            hum_status = 3 # wet

        batt = response["battery"] 
        rssi = response["RSSI"]

        message = f'{{ "idx" : {idx},  "nvalue" : 0, "svalue" : "{temp};{hum};{hum_status}", "Battery" : {batt}, "RSSI" : {rssi}  }}'
        print( message )
        client.publish( topic = topic, payload = message )


    sm = Scanner( updateEvent= event, names = macs )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sm.scan())
    loop.close()

