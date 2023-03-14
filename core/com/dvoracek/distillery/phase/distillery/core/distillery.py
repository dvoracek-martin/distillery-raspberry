import json
import random
from datetime import datetime

from kafka import KafkaConsumer
from kafka import KafkaProducer

# import RPi.GPIO as GPIO

bootstrap_servers = ['localhost:29092']


class Distillery:

    # # turn on heater
    # def power_on(self, pin):
    #     GPIO.output(pin, GPIO.LOW)
    #
    # # turn off heater
    # def power_off(self, pin):
    #     GPIO.output(pin, GPIO.HIGH)
    #
    # # temperature sensor
    # def sensor(self):
    #     for i in os.listdir('/sys/bus/w1/devices'):
    #         if i != 'w1_bus_master1':
    #             ds18b20 = i
    #     return ds18b20
    #
    # # read temperature
    # def readTemperature(self, ds18b20):
    #     location = '/sys/bus/w1/devices/' + ds18b20 + '/w1_slave'
    #     t_file = open(location)
    #     text = t_file.read()
    #     t_file.close()
    #     second_line = text.split("\n")[1]
    #     temperature_data = second_line.split(" ")[9]
    #     temperature = float(temperature_data[2:])
    #     celsius = temperature / 1000
    #     fahrenheit = (celsius * 1.8) + 32
    #     return celsius, fahrenheit
    #
    # @staticmethod
    # def kill():
    #     quit()
    #
    # # calculate the flow
    # def pulse_callback(self, p):
    #     # Calculate the time difference since last pulse received
    #     current_time = datetime.now()
    #     diff = (current_time - self.last_time).total_seconds()
    #
    #     # Calculate current flow rate
    #     hertz = 1. / diff
    #     self.flow_rate = hertz / 7.5
    #
    #     # Reset time of last pulse
    #     self.last_time = current_time
    #
    # def get_flow_rate(self):
    #     if (datetime.now() - self.last_time).total_seconds() > 1:
    #         self.flow_rate = 0.0
    #
    #     return self.flow_rate
    #
    def __init__(self):
        self.flow_rate = 0.0
        self.last_time = datetime.now()


def main():
    def kafkaDistillationStartedConsumer():
        consumer = KafkaConsumer(group_id='distillery-raspberry', bootstrap_servers=bootstrap_servers)
        consumer.subscribe(
            ['distillation-started', 'distillation-paused', 'distillation-continued', 'distillation-terminated',
             'distillation-progress-backend'])
        producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        isPaused = False
        isRunning = False

        for msg in consumer:
            if (msg.topic == 'distillation-started'):
                print('DISTILLATION STARTED')
                print('Turning the power on - started')
                isRunning = True
                isPaused = False
            if (msg.topic == 'distillation-paused'):
                print('DISTILLATION PAUSED')
                if (isPaused is False):
                    print('Turning the power off - paused')
                isPaused = True
                isRunning = False
            if (msg.topic == 'distillation-continued'):
                # print('DISTILLATION CONTINUED')
                if (isPaused is True and isRunning is False):
                    print('Turning the power on - continued')
                isPaused = False
                isRunning = True
            if (msg.topic == 'distillation-terminated'):
                print('DISTILLATION TERMINATED')
                print('Turning the power off - terminated')
                isPaused = False
                isRunning = False
            if (msg.topic == 'distillation-progress-backend'):
                # print('DISTILLATION PROGRESS BACKEND')
                # print('Getting information from the sensors and sending it to backend')
                receivedFromBackend = json.loads(msg.value)
                body = {
                    'timeElapsedInMillis': receivedFromBackend["timeElapsedInMillis"],
                    'distillationProcedureId': receivedFromBackend["distillationProcedureId"],
                    'temperature': (38 + random.randint(0, 9)),
                    'weight': (350 + random.randint(0, 50)),
                    'flow': 3700 + (random.randint(0, 500)),
                }
                producer.send('distillation-progress-raspberry', json.dumps(body).encode('utf-8'))
                producer.flush()

    kafkaDistillationStartedConsumer()


if __name__ == '__main__':
    main()
