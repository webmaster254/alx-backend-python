#!/usr/bin/env python3
"""Unit tests for utils module"""
import unittest
from parameterized import parameterized
from unittest.mock import patch, Mock
from utils import access_nested_map, get_json


class TestAccessNestedMap(unittest.TestCase):
    """Test case for access_nested_map function"""

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(self, nested_map, path, expected):
        """Test that access_nested_map returns the expected result"""
        self.assertEqual(access_nested_map(nested_map, path), expected)
        
    @parameterized.expand([
        ({}, ("a",), "a"),
        ({"a": 1}, ("a", "b"), "b"),
    ])
    def test_access_nested_map_exception(self, nested_map, path, expected):
        """Test that accessing a nonexistent key raises a KeyError"""
        with self.assertRaises(KeyError) as context:
            access_nested_map(nested_map, path)
        self.assertEqual(str(context.exception), f"'{expected}'")


class TestGetJson(unittest.TestCase):
    """Test case for get_json function"""
    
    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    def test_get_json(self, test_url, test_payload):
        """Test that get_json returns the expected result"""
        # Create a mock response with a json method returning test_payload
        mock_response = Mock()
        mock_response.json.return_value = test_payload
        
        # Patch requests.get to return our mock response
        with patch('requests.get', return_value=mock_response) as mock_get:
            # Call the function under test
            result = get_json(test_url)
            
            # Assert requests.get was called once with the test_url
            mock_get.assert_called_once_with(test_url)
            
            # Assert the result is equal to the test_payload
            self.assertEqual(result, test_payload)


if __name__ == "__main__":
    unittest.main()