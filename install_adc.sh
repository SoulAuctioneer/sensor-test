#!/bin/bash

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip i2c-tools

# Enable I2C interface if not already enabled
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "Enabling I2C interface..."
    sudo sh -c 'echo "dtparam=i2c_arm=on" >> /boot/config.txt'
fi

# Install Python libraries
echo "Installing Python dependencies..."
sudo pip3 install adafruit-blinka
sudo pip3 install adafruit-circuitpython-ads1x15

echo "Installation complete! Please reboot your Raspberry Pi." 