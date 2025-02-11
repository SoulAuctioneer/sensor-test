#!/bin/bash

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip i2c-tools python3-venv python3-full

# Enable I2C interface if not already enabled
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "Enabling I2C interface..."
    sudo sh -c 'echo "dtparam=i2c_arm=on" >> /boot/config.txt'
fi

# Remove existing virtual environment if it exists
if [ -d ~/adc_venv ]; then
    echo "Removing existing virtual environment..."
    rm -rf ~/adc_venv
fi

# Create a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv ~/adc_venv

# Create activation script
echo "Creating activation script..."
cat > ~/activate_adc.sh << 'EOF'
#!/bin/bash
source ~/adc_venv/bin/activate
EOF
chmod +x ~/activate_adc.sh

# Source the virtual environment and install packages
echo "Installing Python dependencies..."
source ~/adc_venv/bin/activate
if [ "$VIRTUAL_ENV" != "" ]; then
    pip install --upgrade pip
    pip install adafruit-blinka
    pip install adafruit-circuitpython-ads1x15
else
    echo "Error: Virtual environment activation failed"
    exit 1
fi

echo "Installation complete! Please reboot your Raspberry Pi."
echo "After reboot, run 'source ~/activate_adc.sh' before running the test script." 