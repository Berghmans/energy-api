"""Test module for feeder lambda"""
from unittest import TestCase
from unittest.mock import patch


from lambda_feeder import handler


class TestFeeder(TestCase):
    """Test class for Feeder"""

    def test_handler_none(self):
        """Test the lambda handler"""
        handler({}, {})

    def test_handler_engie(self):
        """Test the lambda handler"""
        with patch("lambda_feeder.engie_handler") as mock:
            handler({"feed": "engie"}, {})
            self.assertEqual(1, mock.call_count)

    def test_handler_eex(self):
        """Test the lambda handler"""
        with patch("lambda_feeder.eex_handler") as mock:
            handler({"feed": "eex"}, {})
            self.assertEqual(1, mock.call_count)

    def test_handler_entsoe(self):
        """Test the lambda handler"""
        with patch("lambda_feeder.entsoe_handler") as mock:
            handler({"feed": "entsoe"}, {})
            self.assertEqual(1, mock.call_count)
