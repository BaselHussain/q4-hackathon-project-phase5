"""
Pytest configuration for unit tests.

Loads environment variables from .env file before running tests.
"""
from dotenv import load_dotenv

# Load environment variables before any tests run
load_dotenv()
