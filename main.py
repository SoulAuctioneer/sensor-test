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
LEFT_MAX = 17000   # Maximum value (far left)
RIGHT_MIN = 8800   # Minimum value (far right)
POSITION_WIDTH = 40  # Width of the visual indicator in characters

# Touch detection thresholds
NO_TOUCH_THRESHOLD = 5500  # Values below this indicate no touch
NOISE_WINDOW = 50        # Ignore value changes smaller than this when not touching

# Stroke detection parameters
STROKE_TIME_WINDOW = 0.5     # Time window to detect stroke (seconds)
MIN_STROKE_DISTANCE = 0.3    # Minimum distance (as percentage) to consider a stroke
MIN_STROKE_POINTS = 5        # Minimum number of touch points to consider a stroke
MIN_STROKE_SPEED = 0.5       # Minimum speed (position units per second)
DIRECTION_REVERSAL_TOLERANCE = 0.05  # Tolerance for small direction reversals

class StrokeDetector:
    """Class to detect stroking motions on the touch sensor"""
    def __init__(self):
        self.touch_history = []  # List of (timestamp, position) tuples
        self.last_stroke_time = 0
        
    def add_point(self, value):
        """Add a touch point to history
        
        Args:
            value (int): Raw sensor value
        """
        # Convert value to normalized position (0 to 1)
        position = 1.0 - ((value - RIGHT_MIN) / (LEFT_MAX - RIGHT_MIN))
        position = max(0, min(position, 1.0))  # Clamp to valid range
        
        # Add point with timestamp
        now = time.time()
        self.touch_history.append((now, position))
        
        # Remove old points outside time window
        cutoff_time = now - STROKE_TIME_WINDOW
        self.touch_history = [(t, p) for t, p in self.touch_history if t >= cutoff_time]
    
    def calculate_stroke_direction(self, positions):
        """Calculate the dominant direction of movement using linear regression
        
        Args:
            positions: List of position values
            
        Returns:
            str: "right" or "left" based on dominant direction
        """
        if len(positions) < 2:
            return None
            
        # Use simple linear regression to find trend
        x = list(range(len(positions)))
        y = positions
        n = len(positions)
        
        # Calculate slope using least squares
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        if denominator == 0:
            return None
            
        slope = numerator / denominator
        return "right" if slope > 0 else "left"
    
    def is_mostly_monotonic(self, positions, direction):
        """Check if movement is mostly monotonic with some tolerance for reversals
        
        Args:
            positions: List of position values
            direction: Expected direction ("right" or "left")
            
        Returns:
            bool: True if movement is mostly monotonic
        """
        reversals = 0
        expected_sign = 1 if direction == "right" else -1
        
        for i in range(1, len(positions)):
            diff = positions[i] - positions[i-1]
            # Only count significant reversals
            if abs(diff) > DIRECTION_REVERSAL_TOLERANCE:
                if (diff * expected_sign) < 0:
                    reversals += 1
        
        # Allow some reversals but ensure overall motion is in correct direction
        return reversals <= len(positions) // 4
    
    def detect_stroke(self):
        """Detect if a stroking motion occurred in the recent touch history
        
        Returns:
            tuple: (bool: stroke detected, str: stroke direction if detected)
        """
        if len(self.touch_history) < MIN_STROKE_POINTS:
            return False, None
            
        # Get positions and times in chronological order
        sorted_history = sorted(self.touch_history)
        times = [t for t, _ in sorted_history]
        positions = [p for _, p in sorted_history]
        
        # Calculate total distance and time
        total_distance = abs(positions[-1] - positions[0])
        total_time = times[-1] - times[0]
        
        if total_time == 0:  # Avoid division by zero
            return False, None
            
        # Calculate speed in position units per second
        speed = total_distance / total_time
        
        # Determine dominant direction using regression
        direction = self.calculate_stroke_direction(positions)
        if not direction:
            return False, None
            
        # Check if motion is mostly monotonic in the determined direction
        is_monotonic = self.is_mostly_monotonic(positions, direction)
        
        # Check if stroke criteria are met
        now = time.time()
        if (total_distance >= MIN_STROKE_DISTANCE and 
            is_monotonic and 
            speed >= MIN_STROKE_SPEED and
            now - self.last_stroke_time >= STROKE_TIME_WINDOW):
            self.last_stroke_time = now
            return True, direction
            
        return False, None

class TouchState:
    """Class to track touch state with hysteresis"""
    def __init__(self):
        self.is_touching = False
        self.last_value = 0
        self.stable_count = 0
    
    def update(self, value):
        """Update touch state with hysteresis to prevent rapid switching
        
        Args:
            value (int): Current sensor value
            
        Returns:
            bool: True if touching, False if not
        """
        # Check if value has changed significantly from last reading
        if abs(value - self.last_value) < NOISE_WINDOW and value < NO_TOUCH_THRESHOLD:
            self.stable_count += 1
        else:
            self.stable_count = 0
        
        self.last_value = value
        
        # Update touch state with hysteresis
        if not self.is_touching:
            if value >= NO_TOUCH_THRESHOLD:
                self.is_touching = True
                self.stable_count = 0
        else:
            if value < NO_TOUCH_THRESHOLD and self.stable_count >= 3:
                self.is_touching = False
                self.stable_count = 0
        
        return self.is_touching

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

def get_position_indicator(value, touch_state):
    """Convert sensor value to a visual position indicator
    
    Args:
        value (int): Raw sensor value
        touch_state (TouchState): Current touch state tracker
        
    Returns:
        tuple: (str: ASCII visualization of touch position, bool: is_touching)
    """
    is_touching = touch_state.update(value)
    
    if not is_touching:
        # Show empty bar when not touched
        return f"[{'─' * POSITION_WIDTH}] (no touch)", False
    
    # Handle values outside calibrated range but still indicating touch
    if value > LEFT_MAX:
        value = LEFT_MAX
    elif value < RIGHT_MIN:
        value = RIGHT_MIN
        
    # Calculate position as percentage (0 to 1) where 0 is left and 1 is right
    position = 1.0 - ((value - RIGHT_MIN) / (LEFT_MAX - RIGHT_MIN))
    
    # Convert to position in the display width (ensure within bounds)
    pos = int(position * (POSITION_WIDTH - 1))  # Subtract 1 since positions are 0-based
    pos = max(0, min(pos, POSITION_WIDTH - 1))  # Clamp to valid range
    
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
        touch_state = TouchState()
        stroke_detector = StrokeDetector()
        
        while True:
            voltage, value = read_sensor(chan)
            
            if voltage is not None:
                display, is_touching = get_position_indicator(value, touch_state)
                
                # Update stroke detection if touching
                if is_touching:
                    stroke_detector.add_point(value)
                    stroke_detected, direction = stroke_detector.detect_stroke()
                    if stroke_detected:
                        logging.info(f"Stroke detected: {direction}")
                        display = f"{display} Stroke: {direction}!"
                
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