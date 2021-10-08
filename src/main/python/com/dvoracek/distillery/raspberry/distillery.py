import os
import time
from datetime import datetime

import RPi.GPIO as GPIO
import requests


class Distillery():

    # turn on heater
    def power_on(self, pin):
        GPIO.output(pin, GPIO.HIGH)

    # turn off heater
    def power_off(self, pin):
        GPIO.output(pin, GPIO.LOW)

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
    flow_meter = Distillery()
    GPIO.add_event_detect(input_pin, GPIO.RISING, callback=flow_meter.pulseCallback)

    serial_num = flow_meter.sensor()
    # api-endpoint
    backend_base_url = "http://localhost:8080/api/data"

    # Begin infinite loop
    while True:
        try:
            # GET
            response = requests.get(backend_base_url + "/last")
            data = response.json()
            print("GET:  " + data)
            turn_on = (data['turnOn'])
            waiting = (data['waiting'])
            if flow_meter.readTemperature(serial_num) is not None:
                if turn_on and not waiting:
                    flow_meter.power_off(output_pin)
                else:
                    flow_meter.power_on(output_pin)

            # POST
            body = {'temperature': flow_meter.readTemperature(serial_num)[0],
                    'flow': flow_meter.getFlowRate()
                    }
            response = requests.post(backend_base_url, json=body)
            data = response.json()
            print("POST: " + data)

            # Delay
            time.sleep(5)
        except KeyboardInterrupt:
            GPIO.cleanup()
            flow_meter.kill()


if __name__ == '__main__':
    main()
