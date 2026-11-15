"""
Метрики качества для сравнения исходного и закодированного изображения.
"""

import numpy as np
from PIL import Image


def calculate_mse(original: np.ndarray, encoded: np.ndarray) -> float:
    """
    Вычисляет Mean Squared Error (среднеквадратичную ошибку).
    """
    if original.shape != encoded.shape:
        raise ValueError(f"Shape mismatch: {original.shape} vs {encoded.shape}")
    
    orig_float = original.astype(np.float64)
    enc_float = encoded.astype(np.float64)
    
    mse = np.mean((orig_float - enc_float) ** 2)
    return float(mse)


def calculate_psnr(original: np.ndarray, encoded: np.ndarray) -> float:
    """
    Вычисляет Peak Signal-to-Noise Ratio (пиковое отношение сигнала к шуму).
    """
    mse = calculate_mse(original, encoded)
    
    if mse == 0:
        return float('inf')
    
    MAX_PIXEL = 255.0
    psnr = 10 * np.log10((MAX_PIXEL ** 2) / mse)
    return float(psnr)


def create_difference_image(original: np.ndarray, encoded: np.ndarray, 
                            scale: int = 50) -> np.ndarray:
    """
    Создаёт карту разности для визуализации изменений.
    """
    if original.shape != encoded.shape:
        raise ValueError(f"Shape mismatch: {original.shape} vs {encoded.shape}")
    
    diff = np.abs(original.astype(np.int16) - encoded.astype(np.int16))
    diff_scaled = np.clip(diff * scale, 0, 255).astype(np.uint8)
    
    return diff_scaled


def save_difference_image(original: np.ndarray, encoded: np.ndarray, 
                          output_path: str, scale: int = 50):
    """
    Сохраняет карту разности как изображение.
    """
    diff_img = create_difference_image(original, encoded, scale)
    img = Image.fromarray(diff_img, mode='RGB')
    img.save(output_path)


def analyze_quality(original: np.ndarray, encoded: np.ndarray) -> dict:
    """
    Полный анализ качества: MSE, PSNR, количество изменённых пикселей.
    """
    mse = calculate_mse(original, encoded)
    psnr = calculate_psnr(original, encoded)
    
    diff = np.abs(original.astype(np.int16) - encoded.astype(np.int16))
    changed_mask = np.any(diff > 0, axis=2)
    changed_pixels = int(np.sum(changed_mask))
    
    total_pixels = original.shape[0] * original.shape[1]
    changed_percent = (changed_pixels / total_pixels) * 100
    
    return {
        "mse": mse,
        "psnr": psnr,
        "changed_pixels": changed_pixels,
        "changed_percent": changed_percent,
        "total_pixels": total_pixels
    }


def print_quality_report(original: np.ndarray, encoded: np.ndarray):
    """
    Выводит отчёт о качестве в консоль.
    """
    metrics = analyze_quality(original, encoded)
    
    print("=" * 50)
    print("ОТЧЁТ О КАЧЕСТВЕ СТЕГАНОГРАФИИ")
    print("=" * 50)
    print(f"MSE:              {metrics['mse']:.4f}")
    print(f"PSNR:             {metrics['psnr']:.2f} dB")
    
    if metrics['psnr'] == float('inf'):
        print("Качество:         ИДЕАЛЬНОЕ (изображения идентичны)")
    elif metrics['psnr'] > 40:
        print("Качество:         ОТЛИЧНОЕ (незаметно)")
    elif metrics['psnr'] > 30:
        print("Качество:         ХОРОШЕЕ")
    else:
        print("Качество:         ЗАМЕТНЫЕ ИСКАЖЕНИЯ")
    
    print("-" * 50)
    print(f"Всего пикселей:   {metrics['total_pixels']:,}")
    print(f"Изменено:         {metrics['changed_pixels']:,} "
          f"({metrics['changed_percent']:.2f}%)")
    print("=" * 50)