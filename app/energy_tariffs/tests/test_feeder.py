"""Test module for feeder lambda"""
from unittest import TestCase
from unittest.mock import patch


from lambda_feeder import handler


class TestFeeder(TestCase):
    """Test class for Feeder"""

    def test_handler_none(self):
        """Test the lambda handler"""
        handler({}, {})

    def test_handlers(self):
        """Test the lambda handler"""
        handlers = ["engie", "eex", "entsoe", "fluvius", "excises"]
        for feeder in handlers:
            with patch(f"lambda_feeder.{feeder}_handler") as mock:
                handler({"feed": feeder}, {})
                self.assertEqual(1, mock.call_count, f"Handler for {feeder} not invoked")
