#include "stego_core.hpp"

#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static std::vector<uint8_t> make_gradient(size_t w, size_t h, int channels) {
    std::vector<uint8_t> pixels(w * h * channels);
    for (size_t y = 0; y < h; ++y) {
        for (size_t x = 0; x < w; ++x) {
            size_t idx = (y * w + x) * channels;
            for (int c = 0; c < channels; ++c) {
                pixels[idx + c] = static_cast<uint8_t>((x + y * 3 + c * 17) & 0xFF);
            }
        }
    }
    return pixels;
}

static void test_roundtrip() {
    std::cout << "=== test_roundtrip ===" << std::endl;
    const size_t W = 100, H = 100;
    const int CH = 3;
    auto pixels = make_gradient(W, H, CH);

    std::string msg = "Hello, LSB steganography!";
    std::vector<uint8_t> payload(msg.begin(), msg.end());

    const uint64_t pass_hash = 0;
    const uint8_t flags = 0;
    const int bits = 1;

    auto encoded = stego::encode(pixels.data(), pixels.size(), CH, payload, bits, pass_hash, flags);
    auto result = stego::decode(encoded.data(), encoded.size(), CH, pass_hash);

    if (!result.ok) { std::cerr << "FAIL: " << result.error << std::endl; return; }
    if (result.payload != payload) { std::cerr << "FAIL: payload mismatch" << std::endl; return; }
    if (result.bits != bits || result.flags != flags) { std::cerr << "FAIL: metadata mismatch" << std::endl; return; }
    std::cout << "PASS" << std::endl;
}

static void test_wrong_password() {
    std::cout << "=== test_wrong_password ===" << std::endl;
    const size_t W = 100, H = 100;
    const int CH = 3;
    auto pixels = make_gradient(W, H, CH);

    std::vector<uint8_t> payload = {1, 2, 3, 4, 5};
    const uint64_t correct_hash = 0xDEADBEEFCAFEBABEULL;
    const uint64_t wrong_hash = 0x1234567890ABCDEFULL;

    auto encoded = stego::encode(pixels.data(), pixels.size(), CH, payload, 1, correct_hash, 0);
    auto result = stego::decode(encoded.data(), encoded.size(), CH, wrong_hash);

    if (result.ok) { std::cerr << "FAIL: should reject wrong password" << std::endl; return; }
    std::cout << "PASS (error: " << result.error << ")" << std::endl;
}

static void test_overflow() {
    std::cout << "=== test_overflow ===" << std::endl;
    const size_t W = 10, H = 10;
    const int CH = 3;
    auto pixels = make_gradient(W, H, CH);

    size_t cap = stego::capacity(W, H, CH, 1);
    std::vector<uint8_t> payload(cap + 1, 0xAA);

    bool threw = false;
    try {
        stego::encode(pixels.data(), pixels.size(), CH, payload, 1, 0, 0);
    } catch (const std::exception& e) {
        threw = true;
        std::cout << "PASS (exception: " << e.what() << ")" << std::endl;
    }
    if (!threw) std::cerr << "FAIL: expected exception on overflow" << std::endl;
}

int main() {
    test_roundtrip();
    test_wrong_password();
    test_overflow();
    return 0;
}