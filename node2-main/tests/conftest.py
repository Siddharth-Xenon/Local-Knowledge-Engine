import sys
import os

# Add project root to sys.path so we can import 'app'
# This assumes conftest.py is in /tests and project root is one level up
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
