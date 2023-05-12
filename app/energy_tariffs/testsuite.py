"""Main module for running the test suite"""
import unittest
import logging
import sys
import os

import tests.test_dao
import tests.test_engie_feeder
import tests.test_api
import tests.test_api_methods

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
logging.disable(logging.CRITICAL)  # Disable logging
suite = unittest.TestSuite()
# Add all tests 'manually'
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.test_dao))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.test_engie_feeder))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.test_api))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.test_api_methods))
# Run the test suite
results = unittest.TextTestRunner().run(suite)
sys.exit(not results.wasSuccessful())
