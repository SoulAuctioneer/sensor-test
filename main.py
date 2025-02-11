#!/usr/bin/env python3

"""
ADC Sensor Test Script
Reads analog data from a linear softpot touch sensor connected to channel A0 of ADS1115/ADS1015 ADC
and displays a visual indicator of touch position.
"""

import sys
import time
import logging
import config
from sensor import TouchSensor

# Check if running in virtual environment
if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
    print("Error: This script should be run within the virtual environment.")
    print("Please run './run.sh'")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_position_indicator(value, is_touching):
    """Convert sensor value to a visual position indicator
    
    Args:
        value (int): Raw sensor value
        is_touching (bool): Current touch state
        
    Returns:
        str: ASCII visualization of touch position
    """
    # Only show position if actually touching and value is in valid range
    if not is_touching or value < config.NO_TOUCH_THRESHOLD or (value > config.NO_TOUCH_THRESHOLD and value < config.LEFT_MIN):
        return f"[{'─' * config.POSITION_WIDTH}] (no touch)"
    
    # Handle values outside calibrated range but still indicating touch
    if value > config.RIGHT_MAX:
        value = config.RIGHT_MAX
    
    # Calculate position as percentage (0 to 1) where 0 is left and 1 is right
    position = ((value - config.LEFT_MIN) / (config.RIGHT_MAX - config.LEFT_MIN))
    
    # Convert to position in the display width (ensure within bounds)
    pos = int(position * (config.POSITION_WIDTH - 1))  # Subtract 1 since positions are 0-based
    pos = max(0, min(pos, config.POSITION_WIDTH - 1))  # Clamp to valid range
    
    # Create the visual indicator
    indicator = ['─'] * config.POSITION_WIDTH
    indicator[pos] = '●'
    
    return f"[{''.join(indicator)}]"

def main():
    """Main function to continuously read and display touch position"""
    print("\nLinear Softpot Touch Sensor")
    print("Left" + " " * (config.POSITION_WIDTH - 2) + "Right")
    
    try:
        sensor = TouchSensor()
        logging.info("ADC initialized successfully")
        print("\nTouch the sensor to see position...\n")
        
        last_display = ""
        
        while True:
            value, is_touching, stroke_detected, direction = sensor.read()
            
            if value is not None:
                display = get_position_indicator(value, is_touching)
                
                if stroke_detected:
                    logging.info(f"Stroke detected: {direction}")
                    display = f"{display} Stroke: {direction}!"
                
                # Only update display if position changed
                if display != last_display:
                    print(f"\r{display}", end='', flush=True)
                    last_display = display
                    # Log position only if actually touching and in valid range
                    if is_touching and value >= config.RIGHT_MIN:
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