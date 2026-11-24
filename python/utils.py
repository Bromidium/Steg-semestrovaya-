"""
Утилиты для работы с изображениями и хешированием.
"""

from PIL import Image
import numpy as np
from typing import Tuple, Optional

def fnv1a_64(text: str) -> int:
    """
    FNV-1a 64-bit хеш для строки (UTF-8).
    Используется для хеширования пароля.
    """
    if not text:
        return 0
    
    FNV_OFFSET_BASIS = 0xcbf29ce484222325
    FNV_PRIME = 0x100000001b3
    MASK_64 = 0xFFFFFFFFFFFFFFFF
    
    data = text.encode('utf-8')
    hash_value = FNV_OFFSET_BASIS
    
    for byte in data:
        hash_value ^= byte
        hash_value = (hash_value * FNV_PRIME) & MASK_64
    
    return hash_value


def load_image_pixels(image_path: str) -> Tuple[np.ndarray, int, int]:
    """
    Загружает изображение (PNG/BMP) и возвращает сырые пиксели в формате RGB.
    
    Returns:
        pixels: numpy array shape (H, W, 3), dtype uint8
        width: ширина изображения
        height: высота изображения
    """
    img = Image.open(image_path)
    
    # Конвертируем в RGB (если было RGBA, grayscale, etc.)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    pixels = np.array(img, dtype=np.uint8)
    
    return pixels, width, height


def save_image_pixels(pixels: np.ndarray, output_path: str, 
                      width: int, height: int, original_format: Optional[str] = None):
    """
    Сохраняет сырые пиксели в файл изображения (PNG/BMP).
    """
    # Если плоский массив — reshape в (H, W, 3)
    if pixels.ndim == 1:
        pixels = pixels.reshape((height, width, 3))
    
    img = Image.fromarray(pixels, mode='RGB')
    
    # Определяем формат из расширения, если не указан
    if original_format is None:
        ext = output_path.lower().split('.')[-1]
        if ext in ('png', 'bmp'):
            original_format = ext.upper()
        else:
            original_format = 'PNG'
    
    img.save(output_path, format=original_format)


def pixels_to_bytes(pixels: np.ndarray) -> bytes:
    """Конвертирует numpy array в bytes для передачи в C++."""
    return pixels.tobytes()


def bytes_to_pixels(data: bytes, width: int, height: int) -> np.ndarray:
    """Конвертирует bytes из C++ обратно в numpy array."""
    return np.frombuffer(data, dtype=np.uint8).reshape((height, width, 3))