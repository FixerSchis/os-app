import pytest
import base64
from utils import generate_qr_code, generate_web_qr_code
from unittest.mock import patch, MagicMock

def test_generate_qr_code():
    """Test QR code generation with basic data."""
    data = "https://example.com"
    qr_data_url = generate_qr_code(data)
    
    # Check that it returns a valid data URL
    assert qr_data_url.startswith("data:image/png;base64,")
    
    # Extract the base64 data and decode it
    base64_data = qr_data_url.split(",")[1]
    decoded_data = base64.b64decode(base64_data)
    
    # Check that it's a valid PNG image
    assert decoded_data.startswith(b'\x89PNG\r\n\x1a\n')

def test_generate_qr_code_with_custom_size():
    """Test QR code generation with custom size and border."""
    data = "https://example.com"
    qr_data_url = generate_qr_code(data, size=20, border=4)
    
    # Check that it returns a valid data URL
    assert qr_data_url.startswith("data:image/png;base64,")
    
    # Extract the base64 data and decode it
    base64_data = qr_data_url.split(",")[1]
    decoded_data = base64.b64decode(base64_data)
    
    # Check that it's a valid PNG image
    assert decoded_data.startswith(b'\x89PNG\r\n\x1a\n')

def test_generate_qr_code_with_empty_data():
    """Test QR code generation with empty data."""
    data = ""
    qr_data_url = generate_qr_code(data)
    
    # Check that it returns a valid data URL
    assert qr_data_url.startswith("data:image/png;base64,")
    
    # Extract the base64 data and decode it
    base64_data = qr_data_url.split(",")[1]
    decoded_data = base64.b64decode(base64_data)
    
    # Check that it's a valid PNG image
    assert decoded_data.startswith(b'\x89PNG\r\n\x1a\n')

@patch('utils.url_for')
def test_generate_web_qr_code_success(mock_url_for):
    """Test web QR code generation with successful URL generation."""
    mock_url_for.return_value = "https://example.com/test"
    
    qr_data_url = generate_web_qr_code('test_route', param1='value1')
    
    # Check that url_for was called correctly
    mock_url_for.assert_called_once_with('test_route', param1='value1', _external=True)
    
    # Check that it returns a valid data URL
    assert qr_data_url.startswith("data:image/png;base64,")
    
    # Extract the base64 data and decode it
    base64_data = qr_data_url.split(",")[1]
    decoded_data = base64.b64decode(base64_data)
    
    # Check that it's a valid PNG image
    assert decoded_data.startswith(b'\x89PNG\r\n\x1a\n')

@patch('utils.url_for')
def test_generate_web_qr_code_failure(mock_url_for):
    """Test web QR code generation when URL generation fails."""
    mock_url_for.side_effect = Exception("URL generation failed")
    
    qr_data_url = generate_web_qr_code('test_route')
    
    # Check that it returns None when URL generation fails
    assert qr_data_url is None

@patch('utils.url_for')
def test_generate_web_qr_code_with_parameters(mock_url_for):
    """Test web QR code generation with URL parameters."""
    mock_url_for.return_value = "https://example.com/test/123"
    
    qr_data_url = generate_web_qr_code('test_route', id=123, name='test')
    
    # Check that url_for was called with the correct parameters
    mock_url_for.assert_called_once_with('test_route', id=123, name='test', _external=True)
    
    # Check that it returns a valid data URL
    assert qr_data_url.startswith("data:image/png;base64,") 