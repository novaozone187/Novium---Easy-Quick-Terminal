import pytest
from unittest.mock import MagicMock
from pathlib import Path
import time

# Import the functions to be tested
# Assuming system_monitor.py is correctly structured and testable via imports
from novium.system_monitor import get_system_stats_snapshot, get_temperature, get_fan_rpm, check_browser_installed # Added general utility for completeness

# Mocking external dependencies globally for this module's tests
@pytest.fixture(scope="module")
def mock_psutil_success():
    """Mocks psutil to simulate healthy hardware readings."""
    with MagicMock() as mock_psutil:
        # Mock virtual memory stats
        mock_psutil.virtual_memory.return_value.percent = 45.0
        mock_psutil.virtual_memory.total = 16 * (1024**3)  # 16 GB
        
        # Mock CPU percentage
        mock_psutil.cpu_percent.side_effect = [10.0, 15.0] # Simulate multiple calls if needed

        # Mock sensor functions
        class MockSensors:
            def __init__(self):
                self.sensors_temperatures = {
                    "core": [{"label": "Core", "current": 45.0}],
                    "gpu": [{"label": "GPU", "current": 60.0}]
                }
                self.sensors_fans = {
                    "cpu_fan": [{"label": "CPU Fan", "current": 1200}]
                }

        mock_psutil.sensors_temperatures.return_value = MockSensors.sensors_temperatures
        mock_psutil.sensors_fans.return_value = MockSensors.sensors_fans
        
        # Set the mock module globally for the test scope
        print("Mocking psutil success.")
        yield mock_psutil

@pytest.fixture(scope="module")
def mock_disk_usage():
    """Mocks shutil.disk_usage to simulate disk space."""
    with MagicMock() as mock_shutil:
        mock_shutil.disk_usage.return_value = MagicMock(free=256 * (1024**3)) # 256 GB free
        print("Mocking shutil.disk_usage.")
        yield mock_shutil

def test_get_system_stats_snapshot_success(mock_psutil_success, mock_disk_usage):
    """Tests snapshot gathering when psutil and disk usage are successful."""
    # We need to pass the mocked psutil object (which is available through mock_psutil_success fixture)
    from novium.system_monitor import get_system_stats_snapshot 

    # Since the function expects a psutil-like object, we pass the module reference captured by the fixture scope.
    result = get_system_stats_snapshot(mock_psutil_success) 
    
    assert result["CPU"] == "15.0%" # Checking for the second mock call value
    assert result["Memory"].startswith("45.0%")
    assert result["Disk Free"] == "256.0 GB"
    # Check if temperature and fan are correctly formatted strings from mocks
    assert isinstance(result["Temperature"], str) 

def test_get_system_stats_snapshot_failure(mock_psutil_success, mock_disk_usage):
    """Tests snapshot gathering when psutil fails."""
    with MagicMock() as mock_psutil_fail:
        # Simulate failure by making required methods raise an exception
        mock_psutil_fail.cpu_percent.side_effect = Exception("Failed to read CPU")
        
        from novium.system_monitor import get_system_stats_snapshot 
        result = get_system_stats_snapshot(mock_psutil_fail) 
        
        assert result["CPU"] == "Error"

def test_get_temperature_success():
    """Tests temperature reading when psutil is mocked successfully."""
    # This relies on the mock set up by mock_psutil_success fixture (or equivalent setup)
    from novium.system_monitor import get_temperature 
    mock_psutil = MagicMock() # Simple mock for standalone function test
    
    # Mock the attribute check to ensure it doesn't fail immediately
    setattr(mock_psutil, 'sensors_temperatures', {'core': [{'label': 'Core', 'current': 50.0}]})
    
    result = get_temperature(mock_psutil)
    assert result == "50.0C"

def test_get_fan_rpm_success():
    """Tests fan speed reading when psutil is mocked successfully."""
    from novium.system_monitor import get_fan_rpm
    mock_psutil = MagicMock() 
    
    setattr(mock_psutil, 'sensors_fans', {'cpu_fan': [{'label': 'CPU Fan', 'current': 1500}]})
    
    result = get_fan_rpm(mock_psutil)
    assert result == "1500 RPM"

def test_get_temperature_failure():
    """Tests temperature reading when psutil fails."""
    from novium.system_monitor import get_temperature 
    mock_psutil = MagicMock()
    # Ensure the mock has no sensors, simulating failure
    setattr(mock_psutil, 'sensors_temperatures', {}) 

    result = get_temperature(mock_psutil)
    assert result == 'N/A'