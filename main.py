#!/usr/bin/env python3

"""
ADC Sensor Test Script
Reads analog data from a sensor connected to channel A0 of ADS1115/ADS1015 ADC
and logs the readings to a file.
"""

import sys
import os

# Check if running in virtual environment
if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
    print("Error: This script should be run within the virtual environment.")
    print("Please run './run.sh'")
    sys.exit(1)

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS  # Change to ads1015 if using ADS1015
from adafruit_ads1x15.analog_in import AnalogIn
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('sensor_readings.log'),
        logging.StreamHandler()
    ]
)

def setup_adc():
    """Initialize the ADC connection
    
    Uses hardware I2C port (1, 3, 2) and default I2C address 0x48 for ADS1115
    """
    try:
        # Create the I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Create the ADC object using the I2C bus
        ads = ADS.ADS1115(i2c)  # Change to ADS1015 if using that model
        # TODO: We want to enable continuous mode, but we need to know where to import Mode from
        # ads.mode = Mode.CONTINUOUS
        
        # Create single-ended input on channel 0
        chan = AnalogIn(ads, ADS.P0)
        
        return ads, chan
    except Exception as e:
        logging.error(f"Failed to initialize ADC: {str(e)}")
        raise

def read_sensor(chan):
    """Read voltage and raw values from the ADC channel"""
    try:
        voltage = chan.voltage
        raw = chan.value
        return voltage, raw
    except Exception as e:
        logging.error(f"Error reading sensor: {str(e)}")
        return None, None

def main():
    """Main function to continuously read and log sensor data"""
    logging.info("Starting ADC sensor test...")
    
    try:
        ads, chan = setup_adc()
        
        # Set the gain (optional, default is 1)
        ads.gain = 4
        
        logging.info("ADC initialized successfully")
        logging.info("Reading sensor data...")
        
        while True:
            voltage, value = read_sensor(chan)
            
            if voltage is not None:
                logging.info(f"Voltage: {voltage:.6f} V, Value: {value}")
            
            time.sleep(0.01)  # Adjust sampling rate as needed
            
    except KeyboardInterrupt:
        logging.info("Test stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main() 