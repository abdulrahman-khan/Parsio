#!/usr/bin/env python3
"""
Launcher script for Parsio application.
This script runs the Core_Application module from the correct context.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
from Core_Application.main import main

if __name__ == "__main__":
    main()
