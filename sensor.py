"""
Core sensor functionality for reading and processing touch sensor data.
"""

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import logging
import config

class StrokeDetector:
    """Class to detect stroking motions on the touch sensor"""
    def __init__(self):
        self.touch_history = []  # List of (timestamp, position) tuples
        self.last_stroke_time = 0
        self.was_touching = False  # Track previous touch state
        self.pending_stroke = None  # Store detected stroke until next touch
        self.touch_start_time = None  # Track when the current touch started
        
    def add_point(self, value, is_touching):
        """Add a touch point to history and check for stroke on release
        
        Args:
            value (int): Raw sensor value
            is_touching (bool): Current touch state
            
        Returns:
            tuple: (bool: stroke detected, str: stroke direction if detected) or (False, None)
        """
        now = time.time()
        
        # Handle touch state transition
        if is_touching != self.was_touching:
            if self.was_touching and not is_touching:  # Finger lifted
                # Check for stroke only when finger is lifted
                if len(self.touch_history) >= config.MIN_STROKE_POINTS:
                    self.pending_stroke = self._check_stroke()
            else:  # New touch started
                self.touch_start_time = now
                self.pending_stroke = None
            
            # Only clear history when starting a new touch
            if is_touching:
                self.touch_history = []
            self.was_touching = is_touching
            
            # Return pending stroke detection if finger was just lifted
            if self.pending_stroke:
                result = self.pending_stroke
                self.pending_stroke = None
                return result
            return False, None
            
        # Only add points while touching
        if not is_touching:
            return False, None
            
        # Convert value to normalized position (0 to 1)
        position = ((value - config.LEFT_MIN) / (config.RIGHT_MAX - config.LEFT_MIN))
        logging.debug(f"Normalized position: {position:.3f} from value: {value}")
        position = max(0, min(position, 1.0))  # Clamp to valid range
        
        # Add point with timestamp
        self.touch_history.append((now, position))
        
        return False, None
    
    def _check_stroke(self):
        """Internal method to check if the completed touch was a stroke
        
        Returns:
            tuple: (bool: stroke detected, str: stroke direction if detected)
        """
        # Keep history in chronological order (should already be since we append in order)
        history = list(self.touch_history)  # Make a copy to avoid modifying original
        times = []
        positions = []
        for t, p in history:
            times.append(t)
            positions.append(p)
            
        # Log raw positions for debugging
        logging.info(f"Raw positions: {[f'{p:.3f}' for p in positions]}")
        
        # Trim inconsistent readings at the end (lift-off artifacts)
        original_len = len(positions)
        if len(positions) >= 3:
            # Look for sudden direction changes or large jumps at the end
            for i in range(len(positions)-2, max(0, len(positions)-10), -1):  # Only check last 10 points
                # Calculate differences between consecutive points
                diff1 = positions[i] - positions[i-1]  # Direction of movement
                diff2 = positions[i+1] - positions[i]  # Direction of next movement
                
                # If direction suddenly changes significantly or there's a large jump
                if (abs(diff2) > 0.4 or  # Large position jump (40% of sensor range)
                    (abs(diff1) > 0.05 and abs(diff2) > 0.05 and  # Both movements are significant (5%)
                     diff1 * diff2 < 0)):  # Direction changed
                    # Trim the history to remove lift-off artifacts
                    times = times[:i+1]
                    positions = positions[:i+1]
                    logging.info(f"Trimmed {original_len - len(positions)} points from end of stroke")
                    break
        
        if len(positions) < config.MIN_STROKE_POINTS:
            logging.info(f"Not enough points for stroke: {len(positions)} < {config.MIN_STROKE_POINTS}")
            return False, None
            
        # Calculate total distance and time
        total_distance = abs(positions[-1] - positions[0])
        logging.info(f"First position: {positions[0]:.3f}, Last position: {positions[-1]:.3f}, Distance: {total_distance:.3f}")
        total_time = times[-1] - times[0]
        
        if total_time == 0:  # Avoid division by zero
            logging.info("Zero time duration for stroke")
            return False, None
            
        # Calculate speed in position units per second
        speed = total_distance / total_time
        
        # Determine dominant direction using regression
        direction = self.calculate_stroke_direction(positions)
        if not direction:
            logging.info("Could not determine stroke direction")
            return False, None
            
        # Check if motion is mostly monotonic in the determined direction
        is_monotonic = self.is_mostly_monotonic(positions, direction)
        
        # Log stroke detection criteria
        logging.info(f"Stroke check - Distance: {total_distance:.3f}, Speed: {speed:.3f}, Direction: {direction}, Monotonic: {is_monotonic}")
        
        # Check if stroke criteria are met and enough time has passed since last stroke
        now = time.time()
        if not (total_distance >= config.MIN_STROKE_DISTANCE):
            logging.info(f"Distance too small: {total_distance:.3f} < {config.MIN_STROKE_DISTANCE}")
        if not is_monotonic:
            logging.info("Movement not monotonic enough")
        if not (speed >= config.MIN_STROKE_SPEED):
            logging.info(f"Speed too low: {speed:.3f} < {config.MIN_STROKE_SPEED}")
        if not (now - self.last_stroke_time >= config.STROKE_TIME_WINDOW):
            logging.info(f"Too soon after last stroke: {now - self.last_stroke_time:.3f}s < {config.STROKE_TIME_WINDOW}s")
            
        if (total_distance >= config.MIN_STROKE_DISTANCE and 
            is_monotonic and 
            speed >= config.MIN_STROKE_SPEED and
            now - self.last_stroke_time >= config.STROKE_TIME_WINDOW):
            self.last_stroke_time = now
            return True, direction
            
        return False, None
    
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
            if abs(diff) > config.DIRECTION_REVERSAL_TOLERANCE:
                if (diff * expected_sign) < 0:
                    reversals += 1
        
        # Allow some reversals but ensure overall motion is in correct direction
        return reversals <= len(positions) // 4

