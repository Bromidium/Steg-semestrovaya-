import pytest
import cpp_bridge


def test_roundtrip_bits1():
    """Roundtrip с bits=1: encode -> decode."""
    pixels = bytes([128] * (64 * 64 * 3))
    payload = b"hello"
    encoded = cpp_bridge.cpp_encode(pixels, payload, bits=1)
    decoded = cpp_bridge.cpp_decode(encoded)
    assert decoded == payload


def test_roundtrip_bits2():
    """Roundtrip с bits=2: encode -> decode."""
    pixels = bytes([128] * (64 * 64 * 3))
    payload = b"hello"
    encoded = cpp_bridge.cpp_encode(pixels, payload, bits=2)
    decoded = cpp_bridge.cpp_decode(encoded)
    assert decoded == payload


def test_wrong_password():
    """Неверный пароль: encode с hash=111, decode с hash=222 -> RuntimeError."""
    pixels = bytes([128] * (64 * 64 * 3))
    payload = b"x"
    encoded = cpp_bridge.cpp_encode(pixels, payload, bits=1, password_hash=111)
    with pytest.raises(RuntimeError, match="wrong password"):
        cpp_bridge.cpp_decode(encoded, password_hash=222)