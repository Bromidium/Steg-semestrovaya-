import os
import subprocess
import tempfile

# cpp_bridge.py лежит в python/, .exe — в cpp/ (сестринская папка)
_HERE = os.path.dirname(os.path.abspath(__file__))
_CPP_DIR = os.path.join(os.path.dirname(_HERE), "cpp")

ENCODE_EXE = os.path.join(_CPP_DIR, "stego_encode.exe")
DECODE_EXE = os.path.join(_CPP_DIR, "stego_decode.exe")
CHANNELS = 3


def cpp_encode(pixels: bytes, payload: bytes, bits: int,
               password_hash: int = 0, flags: int = 0) -> bytes:
    """Вызывает stego_encode.exe через subprocess, возвращает закодированные пиксели."""
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
    """Вызывает stego_decode.exe через subprocess, возвращает извлечённый payload."""
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