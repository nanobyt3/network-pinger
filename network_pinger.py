#!/usr/bin/python3
#!/usr/bin/env python
import os
import subprocess
import RPi.GPIO as GPIO
import time
import atexit
import logging
from logging.handlers import TimedRotatingFileHandler


pingServer = '8.8.4.4'
timeout = '100'
pingDropThreshold = 5
logFileName = '/home/pi/network-pinger-logs/pinger.log'

pins = {
  "eth0red": 11,
  "eth1red": 12,
  "eth2red": 13,
  "eth0green": 15,
  "eth1green": 16,
  "eth2green": 18
}
Interfaces = {"eth0":"airtel", "eth1":"tatasky", "eth2":"pdpl"}
Status = {"eth0":False, "eth1":False, "eth2":False}
Drops = {"eth0":0, "eth1":0, "eth2":0}
DND = {"from":21, "to": 7}
IsApacheServerUp = 0;
logger = logging.getLogger("Rotating Log")


def setup():
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(pins['eth0red'], GPIO.OUT)
  GPIO.output(pins['eth0red'], GPIO.LOW)
  GPIO.setup(pins['eth1red'], GPIO.OUT)
  GPIO.output(pins['eth1red'], GPIO.LOW)
  GPIO.setup(pins['eth2red'], GPIO.OUT)
  GPIO.output(pins['eth2red'], GPIO.LOW)
  GPIO.setup(pins['eth0green'], GPIO.OUT)
  GPIO.output(pins['eth0green'], GPIO.LOW)
  GPIO.setup(pins['eth1green'], GPIO.OUT)
  GPIO.output(pins['eth1green'], GPIO.LOW)
  GPIO.setup(pins['eth2green'], GPIO.OUT)
  GPIO.output(pins['eth2green'], GPIO.LOW)
  os.system('amixer set Headphone 100%')
  atexit.register(destroy)
  #Set logging file
  create_timed_rotating_log(logFileName)
  

def create_timed_rotating_log(path):
  global logger
  """"""
  log_format = "%(asctime)s - %(levelname)s - %(message)s"
  log_level = 10
  formatter = logging.Formatter(log_format)
  logger.setLevel(logging.INFO)  
  
  handler = TimedRotatingFileHandler(path,
                                     when="midnight",
                                     interval=1,
                                     backupCount=365)
  handler.setLevel(log_level)
  handler.setFormatter(formatter)  
  logger.addHandler(handler)


def soundNotify(Interface, NewStatus):
  now = time.localtime(time.time())
  current_time = now.tm_hour
  if current_time <= DND['from'] and current_time >= DND['to']:
    if Status[Interface] != NewStatus:
      if NewStatus == True:
        logger.warning(Interfaces[Interface].upper() + ' on ' + Interface + ' is UP!')
        os.system('mpg123 -f 32768 /home/pi/network-pinger/sounds/' + Interfaces[Interface] + '_network_up.mp3')      
      else:
        logger.warning(Interfaces[Interface].upper() + ' on ' + Interface + ' is DOWN!')
        os.system('mpg123 -f 32768 /home/pi/network-pinger/sounds/' + Interfaces[Interface] + '_network_down.mp3')
      Status[Interface] = NewStatus


def loop():

  while True:
    for i in Interfaces:
      res = subprocess.call(['fping', '-c 1', '-t ' + timeout, '-I', i, pingServer])
      if res == 0:
        print ("ping to", i, "OK")
        Drops[i] = 0
        GPIO.output(pins[i + 'green'], GPIO.LOW)
        GPIO.output(pins[i + 'red'], GPIO.HIGH)
        soundNotify(i, True)
        #if i == 'eth0' and IsApacheServerUp == 0:
        #  subprocess.check_call("sudo service apache2 start".split())
        #  IsApacheServerUp = 1
        #  subprocess.check_call("sudo ifconfig eth1 down".split())
        #  subprocess.check_call("sudo ifconfig eth2 down".split())
        #  subprocess.check_call("sudo ifconfig eth1 up".split())
        #  subprocess.check_call("sudo ifconfig eth2 up".split())
      elif res == 2:
        print ("no response from", i)
        Drops[i] = Drops[i] + 1
        if Drops[i] >= pingDropThreshold:
          GPIO.output(pins[i + 'green'], GPIO.HIGH)
          GPIO.output(pins[i + 'red'], GPIO.LOW)
          soundNotify(i, False)
        else:
          logger.info('Ping(' + str(Drops[i]) + ') timeout for ' + Interfaces[i].upper() + ' on ' + i)
      else:
        print ("ping to", i, "failed!")
        Drops[i] = Drops[i] + 1
        if Drops[i] >= pingDropThreshold:
          GPIO.output(pins[i + 'green'], GPIO.HIGH)
          GPIO.output(pins[i + 'red'], GPIO.LOW)
          soundNotify(i, False)
        else:
          logger.info('Ping(' + str(Drops[i]) + ') timeout for ' + Interfaces[i].upper() + ' on ' + i)

    time.sleep(1)

  
def testLEDs():
  i = 'eth0'
  while True:
    GPIO.output(pins[i + 'green'], GPIO.LOW)
    GPIO.output(pins[i + 'red'], GPIO.HIGH)


def destroy():
  GPIO.output(pins['eth0red'], GPIO.HIGH)
  GPIO.output(pins['eth1red'], GPIO.HIGH)
  GPIO.output(pins['eth2red'], GPIO.HIGH)
  GPIO.output(pins['eth0green'], GPIO.HIGH)
  GPIO.output(pins['eth1green'], GPIO.HIGH)
  GPIO.output(pins['eth2green'], GPIO.HIGH)
  GPIO.cleanup()


if __name__ == '__main__':
  setup()
  try:
    loop()
    #testLEDs()
  except KeyboardInterrupt:
    #destroy()
    print('exit')
