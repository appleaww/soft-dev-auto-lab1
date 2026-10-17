// Fixed lab version: safe label, output filename validation and no symlink following.
#include "archiver.hpp"
#include <algorithm>
#include <cerrno>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <zlib.h>
namespace fs = std::filesystem;

// Restrict the output to a single filename (no slash, "..", absolute path).
static void validate_output_name(const std::string& name) {
    if (name.empty() || name == "." || name == ".." ||
        fs::path(name).is_absolute() || name.find('/') != std::string::npos ||
        name.find('\\') != std::string::npos || name.find('\0') != std::string::npos)
        throw std::runtime_error("Invalid output filename (basename only)");
}

static void safe_save(const std::string& output_name,
                      const std::vector<std::uint8_t>& bytes) {
    validate_output_name(output_name);
    if (!fs::exists("output")) fs::create_directory("output");
    // Opening the directory without following symlinks closes the symlink route.
    const int dirfd = ::open("output", O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    if (dirfd < 0) throw std::runtime_error("Cannot open secure output directory");
    const int fd = ::openat(dirfd, output_name.c_str(),
                            O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW, 0600);
    ::close(dirfd);
    if (fd < 0) throw std::runtime_error("Cannot open secure output file");
    const std::uint8_t* cursor = bytes.data();
    std::size_t remaining = bytes.size();
    while (remaining) {
        const std::size_t part = std::min(remaining, static_cast<std::size_t>(1024 * 1024));
        const ssize_t count = ::write(fd, cursor, part);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) { ::close(fd); throw std::runtime_error("Output write failed"); }
        remaining -= static_cast<std::size_t>(count);
        cursor += count;
    }
    if (::close(fd) != 0) throw std::runtime_error("Output close failed");
}

int main(int argc, char** argv) {
    try {
        std::string input_name;
        std::string output_file = "result.zlib";
        std::string label = "lab"; // No fixed C buffer.
        for (int i = 1; i < argc; ++i) {
            const std::string option = argv[i];
            if (option == "--help") {
                std::cout << "Usage: security_archiver [--input FILE] [--output FILE] [--label TEXT]\n";
                return 0;
            }
            if (i + 1 >= argc) throw std::runtime_error("Option needs a value: " + option);
            if (option == "--input") input_name = argv[++i];
            else if (option == "--output") output_file = argv[++i];
            else if (option == "--label") label = argv[++i];
            else throw std::runtime_error("Unknown option: " + option);
        }
        std::vector<std::uint8_t> bytes;
        if (input_name.empty()) bytes = read_all(std::cin);
        else {
            std::ifstream in(input_name, std::ios::binary);
            if (!in) throw std::runtime_error("Cannot open input: " + input_name);
            bytes = read_all(in);
        }
        const auto compressed = compress_text(bytes);
        safe_save(output_file, compressed);
        std::cout << "Label: " << label << "\n"
                  << "zlib version: " << zlibVersion() << "\n"
                  << "Input: " << bytes.size() << " bytes\n"
                  << "Compressed: " << compressed.size() << " bytes\n"
                  << "Saved: " << fs::path("output") / output_file << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << "\n";
        return 1;
    }
}
