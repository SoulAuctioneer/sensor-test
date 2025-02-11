#!/usr/bin/env python3

"""
ADC Sensor Test Script
Reads analog data from a linear softpot touch sensor connected to channel A0 of ADS1115/ADS1015 ADC
and displays a visual indicator of touch position.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('sensor_readings.log'),
        logging.StreamHandler()
    ]
)

# Softpot calibration values
LEFT_MAX = 17625   # Maximum value (far left)
RIGHT_MIN = 6000   # Minimum value (far right)
POSITION_WIDTH = 40  # Width of the visual indicator in characters
NO_TOUCH_THRESHOLD = 5000  # Values below this indicate no touch

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
        value = chan.value
        return voltage, value
    except Exception as e:
        logging.error(f"Error reading sensor: {str(e)}")
        return None, None

def get_position_indicator(value):
    """Convert sensor value to a visual position indicator
    
    Args:
        value (int): Raw sensor value
        
    Returns:
        tuple: (str: ASCII visualization of touch position, bool: is_touching)
    """
    # Check if sensor is being touched
    if value < NO_TOUCH_THRESHOLD or value > LEFT_MAX + 1000:
        # Show empty bar when not touched
        return f"[{'─' * POSITION_WIDTH}] (no touch)", False
    
    # Handle values outside calibrated range but still indicating touch
    if value > LEFT_MAX:
        value = LEFT_MAX
    elif value < RIGHT_MIN:
        value = RIGHT_MIN
        
    # Calculate position as percentage (0 to 1) where 0 is right and 1 is left
    position = (value - RIGHT_MIN) / (LEFT_MAX - RIGHT_MIN)
    
    # Convert to position in the display width
    pos = int(position * POSITION_WIDTH)
    
    # Create the visual indicator
    indicator = ['─'] * POSITION_WIDTH
    indicator[pos] = '●'
    
    return f"[{''.join(indicator)}]", True

def main():
    """Main function to continuously read and display touch position"""
    print("\nLinear Softpot Touch Sensor")
    print("Left" + " " * (POSITION_WIDTH - 2) + "Right")
    
    try:
        ads, chan = setup_adc()
        ads.gain = 1
        
        logging.info("ADC initialized successfully")
        print("\nTouch the sensor to see position...\n")
        
        last_display = ""
        while True:
            voltage, value = read_sensor(chan)
            
            if voltage is not None:
                display, is_touching = get_position_indicator(value)
                # Only update display if position changed
                if display != last_display:
                    print(f"\r{display}", end='', flush=True)
                    last_display = display
                    if is_touching:
                        logging.info(f"Position: {value}")
                    else:
                        logging.info("No touch detected")
            
            time.sleep(0.01)  # Adjust sampling rate as needed
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
        logging.info("Test stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main() 