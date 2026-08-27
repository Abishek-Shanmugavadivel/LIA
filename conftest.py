import sys
import os

# Guarantee project root is at the front of sys.path for pytest
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
