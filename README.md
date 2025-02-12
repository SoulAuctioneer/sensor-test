ADC Sensor Test Script
Reads analog data from a linear softpot touch sensor connected to channel A0 of ADS1115/ADS1015 ADC
Displays a visual indicator of touch position.

Also detects stroking gestures, and tracks intensity over time, for implementing a physical virtual pet.

Installation on a Raspberry Pi:
```
git clone https://github.com/SoulAuctioneer/sensor-test.git
cd sensor-test
chmod +x ./install.sh && ./install.sh
```

Note: I've found that I need to manually enable SPI in the Raspberry Pi OS:
```
sudo raspi-config
```
Select "Interfacing Options" -> "SPI" -> "Yes" -> "Finish" -> "Yes" -> "Reboot"

After rebooting, run the script:
```
cd sensor-test
./run.sh
```

To stop the script, press Ctrl+C.
