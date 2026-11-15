"""
Главный CLI скрипт для стеганографии.
"""

import argparse
import sys
from pathlib import Path

from cpp_bridge import encode_image, decode_image, cpp_capacity, load_image_pixels
from metrics import print_quality_report, save_difference_image


def cmd_encode(args):
    """Команда: встраивание данных"""
    input_img = args.input_image
    payload_file = args.payload_file
    output_img = args.output_image
    bits = args.bits
    password = args.password or ""
    
    with open(payload_file, 'rb') as f:
        payload = f.read()
    
    print(f"Встраивание данных...")
    print(f"  Исходное изображение: {input_img}")
    print(f"  Payload: {payload_file} ({len(payload)} байт)")
    print(f"  Выход: {output_img}")
    print(f"  Bits: {bits}")
    print(f"  Пароль: {'[установлен]' if password else '[нет]'}")
    print()
    
    orig_pixels, w, h = load_image_pixels(input_img)
    
    info = encode_image(input_img, payload, output_img, bits, password, flags=0)
    
    print(f"✓ Встроено {info['payload_size']} байт из {info['capacity']} доступных")
    print(f"✓ Сохранено: {output_img}")
    print()
    
    enc_pixels, _, _ = load_image_pixels(output_img)
    
    print_quality_report(orig_pixels, enc_pixels)
    
    diff_path = Path(output_img).stem + "_diff.png"
    save_difference_image(orig_pixels, enc_pixels, diff_path, scale=50)
    print(f"\n✓ Карта разности сохранена: {diff_path}")


def cmd_decode(args):
    """Команда: извлечение данных"""
    input_img = args.input_image
    output_file = args.output_file
    password = args.password or ""
    
    print(f"Извлечение данных...")
    print(f"  Закодированное изображение: {input_img}")
    print(f"  Выход: {output_file}")
    print(f"  Пароль: {'[установлен]' if password else '[нет]'}")
    print()
    
    payload = decode_image(input_img, password)
    
    with open(output_file, 'wb') as f:
        f.write(payload)
    
    print(f"✓ Извлечено {len(payload)} байт")
    print(f"✓ Сохранено: {output_file}")


def cmd_capacity(args):
    """Команда: оценка ёмкости"""
    input_img = args.input_image
    bits = args.bits
    
    _, w, h = load_image_pixels(input_img)
    
    cap = cpp_capacity(w, h, bits)
    
    print(f"Изображение: {input_img} ({w}x{h})")
    print(f"Bits: {bits}")
    print(f"Максимальный объём payload: {cap} байт")


def main():
    parser = argparse.ArgumentParser(
        description="LSB Стеганография (C++ core + Python wrapper)"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    enc_parser = subparsers.add_parser('encode', help='Встроить данные в изображение')
    enc_parser.add_argument('input_image', help='Путь к исходному изображению')
    enc_parser.add_argument('payload_file', help='Путь к файлу с данными')
    enc_parser.add_argument('output_image', help='Путь для сохранения')
    enc_parser.add_argument('--bits', type=int, choices=[1, 2], default=1)
    enc_parser.add_argument('--password', type=str, default='')
    
    dec_parser = subparsers.add_parser('decode', help='Извлечь данные из изображения')
    dec_parser.add_argument('input_image', help='Путь к закодированному изображению')
    dec_parser.add_argument('output_file', help='Путь для сохранения')
    dec_parser.add_argument('--password', type=str, default='')
    
    cap_parser = subparsers.add_parser('capacity', help='Оценить максимальный объём')
    cap_parser.add_argument('input_image', help='Путь к изображению')
    cap_parser.add_argument('--bits', type=int, choices=[1, 2], default=1)
    
    args = parser.parse_args()
    
    if args.command == 'encode':
        cmd_encode(args)
    elif args.command == 'decode':
        cmd_decode(args)
    elif args.command == 'capacity':
        cmd_capacity(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()