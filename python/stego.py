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
    output_img = args.output_image
    bits = args.bits
    password = args.password or ""
    
    # Получаем payload: либо из текста, либо из файла
    if args.text is not None:
        payload = args.text.encode('utf-8')
        payload_source = "текст"
    elif args.payload_file is not None:
        with open(args.payload_file, 'rb') as f:
            payload = f.read()
        payload_source = f"файл {args.payload_file}"
    else:
        print("Ошибка: укажите -t 'текст' или --file путь_к_файлу", file=sys.stderr)
        sys.exit(1)
    
    print(f"Встраивание данных...")
    print(f"  Исходное изображение: {input_img}")
    print(f"  Payload: {payload_source} ({len(payload)} байт)")
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
    
    # Карта разности сохраняется рядом с выходным файлом
    out_path = Path(output_img)
    diff_path = out_path.parent / (out_path.stem + "_diff.png")
    save_difference_image(orig_pixels, enc_pixels, str(diff_path), scale=50)
    print(f"\n✓ Карта разности сохранена: {diff_path}")


def cmd_decode(args):
    """Команда: извлечение данных"""
    input_img = args.input_image
    password = args.password or ""
    
    print(f"Извлечение данных...")
    print(f"  Закодированное изображение: {input_img}")
    print(f"  Пароль: {'[установлен]' if password else '[нет]'}")
    print()
    
    try:
        payload = decode_image(input_img, password)
    except RuntimeError as e:
        # Ловим ошибку из C++ (неверный пароль, нет данных и т.д.)
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Ловим прочие ошибки (например, файл не найден)
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    
    if args.text:
        # Выводим текст в консоль
        try:
            text = payload.decode('utf-8')
            print(f"✓ Извлечено {len(payload)} байт:")
            print("-" * 50)
            print(text)
            print("-" * 50)
        except UnicodeDecodeError:
            print("Ошибка: извлечённые данные не являются текстом в UTF-8.", file=sys.stderr)
            sys.exit(1)
    else:
        if not args.output_file:
            print("Ошибка: укажите --text (для вывода) или output_file (для сохранения в файл)", file=sys.stderr)
            sys.exit(1)
        with open(args.output_file, 'wb') as f:
            f.write(payload)
        print(f"✓ Извлечено {len(payload)} байт")
        print(f"✓ Сохранено: {args.output_file}")

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
    
    # --- Парсер для encode ---
    enc_parser = subparsers.add_parser('encode', help='Встроить данные')
    enc_parser.add_argument('input_image', help='Путь к исходному изображению')
    enc_parser.add_argument('output_image', help='Путь для сохранения')
    
    # Группа: либо текст (-t), либо файл (--file)
    enc_group = enc_parser.add_mutually_exclusive_group(required=True)
    enc_group.add_argument('-t', '--text', type=str, help='Текст для встраивания')
    enc_group.add_argument('--file', dest='payload_file', type=str, help='Файл с данными')
    
    enc_parser.add_argument('--bits', type=int, choices=[1, 2], default=1)
    enc_parser.add_argument('--password', type=str, default='')
    
    # --- Парсер для decode ---
    dec_parser = subparsers.add_parser('decode', help='Извлечь данные')
    dec_parser.add_argument('input_image', help='Путь к закодированному изображению')
    
    # Группа: либо сохранить в файл (-o), либо вывести текст (-t)
    dec_group = dec_parser.add_mutually_exclusive_group(required=True)
    dec_group.add_argument('-o', '--output', dest='output_file', type=str, help='Куда сохранить файл')
    dec_group.add_argument('-t', '--text', action='store_true', help='Вывести текст в консоль')
    
    dec_parser.add_argument('--password', type=str, default='')

    # --- Парсер для capacity ---
    cap_parser = subparsers.add_parser('capacity', help='Оценить максимальный объём')
    cap_parser.add_argument('input_image', help='Путь к изображению')
    cap_parser.add_argument('--bits', type=int, choices=[1, 2], default=1)
    
    # --- Обработка команд ---
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