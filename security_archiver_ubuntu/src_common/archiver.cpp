#include "archiver.hpp"
#include <array>
#include <limits>
#include <stdexcept>
#include <zlib.h>

std::vector<std::uint8_t> read_all(std::istream& input) {
    std::vector<std::uint8_t> bytes;
    std::array<char, 4096> chunk{};
    while (input) {
        input.read(chunk.data(), static_cast<std::streamsize>(chunk.size()));
        for (std::streamsize i = 0; i < input.gcount(); ++i) {
            bytes.push_back(static_cast<std::uint8_t>(chunk[static_cast<std::size_t>(i)]));
        }
    }
    if (input.bad()) throw std::runtime_error("Input read error");
    return bytes;
}

std::vector<std::uint8_t> compress_text(const std::vector<std::uint8_t>& input) {
    if (input.size() > std::numeric_limits<uLong>::max())
        throw std::runtime_error("Input too big for zlib");
    const auto in_length = static_cast<uLong>(input.size());
    auto out_length = static_cast<uLongf>(compressBound(in_length));
    std::vector<std::uint8_t> output(static_cast<std::size_t>(out_length));
    const Bytef empty_byte = 0;
    const Bytef* in_ptr = input.empty() ? &empty_byte : input.data();
    const int status = compress2(output.data(), &out_length,
                                 in_ptr, in_length, Z_BEST_COMPRESSION);
    if (status != Z_OK) throw std::runtime_error("zlib compress2 failed");
    output.resize(static_cast<std::size_t>(out_length));
    return output;
}
