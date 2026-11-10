#include "stego_core.hpp"
#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc, char* argv[]) {
    if (argc != 7) {
        std::fprintf(stderr, "usage: %s pixels_in payload_in pixels_out bits hash flags\n", argv[0]);
        return 1;
    }

    // Чтение пикселей
    std::ifstream px_ifs(argv[1], std::ios::binary);
    if (!px_ifs) { std::fprintf(stderr, "cannot open %s\n", argv[1]); return 1; }
    px_ifs.seekg(0, std::ios::end);
    std::vector<uint8_t> pixels(px_ifs.tellg());
    px_ifs.seekg(0, std::ios::beg);
    px_ifs.read(reinterpret_cast<char*>(pixels.data()), pixels.size());

    // Чтение payload
    std::ifstream pay_ifs(argv[2], std::ios::binary);
    if (!pay_ifs) { std::fprintf(stderr, "cannot open %s\n", argv[2]); return 1; }
    pay_ifs.seekg(0, std::ios::end);
    std::vector<uint8_t> payload(pay_ifs.tellg());
    pay_ifs.seekg(0, std::ios::beg);
    pay_ifs.read(reinterpret_cast<char*>(payload.data()), payload.size());

    // Парсинг параметров
    int bits = 0;
    uint64_t hash = 0;
    int flags = 0;
    try {
        bits = std::stoi(argv[4]);
        hash = std::stoull(argv[5]);
        flags = std::stoi(argv[6]);
    } catch (const std::exception& e) {
        std::fprintf(stderr, "invalid numeric argument: %s\n", e.what());
        return 1;
    }

    // Кодирование
    try {
        auto out = stego::encode(pixels.data(), pixels.size(), 3, payload, bits, hash, static_cast<uint8_t>(flags));
        std::ofstream ofs(argv[3], std::ios::binary);
        if (!ofs) { std::fprintf(stderr, "cannot write %s\n", argv[3]); return 1; }
        ofs.write(reinterpret_cast<const char*>(out.data()), out.size());
    } catch (const std::exception& e) {
        std::fprintf(stderr, "%s\n", e.what());
        return 1;
    }
    return 0;
}