#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gradio Web UI Entry Point
Run the Restaurant Assistant as a web interface
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ports.web.gradio_client import launch

if __name__ == "__main__":
    launch()
