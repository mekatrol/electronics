import serial
from time import sleep
import RPi.GPIO as GPIO


rx_enable = 23
driver_enable = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(rx_enable, GPIO.OUT)
GPIO.setup(driver_enable, GPIO.OUT)

GPIO.output(rx_enable, GPIO.LOW)
GPIO.output(driver_enable, GPIO.LOW)

ser = serial.Serial ("/dev/ttyAMA0", 9600)    #Open port with baud rate
while True:
    received_data = ser.read()              #read serial port
    sleep(1)
    data_left = ser.inWaiting()             #check for remaining byte
    received_data += ser.read(data_left)
    print (received_data)                   #print received data
    GPIO.output(rx_enable, GPIO.HIGH)
    GPIO.output(driver_enable, GPIO.HIGH)
    ser.write(received_data)                #transmit data serially
    sleep(1)
    GPIO.output(driver_enable, GPIO.LOW)
    GPIO.output(rx_enable, GPIO.LOW)

