# Loads Network connection and transmits stats the IoTPlotter API
import os
import time
import gc
import json
import urequests as requests
import network
import machine
from DHT22 import DHT22

# duplicate stdout and stderr to the log file - Catches errors and saves them.
logfile = open('log.txt', 'a')
os.dupterm(logfile)

### My Functions ###
def disconnect_and_turn_off_wifi():
    #print('Turning off WiFi before sleeping')
    wlan.disconnect()
    wlan.active(False)
    #wlan.deinit() <--- This function would cause problems with machine.lightsleep() and machine.deepsleep()
    #time.sleep(1)
    machine.Pin(23,machine.Pin.OUT).low()
    #time.sleep(1)
### END My Functions ###

# Header info for IoTPlotter
headers = {'api-key': 'MyAPIKeyforIoTPlotter'}

led = machine.Pin("LED", machine.Pin.OUT)
led.value(1) # LED On
led.value(0) # LED Off

ssid = 'MyWiFiNetwork'
password = 'MyWiFiPassword'

# Turn on WiFi Chip
machine.Pin(23,machine.Pin.OUT).high()

# Main Try While Loop
try:
    while True:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(ssid, password)

        # Wait for connect or fail
        max_wait = 120
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            #print('Waiting for WiFi connection...')
            time.sleep(1)

        # Handle connection errorsleep_time
        if wlan.status() != 3:
            #raise RuntimeError('Network connection failed!')
            #print('Network connection failed! I will have a short sleep and then restart...')
            disconnect_and_turn_off_wifi()
            machine.deepsleep(30000)
        else:
            s = 1
            while s > 0:
                s -= 1
                led.value(1)
                time.sleep(0.5)
                led.value(0)
                time.sleep(0.5)
                
            status = wlan.ifconfig()
            # print('\n')
            # print( 'Connected to WiFi Network: ' + ssid )
            # print('Device IP: ' + status[0] )
            # print('Subnet: ' + status[1])
            # print('Gateway: ' + status[2])
            # print('\n')

        # Read the DHT22 Temp sensor
        dht22 = DHT22(machine.Pin(15,machine.Pin.IN,machine.Pin.PULL_UP))
        
        get_time = requests.get(url='https://worldtimeapi.org/api/timezone/gmt')
        date_and_time = json.loads(get_time.text)
        temperature_C, humidity = dht22.read()
        temperature_F=32+(1.8*temperature_C)
        #print('Saving data locally...')
        tempDataLoggedLocally=open("Data.csv", "a")
        tempDataLoggedLocally.write(str(temperature_C) + ',' + str(date_and_time['datetime'][:16]) + '\n')
        tempDataLoggedLocally.close()
        get_time.close()
        #print('Sending the API: ', temperature_C)
        payload = {"data": {
            "TempTesty": [
            {
                "value": temperature_C
            }
            ]
        }}

        #led.value(1) # Turn LED on to signal payload transmission    
        #print('Sending Payload (', temperature_C, ') to IoTPlotter.com ...')
        response = requests.post("http://iotplotter.com/api/v2/feed/MyFeedNumberGoesHere", headers=headers, data=json.dumps(payload))
        response.close()
        #led.value(0) # Turn LED off to signal end of transmission
        # print("Free Memory: ", gc.mem_free())

        # print("Free Memory Before Clean-up: ", gc.mem_free())

        ### Starting to Clean Up and Shutdown ###
        # Release RAM Memory
        gc.collect()
        # print("Free Memory After Clean-up:  ", gc.mem_free(), '\n')

        #print('Performing clean-up of State Machine')
        rp2.PIO(0).remove_program()
        
        # My function to disconnect from WiFi and cut the power to the WiFi chip
        disconnect_and_turn_off_wifi()
        
        #print('Turning off the DHT22 sensor before sleeping')
        DHT22(machine.Pin(15,machine.Pin.IN,machine.Pin.PULL_DOWN))

        # print('Deep Sleeping for 120 seconds...')
        # time.sleep(1)

        machine.deepsleep(120000)
        
except KeyboardInterrupt as e:
    print("Keyboard interrupt detected at " + str(date_and_time['datetime'][:16]) + '\n')
    
    #print("Performing clean-up of State Machine...")
    #rp2.PIO(0).remove_program()
