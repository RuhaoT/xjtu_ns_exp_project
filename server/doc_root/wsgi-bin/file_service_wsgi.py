#!/usr/local/bin/python3.12
import sys
import os
import site

# Add the current directory to sys.path
sys.path.append(os.path.dirname(p=__file__))

# Import the Flask app
from file_service_app import app

application = app