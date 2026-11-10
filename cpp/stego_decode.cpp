#include "stego_core.hpp"
#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::fprintf(stderr, "usage: %s pixels_in payload_out hash\n", argv[0]);
        return 1;
    }

    // Чтение пикселей
    std::ifstream ifs(argv[1], std::ios::binary);
    if (!ifs) { std::fprintf(stderr, "cannot open %s\n", argv[1]); return 1; }
    ifs.seekg(0, std::ios::end);
    std::vector<uint8_t> pixels(ifs.tellg());
    ifs.seekg(0, std::ios::beg);
    ifs.read(reinterpret_cast<char*>(pixels.data()), pixels.size());

    // Парсинг пароля
    uint64_t hash = 0;
    try {
        hash = std::stoull(argv[3]);
    } catch (const std::exception& e) {
        std::fprintf(stderr, "invalid hash: %s\n", e.what());
        return 1;
    }

    // Декодирование
    auto res = stego::decode(pixels.data(), pixels.size(), 3, hash);
    if (!res.ok) {
        std::fprintf(stderr, "%s\n", res.error.c_str());
        return 1;
    }

    // Запись payload
    std::ofstream ofs(argv[2], std::ios::binary);
    if (!ofs) { std::fprintf(stderr, "cannot write %s\n", argv[2]); return 1; }
    ofs.write(reinterpret_cast<const char*>(res.payload.data()), res.payload.size());
    return 0;
}