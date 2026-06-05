import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system_monitor import get_system_stats_snapshot, get_temperature, get_fan_rpm


def make_mock_psutil(temps=None, fans=None, cpu=10.0, mem_pct=45.0, mem_total=16 * (1024**3)):
    """Helper to create a properly configured psutil mock."""
    mock = MagicMock()
    mock.cpu_percent.return_value = cpu
    mock.virtual_memory.return_value.percent = mem_pct
    mock.virtual_memory.return_value.total = mem_total

    if temps is not None:
        mock.sensors_temperatures.return_value = temps
    else:
        mock.sensors_temperatures = MagicMock(side_effect=AttributeError)

    if fans is not None:
        mock.sensors_fans.return_value = fans
    else:
        mock.sensors_fans = MagicMock(side_effect=AttributeError)

    return mock


def test_get_system_stats_snapshot_success():
    """Tests snapshot gathering with valid mock data."""
    mock_psutil = make_mock_psutil(
        temps={"core": [MagicMock(label="Core", current=45.0)]},
        fans={"cpu_fan": [MagicMock(label="CPU Fan", current=1200)]}
    )

    with patch('system_monitor.shutil') as mock_shutil:
        mock_disk = MagicMock()
        mock_disk.free = 256 * (1024 ** 3)
        mock_shutil.disk_usage.return_value = mock_disk

        result = get_system_stats_snapshot(mock_psutil)

    assert result["CPU"] == "10.0%"
    assert "45.0%" in result["Memory"]
    assert "256.0 GB" in result["Disk Free"]
    assert result["Temperature"] == "45.0C"
    assert result["Fan RPM"] == "1200 RPM"
    assert "Time" in result


def test_get_system_stats_snapshot_failure():
    """Tests snapshot gathering when psutil raises an exception."""
    mock_psutil = MagicMock()
    mock_psutil.cpu_percent.side_effect = Exception("Failed")

    result = get_system_stats_snapshot(mock_psutil)

    assert result["CPU"] == "Error"
    assert result["Memory"] == "Error"


def test_get_temperature_success():
    """Tests temperature reading with valid mock data."""
    mock_psutil = make_mock_psutil(temps={"core": [MagicMock(label="Core", current=50.0)]})
    result = get_temperature(mock_psutil)
    assert result == "50.0C"


def test_get_temperature_no_sensors():
    """Tests temperature reading when no sensors are available."""
    mock_psutil = make_mock_psutil(temps={})
    result = get_temperature(mock_psutil)
    assert result == "N/A"


def test_get_temperature_missing_attr():
    """Tests temperature reading when psutil lacks sensors_temperatures."""
    mock_psutil = make_mock_psutil()
    del mock_psutil.sensors_temperatures
    result = get_temperature(mock_psutil)
    assert result == "N/A"


def test_get_fan_rpm_success():
    """Tests fan speed reading with valid mock data."""
    mock_psutil = make_mock_psutil(fans={"cpu_fan": [MagicMock(label="CPU Fan", current=1500)]})
    result = get_fan_rpm(mock_psutil)
    assert result == "1500 RPM"


def test_get_fan_rpm_no_sensors():
    """Tests fan reading when no sensors are available."""
    mock_psutil = make_mock_psutil(fans={})
    result = get_fan_rpm(mock_psutil)
    assert result == "N/A"


def test_get_fan_rpm_missing_attr():
    """Tests fan reading when psutil lacks sensors_fans."""
    mock_psutil = make_mock_psutil()
    del mock_psutil.sensors_fans
    result = get_fan_rpm(mock_psutil)
    assert result == "N/A"
