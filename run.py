#!/usr/bin/env python3
"""
Entry point for the Kicktipp Bot.

This script can be run directly from the root directory to start the bot.
"""

import sys
import os

# Add the src directory to Python path so we can import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    from kicktipp_bot.main import main
    main()
