"""Main module for running the test suite"""
import unittest
import logging
import sys
import os

import tests.test_dao

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
logging.disable(logging.CRITICAL)  # Disable logging
suite = unittest.TestSuite()
# Add all tests 'manually'
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.test_dao))
# Run the test suite
results = unittest.TextTestRunner().run(suite)
sys.exit(not results.wasSuccessful())
