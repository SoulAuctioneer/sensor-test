#!/usr/bin/env python3

"""
Simple test script for NeoPixel LEDs.
Tests basic LED functionality with different patterns.
"""

import time
import board
import neopixel
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# LED Configuration
LED_PIN = 10  # GPIO10
LED_COUNT = 24
LED_BRIGHTNESS = 1.0
LED_ORDER = "GRB"

def test_leds():
    """Run through different LED test patterns"""
    try:
        # Initialize the NeoPixel
        logging.info("Initializing NeoPixels...")
        pixels = neopixel.NeoPixel(
            board.D10,  # Using GPIO10
            LED_COUNT,
            brightness=LED_BRIGHTNESS,
            auto_write=False,
            pixel_order=LED_ORDER
        )
        
        logging.info("NeoPixel strip initialized successfully")
        
        # Test 1: All Red
        logging.info("Test 1: All Red")
        pixels.fill((255, 0, 0))
        pixels.show()
        time.sleep(2)
        
        # Test 2: All Green
        logging.info("Test 2: All Green")
        pixels.fill((0, 255, 0))
        pixels.show()
        time.sleep(2)
        
        # Test 3: All Blue
        logging.info("Test 3: All Blue")
        pixels.fill((0, 0, 255))
        pixels.show()
        time.sleep(2)
        
        # Test 4: Chase pattern
        logging.info("Test 4: Chase pattern")
        for i in range(LED_COUNT * 2):
            pixels.fill((0, 0, 0))
            pixels[i % LED_COUNT] = (255, 255, 255)
            pixels.show()
            time.sleep(0.1)
        
        # Test 5: Fade in/out white
        logging.info("Test 5: Fade in/out")
        for brightness in range(0, 100, 2):
            pixels.brightness = brightness / 100.0
            pixels.fill((255, 255, 255))
            pixels.show()
            time.sleep(0.02)
        for brightness in range(100, 0, -2):
            pixels.brightness = brightness / 100.0
            pixels.fill((255, 255, 255))
            pixels.show()
            time.sleep(0.02)
        
        # Clean up
        logging.info("Tests complete, turning off LEDs")
        pixels.fill((0, 0, 0))
        pixels.show()
        
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