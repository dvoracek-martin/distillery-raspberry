import os
import time
from calendar import calendar
from datetime import datetime

import RPi.GPIO as GPIO
import requests


class Distillery():

    # turn on heater
    def power_on(self, pin):
        GPIO.output(pin, GPIO.LOW)

    # turn off heater
    def power_off(self, pin):
        GPIO.output(pin, GPIO.HIGH)

    # temperature sensor
    def sensor(self):
        for i in os.listdir('/sys/bus/w1/devices'):
            if i != 'w1_bus_master1':
                ds18b20 = i
        return ds18b20

    # read temperature
    def readTemperature(self, ds18b20):
        location = '/sys/bus/w1/devices/' + ds18b20 + '/w1_slave'
        tfile = open(location)
        text = tfile.read()
        tfile.close()
        secondline = text.split("\n")[1]
        temperaturedata = secondline.split(" ")[9]
        temperature = float(temperaturedata[2:])
        celsius = temperature / 1000
        farenheit = (celsius * 1.8) + 32
        return celsius, farenheit

    def kill(self):
        quit()

    # calculate the flow
    def pulseCallback(self, p):
        # Calculate the time difference since last pulse recieved
        current_time = datetime.now()
        diff = (current_time - self.last_time).total_seconds()

        # Calculate current flow rate
        hertz = 1. / diff
        self.flow_rate = hertz / 7.5

        # Reset time of last pulse
        self.last_time = current_time

    def getFlowRate(self):
        if (datetime.now() - self.last_time).total_seconds() > 1:
            self.flow_rate = 0.0

        return self.flow_rate

    def __init__(self):
        self.flow_rate = 0.0
        self.last_time = datetime.now()


def main():
    # Configure GPIO pins
    input_pin = 27
    output_pin = 17

    # GPIO setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(output_pin, GPIO.OUT)
    GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Init FlowMeter instance and pulse callback
    distillery = Distillery()
    distillery.power_off(output_pin)
    GPIO.add_event_detect(input_pin, GPIO.RISING, callback=distillery.pulseCallback)

    serial_num = distillery.sensor()
    # api-endpoint
    backend_base_url = "http://localhost:8080/api/data"

    # Begin infinite loop
    while True:
        try:
            # GET
            try:
                response = requests.get(backend_base_url + "/last")
                data = response.json()
                print("GET:  " + str(data))
                print("time: " + str(data['timeElapsed']))

                turn_on = (data['turnOn'])
                waiting = (data['waiting'])

                if turn_on is False:
                    distillery.power_off(output_pin)
                else:
                    distillery.power_on(output_pin)
                now = int(datetime.utcnow().timestamp()*1e3)

                # POST
                body = {
                    'planId': data['planId'],
                    'currentPhaseId': data['currentPhaseId'],
                    'temperature': distillery.readTemperature(serial_num)[0],
                    'timeElapsed': (data['timeElapsed']),
                    'timestamp': now,
                    'alcLevel': data['alcLevel'],
                    'weight': data['weight'],
                    'waiting': waiting,
                    'flow': distillery.getFlowRate(),
                    'terminate': data['terminate'],
                    'turnOn': turn_on
                }
                response = requests.post(backend_base_url, json=body)
                data = response.json()
                print("POST: " + str(data))

                # Delay
                time.sleep(5)
            except Exception as e:
                print('Exception: '+ str(e))
                time.sleep(5)
        except KeyboardInterrupt:
            GPIO.cleanup()
            distillery.kill()


if __name__ == '__main__':
    main()
