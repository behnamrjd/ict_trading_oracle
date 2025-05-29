"""
ICT Trading Oracle Bot Package
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Ensure core modules are importable
core_dir = os.path.join(current_dir, 'core')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

config_dir = os.path.join(current_dir, 'config')
if config_dir not in sys.path:
    sys.path.insert(0, config_dir)