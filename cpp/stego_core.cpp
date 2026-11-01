#include "stego_core.hpp"

#include <array>
#include <cstring>
#include <stdexcept>

namespace stego {

// ============================================================
// Числа в формате little-endian (младший байт первый).
// Заголовок хранит числа именно так.
// ============================================================

static inline void write_le32(uint8_t* dst, uint32_t v) {
    dst[0] = static_cast<uint8_t>(v);
    dst[1] = static_cast<uint8_t>(v >> 8);
    dst[2] = static_cast<uint8_t>(v >> 16);
    dst[3] = static_cast<uint8_t>(v >> 24);
}

static inline void write_le64(uint8_t* dst, uint64_t v) {
    for (int i = 0; i < 8; ++i) dst[i] = static_cast<uint8_t>(v >> (8 * i));
}

static inline uint32_t read_le32(const uint8_t* src) {
    return static_cast<uint32_t>(src[0])
         | (static_cast<uint32_t>(src[1]) << 8)
         | (static_cast<uint32_t>(src[2]) << 16)
         | (static_cast<uint32_t>(src[3]) << 24);
}

static inline uint64_t read_le64(const uint8_t* src) {
    uint64_t v = 0;
    for (int i = 0; i < 8; ++i) v |= static_cast<uint64_t>(src[i]) << (8 * i);
    return v;
}

// ============================================================
// CRC32 (полином как в PNG). Считает контрольную сумму от данных.
// Если при извлечении сумма не совпадёт — payload побился.
// ============================================================

static const std::array<uint32_t, 256>& crc32_table() {
    static std::array<uint32_t, 256> table = []() {
        std::array<uint32_t, 256> t{};
        for (uint32_t i = 0; i < 256; ++i) {
            uint32_t c = i;
            for (int k = 0; k < 8; ++k) {
                c = (c & 1) ? (0xEDB88320u ^ (c >> 1)) : (c >> 1);
            }
            t[i] = c;
        }
        return t;
    }();
    return table;
}

static uint32_t crc32(const uint8_t* data, size_t len) {
    const auto& table = crc32_table();
    uint32_t c = 0xFFFFFFFFu;
    for (size_t i = 0; i < len; ++i) {
        c = table[(c ^ data[i]) & 0xFF] ^ (c >> 8);
    }
    return c ^ 0xFFFFFFFFu;
}

// ============================================================
// Запись/чтение битового потока в младшие биты (LSB) пикселей.
// Пиксель = channels байт (R, G, B при channels=3).
// В каждый байт пикселя кладём `bits` младших бит (1 или 2).
// Порядок: байты данных идут подряд, внутри байта — старший бит первым.
// ============================================================

// Кладёт data (data_len байт) в младшие биты массива pixels (n байт).
static void write_stream(uint8_t* pixels, size_t n, int channels, int bits,
                         const uint8_t* data, size_t data_len) {
    const size_t mask = (1u << bits) - 1u;   // 0b01 или 0b11
    const size_t clear_mask = ~mask;          // для зануления младших бит

    size_t byte_idx = 0;   // индекс текущего байта в data
    uint8_t cur_byte = 0;  // текущий байт данных
    // ВАЖНО: bit_pos = 8 означает «текущий байт исчерпан, надо загрузить новый».
    // Если начать с 0, то первые 8 бит потока будут взяты из cur_byte = 0,
    // а не из data[0] — это ломает roundtrip.
    int bit_pos = 8;

    const size_t total_pixels = n / static_cast<size_t>(channels);

    for (size_t p = 0; p < total_pixels; ++p) {
        for (int c = 0; c < channels; ++c) {
            // Собираем `bits` бит из потока данных
            uint8_t chunk = 0;
            int need = bits;
            while (need > 0) {
                if (bit_pos == 8) {
                    // Текущий байт исчерпан — берём следующий
                    cur_byte = (byte_idx < data_len) ? data[byte_idx++] : 0;
                    bit_pos = 0;
                }
                int available = 8 - bit_pos;
                int take = (available < need) ? available : need;
                // Берём `take` старших из оставшихся бит cur_byte
                uint8_t shifted =
                    static_cast<uint8_t>((cur_byte >> (8 - bit_pos - take))
                                         & ((1u << take) - 1));
                chunk = static_cast<uint8_t>((chunk << take) | shifted);
                bit_pos += take;
                need -= take;
            }
            // Кладём chunk в младшие биты канала
            size_t idx = p * static_cast<size_t>(channels) + c;
            pixels[idx] = static_cast<uint8_t>(
                (pixels[idx] & clear_mask) | (chunk & mask));
        }
    }
}

// Читает out_len байт из младших битов pixels.
// Возвращает true, если удалось прочитать всё.
static bool read_stream(const uint8_t* pixels, size_t n, int channels, int bits,
                        uint8_t* out, size_t out_len) {
    const size_t mask = (1u << bits) - 1u;
    size_t byte_idx = 0;
    uint8_t cur_byte = 0;
    int bit_pos = 0;  // сколько бит уже накоплено в cur_byte (0..7)

    const size_t total_pixels = n / static_cast<size_t>(channels);

    for (size_t p = 0; p < total_pixels; ++p) {
        for (int c = 0; c < channels; ++c) {
            uint8_t chunk = pixels[p * static_cast<size_t>(channels) + c] & mask;
            // Вписываем `bits` бит в текущий выходной байт
            cur_byte = static_cast<uint8_t>(
                cur_byte | (chunk << (8 - bit_pos - bits)));
            bit_pos += bits;
            if (bit_pos == 8) {
                if (byte_idx < out_len) out[byte_idx++] = cur_byte;
                cur_byte = 0;
                bit_pos = 0;
                if (byte_idx == out_len) return true;  // всё прочитали
            }
        }
    }
    return byte_idx == out_len;
}

// ============================================================
// Публичные функции
// ============================================================

// Максимальное число байт payload, которое помещается в изображение.
size_t capacity(size_t w, size_t h, int channels, int bits) {
    if (bits != 1 && bits != 2) return 0;
    if (channels <= 0) return 0;
    size_t total_bits =
        w * h * static_cast<size_t>(channels) * static_cast<size_t>(bits);
    if (total_bits < HEADER_SIZE * 8) return 0;
    return (total_bits - HEADER_SIZE * 8) / 8;
}

// Встраивает payload в копию пиксельного буфера и возвращает эту копию.
// Исходный буфер pixels не меняется — так удобнее тестировать.
std::vector<uint8_t> encode(const uint8_t* pixels, size_t n, int channels,
                            const std::vector<uint8_t>& payload, int bits,
                            uint64_t password_hash, uint8_t flags) {
    if (bits != 1 && bits != 2)
        throw std::invalid_argument("bits must be 1 or 2");
    if (channels != 3)
        throw std::invalid_argument("only 3 channels (RGB) supported");
    if (n == 0 || (n % static_cast<size_t>(channels)) != 0)
        throw std::invalid_argument("invalid pixel buffer size");

    // Сколько payload влезет в этот буфер
    size_t total_bits = n * static_cast<size_t>(bits);
    if (total_bits < HEADER_SIZE * 8)
        throw std::invalid_argument("image too small for header");
    size_t cap = (total_bits - HEADER_SIZE * 8) / 8;
    if (payload.size() > cap)
        throw std::invalid_argument("payload exceeds capacity");

    // Собираем заголовок (24 байта)
    std::vector<uint8_t> header(HEADER_SIZE, 0);
    std::memcpy(header.data() + 0, MAGIC, 4);
    header[4] = VERSION;
    header[5] = static_cast<uint8_t>(bits);
    header[6] = flags;
    write_le32(header.data() + 7, static_cast<uint32_t>(payload.size()));
    write_le32(header.data() + 11, crc32(payload.data(), payload.size()));
    write_le64(header.data() + 15, password_hash);
    // header[23] остаётся 0 (reserved)

    // Склеиваем header + payload и пишем в копию пикселей
    std::vector<uint8_t> stream;
    stream.reserve(HEADER_SIZE + payload.size());
    stream.insert(stream.end(), header.begin(), header.end());
    stream.insert(stream.end(), payload.begin(), payload.end());

    std::vector<uint8_t> out(pixels, pixels + n);
    write_stream(out.data(), n, channels, bits, stream.data(), stream.size());
    return out;
}

// Извлекает payload. Сначала читает заголовок, потом проверяет пароль,
// потом читает payload и проверяет его CRC32.
DecodeResult decode(const uint8_t* pixels, size_t n, int channels,
                    uint64_t password_hash) {
    DecodeResult res;

    auto fail = [&](const std::string& msg) -> DecodeResult {
        res.ok = false;
        res.error = msg;
        return res;
    };

    if (channels != 3) return fail("only 3 channels (RGB) supported");
    if (n == 0 || (n % static_cast<size_t>(channels)) != 0)
        return fail("invalid pixel buffer size");

    // В заголовке записано, сколько бит на канал (1 или 2), но чтобы
    // прочитать заголовок, надо уже это знать.
    // Решение: пробуем bits=1, если magic не сошёлся — bits=2.
    std::vector<uint8_t> header(HEADER_SIZE, 0);
    int bits = 0;
    for (int guess = 1; guess <= 2; ++guess) {
        if (read_stream(pixels, n, channels, guess, header.data(), HEADER_SIZE)
            && std::memcmp(header.data(), MAGIC, 4) == 0
            && header[4] == VERSION) {
            bits = guess;
            break;
        }
    }
    if (bits == 0) return fail("invalid magic/version");

    // Заголовок говорит, сколько бит на канал — сверяем с тем, чем читали
    if (header[5] != bits) return fail("bits mismatch in header");

    uint8_t flags = header[6];
    uint32_t payload_len = read_le32(header.data() + 7);
    uint32_t expected_crc = read_le32(header.data() + 11);
    uint64_t stored_hash = read_le64(header.data() + 15);

    // Проверка пароля: сравниваем хеш из заголовка с хешем от введённого пароля.
    // Это проверка доступа, а не шифрование.
    if (stored_hash != 0 && stored_hash != password_hash)
        return fail("wrong password");
    if (stored_hash == 0 && password_hash != 0)
        return fail("password set but container is unprotected");

    // Проверяем, что заявленная длина не больше ёмкости
    size_t total_bits = n * static_cast<size_t>(bits);
    size_t cap = (total_bits - HEADER_SIZE * 8) / 8;
    if (payload_len > cap) return fail("payload_length exceeds capacity");

    // Читаем header + payload одним потоком, потом отрезаем header
    std::vector<uint8_t> all(HEADER_SIZE + payload_len);
    if (!read_stream(pixels, n, channels, bits, all.data(), all.size()))
        return fail("failed to read payload bits");

    std::vector<uint8_t> payload(all.begin() + HEADER_SIZE, all.end());

    if (crc32(payload.data(), payload.size()) != expected_crc)
        return fail("CRC32 mismatch");

    res.ok = true;
    res.payload = std::move(payload);
    res.flags = flags;
    res.bits = bits;
    return res;
}

} // namespace stego