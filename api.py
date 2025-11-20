#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FastAPI Server Entry Point
Run the Restaurant Assistant as a REST API
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ports.web.api import run_server

if __name__ == "__main__":
    run_server()
