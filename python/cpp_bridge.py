"""
Мост между Python и C++ stego_encode / stego_decode.
"""

import os
import subprocess
import tempfile
import sys
from typing import Tuple

from utils import fnv1a_64, load_image_pixels, save_image_pixels, pixels_to_bytes, bytes_to_pixels

# Пути к исполняемым файлам
_HERE = os.path.dirname(os.path.abspath(__file__))
_CPP_DIR = os.path.join(os.path.dirname(_HERE), "cpp")

# Определяем расширение для исполняемых файлов
if sys.platform == 'win32':
    EXE_EXT = '.exe'
else:
    EXE_EXT = ''

ENCODE_EXE = os.path.join(_CPP_DIR, f"stego_encode{EXE_EXT}")
DECODE_EXE = os.path.join(_CPP_DIR, f"stego_decode{EXE_EXT}")
CHANNELS = 3


def cpp_capacity(width: int, height: int, bits: int) -> int:
    """
    Вычисляет максимальный объём payload для изображения.
    """
    if bits not in (1, 2):
        raise ValueError("bits must be 1 or 2")
    
    total_bits = width * height * CHANNELS * bits
    HEADER_SIZE = 24
    if total_bits < HEADER_SIZE * 8:
        return 0
    
    return (total_bits - HEADER_SIZE * 8) // 8


def cpp_encode(pixels: bytes, payload: bytes, bits: int,
               password_hash: int = 0, flags: int = 0) -> bytes:
    """
    Вызывает stego_encode через subprocess, возвращает закодированные пиксели.
    """
    with tempfile.TemporaryDirectory() as td:
        px_in = os.path.join(td, "px_in.bin")
        pay_in = os.path.join(td, "pay_in.bin")
        px_out = os.path.join(td, "px_out.bin")

        with open(px_in, "wb") as f:
            f.write(pixels)
        with open(pay_in, "wb") as f:
            f.write(payload)

        r = subprocess.run(
            [ENCODE_EXE, px_in, pay_in, px_out, str(bits), str(password_hash), str(flags)],
            capture_output=True
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode("utf-8", "replace").strip())

        with open(px_out, "rb") as f:
            return f.read()


def cpp_decode(pixels: bytes, password_hash: int = 0) -> bytes:
    """
    Вызывает stego_decode через subprocess, возвращает извлечённый payload.
    """
    with tempfile.TemporaryDirectory() as td:
        px_in = os.path.join(td, "px_in.bin")
        pay_out = os.path.join(td, "pay_out.bin")

        with open(px_in, "wb") as f:
            f.write(pixels)

        r = subprocess.run(
            [DECODE_EXE, px_in, pay_out, str(password_hash)],
            capture_output=True
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr.decode("utf-8", "replace").strip())

        with open(pay_out, "rb") as f:
            return f.read()


def encode_image(input_image: str, payload_data: bytes, output_image: str,
                 bits: int = 1, password: str = "", flags: int = 0) -> dict:
    """
    Встраивает данные в изображение.
    """
    pixels, width, height = load_image_pixels(input_image)
    
    capacity = cpp_capacity(width, height, bits)
    if len(payload_data) > capacity:
        raise ValueError(
            f"Payload too large: {len(payload_data)} bytes, "
            f"capacity: {capacity} bytes"
        )
    
    password_hash = fnv1a_64(password)
    
    pixels_bytes = pixels_to_bytes(pixels)
    encoded_bytes = cpp_encode(pixels_bytes, payload_data, bits, password_hash, flags)
    
    encoded_pixels = bytes_to_pixels(encoded_bytes, width, height)
    save_image_pixels(encoded_pixels, output_image, width, height)
    
    return {
        "capacity": capacity,
        "payload_size": len(payload_data),
        "bits": bits,
        "password_hash": password_hash
    }


def decode_image(input_image: str, password: str = "") -> bytes:
    """
    Извлекает данные из изображения.
    """
    pixels, width, height = load_image_pixels(input_image)
    
    password_hash = fnv1a_64(password)
    
    pixels_bytes = pixels_to_bytes(pixels)
    payload = cpp_decode(pixels_bytes, password_hash)
    
    return payload