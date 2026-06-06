import pytest
from pydantic import ValidationError

from main import Event, Measurement


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


# --- AI fields tests ---

def test_ai_fields_default():
    m = Measurement(time=1, name="Pool", pH=7.0, cl=1.0, temp=20.0)
    assert m.aiPH is None
    assert m.aiCL is None
    assert m.aiImage is None
    assert m.aiCorrected is None


def test_ai_fields_with_values():
    m = Measurement(
        time=1, name="Pool", pH=7.2, cl=1.0, temp=20.0,
        aiPH=7.3, aiCL=1.5, aiImage="2026-05-29/123456_abc.jpg", aiCorrected=True,
    )
    assert m.aiPH == 7.3
    assert m.aiCL == 1.5
    assert m.aiImage == "2026-05-29/123456_abc.jpg"
    assert m.aiCorrected is True


def test_ai_fields_ai_corrected_false():
    m = Measurement(
        time=1, name="Pool", pH=7.0, cl=1.0, temp=20.0,
        aiPH=7.0, aiCL=1.0, aiCorrected=False,
    )
    assert m.aiCorrected is False


# --- Event tests ---

def test_valid_event_with_amount_and_unit():
    e = Event(
        time=1755724982,
        name="Pool",
        eventType="chlorine",
        amount=250.0,
        unit="ml",
    )
    assert e.time == 1755724982
    assert e.name == "Pool"
    assert e.eventType == "chlorine"
    assert e.amount == 250.0
    assert e.unit == "ml"
    assert e.note is None


def test_valid_event_without_amount_and_unit():
    e = Event(
        time=1755724982,
        name="Pool",
        eventType="ph",
    )
    assert e.amount is None
    assert e.unit is None


def test_event_rounds_amount_to_one_decimal():
    e = Event(
        time=1755724982,
        name="Pool",
        eventType="flocculant",
        amount=123.45,
        unit="g",
    )
    assert e.amount == 123.5


def test_event_rejects_unknown_name():
    with pytest.raises(ValidationError) as exc:
        Event(
            time=1755724982,
            name="Unknown Pool",
            eventType="chlorine",
            amount=250.0,
            unit="ml",
        )
    assert "Unknown pool name: Unknown Pool" in str(exc.value)


def test_event_requires_unit_when_amount_is_set():
    with pytest.raises(ValidationError) as exc:
        Event(
            time=1755724982,
            name="Pool",
            eventType="chlorine",
            amount=250.0,
        )
    assert "amount and unit must be set together" in str(exc.value)


def test_event_requires_amount_when_unit_is_set():
    with pytest.raises(ValidationError) as exc:
        Event(
            time=1755724982,
            name="Pool",
            eventType="chlorine",
            unit="ml",
        )
    assert "amount and unit must be set together" in str(exc.value)


# --- New event types (refill, backwash, winter) ---

def test_event_accepts_refill_with_minutes():
    e = Event(time=1, name="Pool", eventType="refill", amount=30.0, unit="min")
    assert e.eventType == "refill"
    assert e.unit == "min"
    assert e.amount == 30.0


def test_event_accepts_backwash_with_minutes():
    e = Event(time=1, name="Pool", eventType="backwash", amount=5.0, unit="min")
    assert e.eventType == "backwash"
    assert e.unit == "min"


def test_event_accepts_winter_with_litres():
    e = Event(time=1, name="Pool", eventType="winter", amount=2.5, unit="l")
    assert e.eventType == "winter"
    assert e.unit == "l"


def test_event_rejects_unknown_type():
    with pytest.raises(ValidationError):
        Event(time=1, name="Pool", eventType="bogus")


def test_event_accepts_kg_unit():
    e = Event(time=1, name="Pool", eventType="chlorine", amount=2.5, unit="kg")
    assert e.unit == "kg"
    assert e.amount == 2.5


def test_event_rejects_unknown_unit():
    with pytest.raises(ValidationError):
        Event(time=1, name="Pool", eventType="chlorine", amount=1.0, unit="oz")


# --- Note field ---

def test_event_accepts_note():
    e = Event(time=1, name="Pool", eventType="refill", note="opened the valve halfway")
    assert e.note == "opened the valve halfway"


def test_event_note_default_is_none():
    e = Event(time=1, name="Pool", eventType="chlorine")
    assert e.note is None


def test_event_note_max_length_500_ok():
    e = Event(time=1, name="Pool", eventType="chlorine", note="A" * 500)
    assert e.note == "A" * 500


def test_event_note_too_long_rejected():
    with pytest.raises(ValidationError):
        Event(time=1, name="Pool", eventType="chlorine", note="A" * 501)


def test_event_accepts_negative_amount_for_ph_minus_workflow():
    """The frontend negates ``amount`` for ph-minus before sending; the
    backend just stores the signed value. No range constraint on amount."""
    e = Event(time=1, name="Pool", eventType="ph", amount=-10.0, unit="g")
    assert e.amount == -10.0
