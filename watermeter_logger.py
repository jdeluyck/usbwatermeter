#!/usr/bin/python
# -*- coding: utf-8 -*-
# Credits to python port of nrf24l01, Joao Paulo Barrac & maniacbugs original c library, and this blog: http://blog.riyas.org

import serial
import time
import os
import logging
import logging.handlers
import sys, traceback
import unicodedata
import pytz
import requests
from datetime import datetime, timedelta
from ConfigParser import SafeConfigParser
from apscheduler.schedulers.background import BackgroundScheduler

import urllib
import urllib2

def remoteLog(valueToLog):
	logger.info('Logging remotely...')

	URL=REMOTELOG_URL+ "?type=command&param=udevice&idx="+ REMOTELOG_IDX+ "&svalue="+ str(valueToLog)

	req = urllib2.Request(URL)
	
	try:
		response = urllib2.urlopen(req, timeout=5)
	except urllib2.HTTPError, e:
		logger.info('HTTPError: '+ str(e))
	except urllib2.URLError as e:
		logger.info('URLError: '+ str(e))
	else:
		result = response.read()
		logger.info('successfully logged data (' + str(valueToLog) + ') remotely')

###########################
# PERSONAL CONFIG FILE READ
###########################

parser = SafeConfigParser()
parser.read('watermeter_logger.ini')

# Read path to log file
LOG_FILENAME = parser.get('config', 'log_filename')

LOG_PERIOD = parser.getint('config', 'log_period')

# remote logging URL
REMOTELOG_URL = parser.get('config', 'remotelog_url')

# Idx
REMOTELOG_IDX = parser.get('config', 'sensor_idx')

#################
#  LOGGING SETUP
#################
logging.basicConfig()

LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
#handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=5)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
	def __init__(self, logger, level):
		"""Needs a logger and a logger level."""
		self.logger = logger
		self.level = level

	def write(self, message):
		# Only log if there is a message (not just a new line)
		if message.rstrip() != "":
			self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

logger.info('Starting Watermeter logger')

ser = serial.Serial('/dev/ttyUSB0', 115200)

old_counter_value = -1
total_in_period = 0
current_val = 0

def log_value():
	global total_in_period
	global current_val
	
	logger.info('nb liters in last period: %d (current=%d)' % (total_in_period, current_val))

	if total_in_period != 0:
		remoteLog(total_in_period) 

	total_in_period = 0

logger.info("log period: %d seconds", LOG_PERIOD)

scheduler = BackgroundScheduler()
scheduler.add_job(log_value, 'interval', seconds=LOG_PERIOD)
scheduler.start()

iter = 0

try:
	while True:
		out = ser.readline()
		logger.info('Received: %s' % out)
		params = out.split(":")
		if (len(params) == 3): #protection again corrupted/incomplete messages
			sensor = params[0]
			message = params[1]
			value = params[2].strip('X')
		else:
			continue
		
		if (sensor == "water" and message == "top"):
			current_val = int(value)
			if (old_counter_value == -1):
				old_counter_value = current_val
			else:
				delta = current_val - old_counter_value
				if (delta > 1):
					logger.info('MISSED tops (delta=%d)' % delta)
				total_in_period += delta
				old_counter_value = current_val
except:
	logger.info("*****Exception in main loop******")
	exc_type, exc_value, exc_traceback = sys.exc_info()
	traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)	
	del exc_traceback
	scheduler.shutdown()
	logger.info('EXITING watermeter logger')


