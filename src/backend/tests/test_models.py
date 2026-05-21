import pytest
from pydantic import ValidationError

from main import Measurement


def test_valid_measurement():
    m = Measurement(time=1755724982, name="Pool", pH=7.2, cl=1.0, temp=24.6)
    assert m.time == 1755724982
    assert m.name == "Pool"
    assert m.sensorType == "manual"
    assert m.pH == 7.2
    assert m.cl == 1.0
    assert m.temp == 24.6


def test_default_sensor_type():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=20.0)
    assert m.sensorType == "manual"


# --- Boundary tests: pH ---

def test_ph_min():
    m = Measurement(time=1, name="Pool", pH=0.0, cl=1.0, temp=20.0)
    assert m.pH == 0.0


def test_ph_max():
    m = Measurement(time=1, name="Pool", pH=14.0, cl=1.0, temp=20.0)
    assert m.pH == 14.0


def test_ph_below_min():
    with pytest.raises(ValidationError):
        Measurement(time=1, name="Pool", pH=-0.1, cl=1.0, temp=20.0)


def test_ph_above_max():
    with pytest.raises(ValidationError):
        Measurement(time=1, name="Pool", pH=14.1, cl=1.0, temp=20.0)


# --- Boundary tests: chlorine ---

def test_cl_min():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=0.0, temp=20.0)
    assert m.cl == 0.0


def test_cl_max():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=10.0, temp=20.0)
    assert m.cl == 10.0


def test_cl_below_min():
    with pytest.raises(ValidationError):
        Measurement(time=1, name="Pool", pH=7.0, cl=-0.1, temp=20.0)


def test_cl_above_max():
    with pytest.raises(ValidationError):
        Measurement(time=1, name="Pool", pH=7.0, cl=10.1, temp=20.0)


# --- Boundary tests: temperature ---

def test_temp_min():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=5.0)
    assert m.temp == 5.0


def test_temp_max():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=45.0)
    assert m.temp == 45.0


def test_temp_below_min():
    with pytest.raises(ValidationError):
        Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=4.9)


def test_temp_above_max():
    with pytest.raises(ValidationError):
        Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=45.1)


# --- Boundary tests: name ---

def test_valid_name():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=20.0)
    assert m.name == "Pool"


def test_unknown_name():
    with pytest.raises(ValidationError) as exc:
        Measurement(time=1, name="Unknown Pool", pH=7.0, cl=1.0, temp=20.0)
    assert "Unknown pool name: Unknown Pool" in str(exc.value)


# --- Status tests ---

def test_status_valid():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=20.0, status="Some text")
    assert m.status == "Some text"


def test_status_too_long():
    with pytest.raises(ValidationError):
        Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=20.0, status="A" * 501)


def test_status_default():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=20.0)
    assert m.status is None


# --- Rounding tests ---

def test_rounding_to_one_decimal():
    m = Measurement(time=1, name="Pool", pH=7.25, cl=1.0, temp=20.0)
    assert m.pH == 7.2  # Python rounds 7.25 -> 7.2 (banker's rounding)


def test_rounding_temp():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=24.55)
    assert m.temp == 24.6  # Python rounds 24.55 -> 24.6


def test_rounding_cl():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.55, temp=20.0)
    assert m.cl == 1.6  # Python rounds 1.55 -> 1.6
