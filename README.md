stego/
├── cpp/
│   ├── stego_core.hpp          # API ядра (3 функции)
│   ├── stego_core.cpp          # LSB + заголовок + CRC32
│   ├── main_test.cpp           # самопроверка ядра (6 сценариев)
│   ├── stego_encode.cpp        # main() → stego_encode.exe
│   ├── stego_decode.cpp        # main() → stego_decode.exe
│   ├── stego_encode.exe        # после сборки (можно в .gitignore)
│   └── stego_decode.exe        # после сборки (можно в .gitignore)
│
├── python/
│   └── stego_app/
│       ├── __init__.py
│       ├── cpp_bridge.py       # subprocess-обёртка над .exe
│       ├── image_io.py         # Pillow: загрузка/сохранение PNG/BMP
│       ├── hashing.py          # FNV-1a 64 для пароля
│       ├── metrics.py          # PSNR, MSE, diff_map, LSB-гистограмма
│       └── cli.py              # argparse: hide/extract/capacity/compare/wm-*/detect
│
├── tests/
│   ├── test_subprocess.py      # roundtrip через .exe (шаг 2)
│   ├── test_roundtrip.py       # hide → extract через CLI
│   ├── test_errors.py          # неверный пароль, не-stego, переполнение
│   ├── test_capacity.py        # формула совпадает с фактом
│   └── test_metrics.py         # PSNR одинаковых = inf
│
├── samples/
│   ├── small.png               # 64×64 или 200×200 — для быстрых тестов
│   └── photo.png               # реальное фото — для PSNR и бенчмарка
│
├── report/
│   └── report.md               # отчёт (или .docx — как требует препод)
│
├── requirements.txt            # pillow, numpy, pytest
├── README.md                   # установка, сборка, команды CLI
└── .gitignore                  # *.exe, __pycache__/, build/, *.bin