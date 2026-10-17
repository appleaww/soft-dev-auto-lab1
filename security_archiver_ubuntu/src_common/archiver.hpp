#pragma once
#include <cstdint>
#include <istream>
#include <vector>

std::vector<std::uint8_t> read_all(std::istream& input);
std::vector<std::uint8_t> compress_text(const std::vector<std::uint8_t>& input);
