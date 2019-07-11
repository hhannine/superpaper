"""Define paths used by Superpaper."""

import os
import sys

# Set path to binary / script
if getattr(sys, 'frozen', False):
    PATH = os.path.dirname(os.path.dirname(os.path.realpath(sys.executable)))
else:
    PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Derivative paths
TEMP_PATH = PATH + "/temp/"
if not os.path.isdir(TEMP_PATH):
    os.mkdir(TEMP_PATH)
PROFILES_PATH = PATH + "/profiles/"
