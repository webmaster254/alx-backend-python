# Unittests and Integration Tests

This project demonstrates how to implement unit tests and integration tests in Python, focusing on parameterized tests, mock objects, fixtures, and proper test organization. The tests follow the PEP 8 style guide (enforced by pycodestyle 2.5).

## Overview

The project contains tests for utility functions and a GitHub client implementation, showcasing various testing techniques:

1. **Parameterized testing**: Using the `parameterized` package to run the same test with different inputs
2. **Mocking**: Using `unittest.mock` to isolate code from external dependencies 
3. **Patching**: Replacing functions/methods/properties during testing
4. **Fixtures**: Using test fixtures for consistent test data
5. **Integration tests**: Testing components working together while mocking external systems

## Files Structure

- `utils.py`: Utility functions to be tested
  - `access_nested_map`: Navigates nested dictionaries using a sequence of keys
  - `get_json`: Fetches JSON data from a URL
  - `memoize`: Decorator that caches method results

- `client.py`: GitHub organization client implementation
  - `GithubOrgClient`: Client for accessing GitHub organization data

- `test_utils.py`: Unit tests for utility functions
  - `TestAccessNestedMap`: Tests for the access_nested_map function
  - `TestGetJson`: Tests for the get_json function
  - `TestMemoize`: Tests for the memoize decorator

- `test_client.py`: Unit and integration tests for the GitHub client
  - `TestGithubOrgClient`: Unit tests for GithubOrgClient class
  - `TestIntegrationGithubOrgClient`: Integration tests using parameterized fixtures

- `fixtures.py`: Test fixtures for the integration tests

## Testing Techniques Demonstrated

### Parameterized Testing
```python
@parameterized.expand([
    ({"a": 1}, ("a",), 1),
    ({"a": {"b": 2}}, ("a",), {"b": 2}),
    ({"a": {"b": 2}}, ("a", "b"), 2),
])
def test_access_nested_map(self, nested_map, path, expected):
    """Test that access_nested_map returns the expected result"""
    self.assertEqual(access_nested_map(nested_map, path), expected)
```

### Mocking HTTP Requests
```python
@patch('requests.get')
def test_get_json(self, mock_get):
    """Test that get_json returns the expected result"""
    mock_response = Mock()
    mock_response.json.return_value = test_payload
    mock_get.return_value = mock_response
    
    result = get_json(test_url)
    
    mock_get.assert_called_once_with(test_url)
    self.assertEqual(result, test_payload)
```

### Testing Properties with PropertyMock
```python
with patch('client.GithubOrgClient.org', 
           new_callable=PropertyMock) as mock_org:
    mock_org.return_value = payload
    repos_url = org_client._public_repos_url
    self.assertEqual(repos_url, expected_url)
```

### Integration Testing with Fixtures
```python
@parameterized_class(
    ('org_payload', 'repos_payload', 'expected_repos', 'apache2_repos'),
    TEST_PAYLOAD
)
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration tests for GithubOrgClient class"""
    
    @classmethod
    def setUpClass(cls):
        """Set up for the integration tests"""
        # Mock setup code here
```

## Running the Tests

To run the tests, use the unittest framework:

```bash
python -m unittest test_utils.py
python -m unittest test_client.py
```

Or run all tests:

```bash
python -m unittest discover
```

## Style Compliance

All code and tests comply with PEP 8 style guide, as enforced by pycodestyle 2.5:

```bash
pycodestyle test_utils.py
pycodestyle test_client.py
```

## Author

ALX SE Program - Back-End Python Curriculum
