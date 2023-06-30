"""Main module for running the test suite"""
import unittest
import logging
import sys
import os

import tests.dao.test_dao
import tests.dao.test_indexingsetting
import tests.dao.test_gridcosts
import tests.feeders.test_engie_feeder
import tests.feeders.test_eex_feeder
import tests.feeders.test_entsoe_feeder
import tests.feeders.test_fluvius_feeder
import tests.test_api
import tests.test_feeder
import tests.api_methods.test_indexing_setting
import tests.api_methods.test_indexing_settings
import tests.api_methods.test_end_price
import tests.api_methods.test_end_prices
import tests.api_methods.test_list
import tests.api_methods.test_grid_cost

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
logging.disable(logging.CRITICAL)  # Disable logging
suite = unittest.TestSuite()
# Add all tests 'manually'
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.dao.test_dao))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.dao.test_indexingsetting))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.dao.test_gridcosts))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.test_api))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.test_feeder))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.feeders.test_engie_feeder))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.feeders.test_eex_feeder))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.feeders.test_entsoe_feeder))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.feeders.test_fluvius_feeder))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.api_methods.test_indexing_setting))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.api_methods.test_indexing_settings))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.api_methods.test_end_price))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.api_methods.test_end_prices))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.api_methods.test_list))
suite.addTests(unittest.TestLoader().loadTestsFromModule(tests.api_methods.test_grid_cost))
# Run the test suite
results = unittest.TextTestRunner().run(suite)
sys.exit(not results.wasSuccessful())
