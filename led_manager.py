"""
Asynchronous LED Manager for controlling NeoPixel LED patterns.
Provides a clean async interface for LED animations with adjustable parameters.
"""

import asyncio
import colorsys
import logging
from typing import Optional

try:
    import board
    import neopixel
    LEDS_AVAILABLE = True
    logging.info("LED libraries available. Will use LEDs")
except (ImportError, NotImplementedError) as e:
    LEDS_AVAILABLE = False
    logging.error(f"LED libraries not available: {str(e)}")
    logging.info("Won't use LEDs")

from config import LED_PIN, LED_COUNT, LED_BRIGHTNESS, LED_ORDER


class AsyncLedManager:
    """
    Asynchronous LED Manager for controlling NeoPixel LED patterns.
    Provides real-time control over LED animations with adjustable parameters.
    """
    
    def __init__(self):
        """Initialize the LED manager with default settings."""
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._brightness = LED_BRIGHTNESS
        self._speed = 1.0  # Default speed multiplier
        
        # Initialize NeoPixel object
        if LEDS_AVAILABLE:
            try:
                pin = getattr(board, f'D{LED_PIN}') if hasattr(board, f'D{LED_PIN}') else LED_PIN
                logging.info(f"Using LED pin: {pin}")
                self.pixels = neopixel.NeoPixel(
                    pin,
                    LED_COUNT,
                    brightness=self._brightness,
                    auto_write=False,
                    pixel_order=LED_ORDER
                )
                logging.info(f"NeoPixel initialized successfully on pin {LED_PIN} with {LED_COUNT} LEDs")
            except Exception as e:
                logging.error(f"Failed to initialize NeoPixels: {str(e)}")
                LEDS_AVAILABLE = False
                logging.info("Falling back to mock pixels")
        else:
            # Mock pixels for non-Raspberry Pi platforms
            class MockPixels:
                def __init__(self, num_pixels):
                    self.n = num_pixels
                    self._pixels = [(0, 0, 0)] * num_pixels
                    self.brightness = LED_BRIGHTNESS

                def __setitem__(self, index, color):
                    self._pixels[index] = color

                def __getitem__(self, index):
                    return self._pixels[index]

                def fill(self, color):
                    self._pixels = [color] * self.n

                def show(self):
                    pass

            self.pixels = MockPixels(LED_COUNT)
            logging.info(f"Mock NeoPixel initialized with {LED_COUNT} LEDs")

    def clear(self):
        """Turn off all LEDs."""
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    async def start_rainbow(self):
        """
        Start the rainbow rotation effect.
        If already running, this will have no effect.
        """
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._rainbow_effect())

    async def stop(self):
        """
        Stop the current LED effect and clear the LEDs.
        """
        self._running = False
        if self._task:
            await self._task
            self._task = None
        self.clear()

    def set_parameters(self, brightness: Optional[float] = None, speed: Optional[float] = None):
        """
        Update the LED animation parameters in real-time.
        
        Args:
            brightness: Float between 0.0 and 1.0 for LED brightness
            speed: Float > 0, where 1.0 is normal speed, 2.0 is twice as fast, etc.
        """
        if brightness is not None:
            self._brightness = max(0.0, min(1.0, brightness))
            if LEDS_AVAILABLE:
                self.pixels.brightness = self._brightness
        
        if speed is not None:
            self._speed = max(0.1, speed)  # Prevent speed from being too slow

    async def _rainbow_effect(self):
        """
        Generate a rotating rainbow effect across all pixels.
        The effect speed and brightness can be modified in real-time.
        """
        position = 0.0
        base_delay = 0.02  # Base delay between updates in seconds
        
        while self._running:
            # Calculate positions for all LEDs
            for i in range(LED_COUNT):
                # Calculate hue for this pixel
                hue = (i / LED_COUNT) + position
                hue = hue % 1.0
                
                # Convert HSV to RGB
                r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
                self.pixels[i] = (r, g, b)
            
            self.pixels.show()
            
            # Update position for next frame
            position = (position + 0.01) % 1.0
            
            # Adjust delay based on speed setting
            await asyncio.sleep(base_delay / self._speed)


# Example usage
async def main():
    led = AsyncLedManager()
    try:
        # Start rainbow effect
        await led.start_rainbow()
        
        # Run for 5 seconds at normal speed
        await asyncio.sleep(5)
        
        # Double the speed
        led.set_parameters(speed=2.0)
        await asyncio.sleep(5)
        
        # Reduce brightness to 50%
        led.set_parameters(brightness=0.5)
        await asyncio.sleep(5)
        
        # Stop the effect
        await led.stop()
        
    except KeyboardInterrupt:
        await led.stop()

if __name__ == "__main__":
    asyncio.run(main()) 