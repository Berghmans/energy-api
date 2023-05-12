"""Main module for running the test suite"""
import unittest
import logging
import sys

import tests.test_dao

logging.disable(logging.CRITICAL)  # Disable logging
suite = unittest.TestSuite()
# Add all tests 'manually'
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.test_dao))
# Run the test suite
results = unittest.TextTestRunner().run(suite)
sys.exit(not results.wasSuccessful())
