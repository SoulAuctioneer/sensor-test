#!/usr/bin/env python3

"""
ADC Sensor Test Script
Reads analog data from a linear softpot touch sensor connected to channel A0 of ADS1115/ADS1015 ADC
and displays a visual indicator of touch position.
"""

import sys
import asyncio
import logging
import config
from sensor import TouchManager
# from led_manager import AsyncLedManager

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

def get_position_indicator(position):
    """Convert normalized position to a visual indicator
    
    Args:
        position (float): Normalized position (0-1)
        
    Returns:
        str: ASCII visualization of position
    """
    # Convert to position in the display width
    pos = int(position * (config.POSITION_WIDTH - 1))  # Subtract 1 since positions are 0-based
    pos = max(0, min(pos, config.POSITION_WIDTH - 1))  # Clamp to valid range
    
    # Create the visual indicator
    indicator = ['─'] * config.POSITION_WIDTH
    indicator[pos] = '●'
    
    return f"[{''.join(indicator)}]"

class Display:
    """Class to manage the terminal display"""
    def __init__(self):
        self.last_display = ""
        self.is_touching = False
        self.stroke_message = None
        self.stroke_message_time = 0
        self.current_position_display = None  # Store current position display
        self.intensity_level = 0.0
        
    def update_touch(self, is_touching):
        """Handle touch state changes"""
        self.is_touching = is_touching
        if not is_touching:
            self.current_position_display = None
            self.show_display(f"[{'─' * config.POSITION_WIDTH}] (no touch) {self._get_intensity_display()}")
            logging.info("No touch detected")
    
    def update_position(self, position):
        """Handle position updates"""
        if self.is_touching:
            self.current_position_display = get_position_indicator(position)
            display = self.current_position_display
            if self.stroke_message:
                display = f"{display} {self.stroke_message}"
            display = f"{display} {self._get_intensity_display()}"
            self.show_display(display)
    
    def update_stroke(self, direction):
        """Handle stroke detection"""
        self.stroke_message = f"Stroke: {direction}!"
        logging.info(f"Stroke detected: {direction}")
        # Show stroke message immediately with last known position display
        if self.current_position_display:
            self.show_display(f"{self.current_position_display} {self.stroke_message} {self._get_intensity_display()}")
        else:
            self.show_display(f"[{'─' * config.POSITION_WIDTH}] {self.stroke_message} {self._get_intensity_display()}")
    
    def update_intensity(self, level):
        """Handle intensity level updates"""
        self.intensity_level = level
        # Update display with new intensity level
        if self.current_position_display:
            display = self.current_position_display
            if self.stroke_message:
                display = f"{display} {self.stroke_message}"
            display = f"{display} {self._get_intensity_display()}"
            self.show_display(display)
        else:
            self.show_display(f"[{'─' * config.POSITION_WIDTH}] (no touch) {self._get_intensity_display()}")
    
    def _get_intensity_display(self):
        """Get visual representation of intensity level"""
        meter_width = 10  # Width of intensity meter
        filled = int(self.intensity_level * meter_width)
        return f"Intensity: [{('█' * filled) + ('░' * (meter_width - filled))}]"
    
    def show_display(self, display):
        """Update the terminal display if changed"""
        if display != self.last_display:
            print(f"\r{display}", end='', flush=True)
            self.last_display = display

async def main():
    """Main async function to run the sensor interface"""
    print("\nLinear Softpot Touch Sensor")
    print("Left" + " " * (config.POSITION_WIDTH - 2) + "Right")
    print("\nTouch the sensor to see position...\n")
    
    sensor = None
    led_manager = None
    try:
        sensor = TouchSensor()
        display = Display()
        
        # Initialize and start LED manager
        # led_manager = AsyncLedManager()
        # await led_manager.start_rainbow()
        
        # Register callbacks
        sensor.on_touch(display.update_touch)
        sensor.on_position(display.update_position)
        sensor.on_stroke(display.update_stroke)
        sensor.on_intensity(display.update_intensity)
        
        # Start the sensor and wait for Ctrl+C
        await sensor.start()
        
    except KeyboardInterrupt:
        print("\nTest stopped by user")
        logging.info("Test stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
    finally:
        if sensor:
            sensor.stop()
            # Give the sensor loop time to clean up
            await asyncio.sleep(0.1)
        # if led_manager:
        #     await led_manager.stop()
        #     await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This catches Ctrl+C at the top level
        pass 