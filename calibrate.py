#!/usr/bin/env python3

"""
ADC Sensor Calibration Script
Calibrates the sensor by detecting maximum and minimum values when readings
are above a baseline threshold. Run this script before using the sensor in
production to determine its range.
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
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import logging
from datetime import datetime
import json
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('calibration.log'),
        logging.StreamHandler()
    ]
)

# Calibration settings
BASELINE_THRESHOLD = 6000
CALIBRATION_FILE = 'sensor_calibration.json'

class SensorCalibrator:
    """Class to handle sensor calibration process"""
    
    def __init__(self):
        self.calibration_data = {
            'max_value': float('-inf'),
            'min_value': float('inf'),
            'max_voltage': float('-inf'),
            'min_voltage': float('inf'),
            'is_calibrating': False,
            'calibration_count': 0,  # Number of times sensor went above threshold
            'last_calibrated': None
        }
        self.running = True
        
    def setup_adc(self):
        """Initialize the ADC connection"""
        try:
            # Create the I2C bus
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Create the ADC object using the I2C bus
            ads = ADS.ADS1115(i2c)
            
            # Create single-ended input on channel 0
            chan = AnalogIn(ads, ADS.P0)
            
            return ads, chan
        except Exception as e:
            logging.error(f"Failed to initialize ADC: {str(e)}")
            raise

    def read_sensor(self, chan):
        """Read voltage and raw values from the ADC channel"""
        try:
            voltage = chan.voltage
            value = chan.value
            return voltage, value
        except Exception as e:
            logging.error(f"Error reading sensor: {str(e)}")
            return None, None

    def update_calibration(self, value, voltage):
        """Update calibration values when sensor reading is above baseline"""
        if value <= BASELINE_THRESHOLD:
            if self.calibration_data['is_calibrating']:
                self._save_calibration_cycle()
            return False
        
        # Start calibration when we go above threshold
        if not self.calibration_data['is_calibrating']:
            logging.info("\nSensor above baseline - starting new calibration cycle")
            self.calibration_data['is_calibrating'] = True
            self.calibration_data['calibration_count'] += 1
        
        # Update max/min values
        if value > self.calibration_data['max_value']:
            self.calibration_data['max_value'] = value
            self.calibration_data['max_voltage'] = voltage
            
        if value < self.calibration_data['min_value']:
            self.calibration_data['min_value'] = value
            self.calibration_data['min_voltage'] = voltage
        
        return True

    def _save_calibration_cycle(self):
        """Save the results of a calibration cycle"""
        logging.info("\nCalibration cycle complete:")
        logging.info(f"Max Value: {self.calibration_data['max_value']}, Max Voltage: {self.calibration_data['max_voltage']:.6f}V")
        logging.info(f"Min Value: {self.calibration_data['min_value']}, Min Voltage: {self.calibration_data['min_voltage']:.6f}V")
        
        self.calibration_data['is_calibrating'] = False
        self.calibration_data['last_calibrated'] = datetime.now().isoformat()
        
        # Save to file
        with open(CALIBRATION_FILE, 'w') as f:
            # Create a copy of calibration data without the is_calibrating flag
            save_data = self.calibration_data.copy()
            del save_data['is_calibrating']
            json.dump(save_data, f, indent=4)
        logging.info(f"Calibration data saved to {CALIBRATION_FILE}")

    def handle_signal(self, signum, frame):
        """Handle interrupt signals"""
        logging.info("\nReceived interrupt signal. Finishing calibration...")
        if self.calibration_data['is_calibrating']:
            self._save_calibration_cycle()
        self.running = False

    def run_calibration(self):
        """Main calibration loop"""
        logging.info("Starting sensor calibration...")
        
        try:
            ads, chan = self.setup_adc()
            ads.gain = 1
            
            logging.info("ADC initialized successfully")
            logging.info(f"Baseline threshold set to: {BASELINE_THRESHOLD}")
            logging.info("Move the sensor through its full range of motion")
            logging.info("Press Ctrl+C to finish calibration\n")
            
            while self.running:
                voltage, value = self.read_sensor(chan)
                
                if voltage is not None:
                    is_calibrating = self.update_calibration(value, voltage)
                    if is_calibrating:
                        logging.info(f"Calibrating - Current Value: {value}, Voltage: {voltage:.6f}V", end='\r')
                    else:
                        logging.info(f"Waiting - Value: {value}, Voltage: {voltage:.6f}V", end='\r')
                
                time.sleep(0.01)
                
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            if self.calibration_data['is_calibrating']:
                self._save_calibration_cycle()

def main():
    calibrator = SensorCalibrator()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, calibrator.handle_signal)
    signal.signal(signal.SIGTERM, calibrator.handle_signal)
    
    calibrator.run_calibration()

if __name__ == "__main__":
    main() 