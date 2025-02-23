#!/bin/bash

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip i2c-tools python3-venv python3-full

# Additional dependencies for NeoPixel
echo "Installing NeoPixel dependencies..."
sudo apt-get install -y gcc make build-essential python3-dev git scons swig

# Enable I2C interface if not already enabled
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "Enabling I2C interface..."
    sudo sh -c 'echo "dtparam=i2c_arm=on" >> /boot/config.txt'
fi

# Enable SPI interface if not already enabled
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
    echo "Enabling SPI interface..."
    sudo sh -c 'echo "dtparam=spi=on" >> /boot/config.txt'
fi

# Add current user to gpio and spi groups
echo "Adding user to required groups..."
sudo usermod -a -G gpio,spi $USER

# Remove existing virtual environment if it exists
if [ -d .venv ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv

# Set permissions on scripts
chmod +x ./run.sh
chmod +x ./reload.sh

# Source the virtual environment and install packages
echo "Installing Python dependencies..."
source .venv/bin/activate
if [ "$VIRTUAL_ENV" != "" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Error: Virtual environment activation failed"
    exit 1
fi

echo "Installation complete! Please reboot your Raspberry Pi."
echo "After reboot, run './run.sh' to start the test script."
echo "Note: Connect the NeoPixel data line to GPIO10 to keep audio functionality enabled." 