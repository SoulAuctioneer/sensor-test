#!/usr/bin/env python3

"""
Basic ADC Sensor Test Script
Simple script to continuously read and print values from the ADC sensor.
"""

import sys
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_ads1x15.ads1x15 import Mode

# Check if running in virtual environment
if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
    print("Error: This script should be run within the virtual environment.")
    print("Please run './run.sh'")
    sys.exit(1)

def main():
    """
    Main function that continuously reads and prints sensor values.
    Prints both raw ADC value and voltage.
    """
    try:
        # Initialize I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Create ADC object
        ads = ADS.ADS1115(i2c)
        ads.gain = 1
        ads.mode = Mode.CONTINUOUS
        
        # Create analog input channel
        chan = AnalogIn(ads, ADS.P0)
        
        print("Reading sensor values. Press Ctrl+C to exit.\n")
        print("Raw Value | Voltage")
        print("-" * 20)
        
        while True:
            value = chan.value
            voltage = chan.voltage
            print(f"{value:>8} | {voltage:.6f}V", end='\r')
            time.sleep(0.01)  # 10ms delay
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main() 