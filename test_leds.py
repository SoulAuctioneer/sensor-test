#!/usr/bin/env python3

"""
Simple test script for NeoPixel LEDs.
Tests basic LED functionality with different patterns.
Uses rpi_ws281x library for Raspberry Pi compatibility.
"""

import time
import logging
from rpi_ws281x import PixelStrip, Color

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# LED Configuration
LED_COUNT = 24        # Number of LED pixels
LED_PIN = 10         # GPIO pin connected to the pixels (must support PWM)
LED_FREQ_HZ = 800000 # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10         # DMA channel to use for generating signal
LED_BRIGHTNESS = 255 # Set to 0 for darkest and 255 for brightest
LED_INVERT = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0      # PWM channel to use

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def test_leds():
    """Run through different LED test patterns"""
    try:
        # Initialize the NeoPixel
        logging.info("Initializing NeoPixels...")
        strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        strip.begin()
        
        logging.info("NeoPixel strip initialized successfully")
        
        # Test 1: All Red
        logging.info("Test 1: All Red")
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(255, 0, 0))
        strip.show()
        time.sleep(2)
        
        # Test 2: All Green
        logging.info("Test 2: All Green")
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 255, 0))
        strip.show()
        time.sleep(2)
        
        # Test 3: All Blue
        logging.info("Test 3: All Blue")
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 255))
        strip.show()
        time.sleep(2)
        
        # Test 4: Chase pattern
        logging.info("Test 4: Chase pattern")
        for j in range(LED_COUNT * 2):
            for i in range(strip.numPixels()):
                if i == j % LED_COUNT:
                    strip.setPixelColor(i, Color(255, 255, 255))
                else:
                    strip.setPixelColor(i, Color(0, 0, 0))
            strip.show()
            time.sleep(0.1)
        
        # Test 5: Rainbow cycle
        logging.info("Test 5: Rainbow cycle")
        for j in range(256):
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, wheel((i + j) & 255))
            strip.show()
            time.sleep(0.02)
        
        # Clean up
        logging.info("Tests complete, turning off LEDs")
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        
    except Exception as e:
        logging.error(f"Error during LED test: {str(e)}")
        raise

if __name__ == "__main__":
    logging.info("Starting LED test script")
    try:
        test_leds()
        logging.info("LED test completed successfully")
    except KeyboardInterrupt:
        logging.info("\nTest stopped by user")
    except Exception as e:
        logging.error(f"Test failed: {str(e)}") 