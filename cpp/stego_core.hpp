#pragma once
#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>

namespace stego {

constexpr size_t HEADER_SIZE = 24;
constexpr uint8_t VERSION = 1;
constexpr char MAGIC[4] = {'S', 'T', 'G', '9'};

// Сколько байт payload влезает в изображение w*h с channels каналами.
size_t capacity(size_t w, size_t h, int channels, int bits);

// Встраивает payload в копию пиксельного буфера. Возвращает новый буфер.
std::vector<uint8_t> encode(const uint8_t* pixels, size_t n, int channels,
                            const std::vector<uint8_t>& payload, int bits,
                            uint64_t password_hash, uint8_t flags);

struct DecodeResult {
    bool ok = false;
    std::vector<uint8_t> payload;
    uint8_t flags = 0;
    int bits = 0;
    std::string error;
};

// Извлекает payload. Пароль проверяется по хешу из заголовка.
DecodeResult decode(const uint8_t* pixels, size_t n, int channels,
                    uint64_t password_hash);

} // namespace stego