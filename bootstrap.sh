#!/bin/bash

# This script is used to bootstrap the development environment.
# It checks if Python 3.12 is installed and installs it if not.
# It also initializes the virtual environment and installs the required packages.
#
# Important: python3 must be mapped to Python 3.12.X
#
# "Usage: sh bootstrap.sh [python_executable|optional|default=python3]"

# If script is not run as root, exit
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit
fi

MY_PATH=$(dirname "$0")                 # relative
MY_PATH=$(builtin cd "$MY_PATH" && pwd) # absolutized and normalized

# Accept python executable name from script args
PYTHON_EXECUTABLE=${$1:-"python3"}
echo "Using Python executable: $PYTHON_EXECUTABLE"

# Check if Python is installed and python3 is mapped to it
if python3 --version 2>&1 | grep -q "Python $PYTHON_VERSION"; then
    echo "Python $PYTHON_VERSION is installed and mapped to 'python3'."
else
    # Check if Python is installed but not mapped to python3
    if [ -x "$(command -v python$PYTHON_VERSION)" ]; then
        echo "Python $PYTHON_VERSION is installed but not mapped to python3."
        # Optional: Update the symlink for python3 to point to desired version of Python
        ln -sf $(which python$PYTHON_VERSION) /usr/bin/python3
    else
        # Install Python
        echo "Installing Python $PYTHON_VERSION..."

        # Check if the system is running on Ubuntu or RHEL, use the appropriate package manager
        PKG_MANAGER=$( command -v brew || command -v dnf || command -v yum || command -v apt-get || command -v apt )
        # Declare the Python version to be installed
        PYTHON_VERSION=3.12

        # Define the Python version to be installed
        INSTALLABLE_NAME="python${PYTHON_VERSION}"
        # If homebrew, installable name is different
        if [[ $PKG_MANAGER == *"brew"* ]]; then
            INSTALLABLE_NAME="python@${PYTHON_VERSION}"
        fi

        ${PKG_MANAGER} update
        ${PKG_MANAGER} install -y ${INSTALLABLE_NAME}
        # Update the symlink for python3 to point to Python
        ln -sf $(which python$PYTHON_VERSION) /usr/bin/python3
    fi
fi

# Assign permissions to the init and activate scripts
chmod +x ${MY_PATH}/.venv/init.sh
chmod +x ${MY_PATH}/.venv/activate.sh

# Run the init script
. .venv/activate.sh