class TouchState:
    """Class to track touch state with hysteresis"""
    def __init__(self):
        self.is_touching = False
        self.last_value = 0
        self.stable_count = 0
    
    def update(self, value):
        """Update touch state with hysteresis to prevent rapid switching
        
        Args:
            value (int): Raw sensor value
            
        Returns:
            bool: True if touching, False if not
        """
        # Check if value has changed significantly from last reading
        if value < config.NO_TOUCH_THRESHOLD:
            self.stable_count += 1
        else:
            self.stable_count = 0
        
        self.last_value = value
        
        # Update touch state with hysteresis
        if not self.is_touching:
            if value >= config.NO_TOUCH_THRESHOLD:
                self.is_touching = True
                self.stable_count = 0
        else:
            if value < config.NO_TOUCH_THRESHOLD and self.stable_count >= 2:
                self.is_touching = False
                self.stable_count = 0
        
        return self.is_touching

class TouchSensor:
    """Main class for interacting with the touch sensor"""
    def __init__(self):
        self.ads, self.chan = self._setup_adc()
        self.touch_state = TouchState()
        self.stroke_detector = StrokeDetector()
        
    def _setup_adc(self):
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
            
            ads.gain = 1
            return ads, chan
        except Exception as e:
            logging.error(f"Failed to initialize ADC: {str(e)}")
            raise
            
    def read(self):
        """Read and process the current sensor state
        
        Returns:
            tuple: (value, is_touching, stroke_detected, stroke_direction)
        """
        try:
            value = self.chan.value
            is_touching = self.touch_state.update(value)
            stroke_detected, direction = self.stroke_detector.add_point(value, is_touching)
            return value, is_touching, stroke_detected, direction
        except Exception as e:
            logging.error(f"Error reading sensor: {str(e)}")
            return None, False, False, None 