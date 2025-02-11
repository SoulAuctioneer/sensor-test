"""
Configuration parameters for the ADC Sensor Test Script
"""

# Softpot calibration values
LEFT_MIN = 8800   # Minimum value (far left)
RIGHT_MAX = 17000   # Maximum value (far right)
POSITION_WIDTH = 40  # Width of the visual indicator in characters

# Touch detection thresholds
NO_TOUCH_THRESHOLD = 5500  # Values below this indicate no touch
NOISE_WINDOW = 50        # Ignore value changes smaller than this when not touching

# Stroke detection parameters
STROKE_TIME_WINDOW = 0.5     # Time window to detect stroke (seconds)
MIN_STROKE_DISTANCE = 0.2    # Minimum distance (as percentage) to consider a stroke
MIN_STROKE_POINTS = 5        # Minimum number of touch points to consider a stroke
MIN_STROKE_SPEED = 0.25      # Minimum speed (position units per second)
DIRECTION_REVERSAL_TOLERANCE = 0.05  # Tolerance for small direction reversals

# Intensity tracking parameters
INTENSITY_DECAY_RATE = 0.03   # Level lost per second
INTENSITY_SPEED_FACTOR = 2.2  # Higher speeds reduce intensity gain (divisor)
INTENSITY_DISTANCE_FACTOR = 1.0  # Multiplier for distance contribution

# Sampling configuration
SAMPLE_RATE_HZ = 100  # Default sampling rate in Hz

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(message)s'
LOG_FILE = 'sensor_readings.log' 