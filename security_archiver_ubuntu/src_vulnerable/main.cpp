// Deliberately vulnerable lab version. Never use in production.
#include "archiver.hpp"
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <zlib.h>
namespace fs = std::filesystem;

int main(int argc, char** argv) {
    try {
        std::string input_name;
        std::string output_file = "result.zlib";
        char label[32] = "lab";
        for (int i = 1; i < argc; ++i) {
            const std::string option = argv[i];
            if (option == "--help") {
                std::cout << "Usage: security_archiver [--input FILE] [--output FILE] [--label TEXT]\n";
                return 0;
            }
            if (i + 1 >= argc) throw std::runtime_error("Option needs a value: " + option);
            if (option == "--input") input_name = argv[++i];
            else if (option == "--output") output_file = argv[++i];
            else if (option == "--label") {
                // INTENTIONAL CWE-120: writing beyond a fixed-size 32-byte stack buffer.
                std::strcpy(label, argv[++i]);
            } else throw std::runtime_error("Unknown option: " + option);
        }

        std::vector<std::uint8_t> bytes;
        if (input_name.empty()) bytes = read_all(std::cin);
        else {
            std::ifstream in(input_name, std::ios::binary);
            if (!in) throw std::runtime_error("Cannot open input: " + input_name);
            bytes = read_all(in);
        }
        auto compressed = compress_text(bytes);

        fs::create_directories("output");
        // INTENTIONAL CWE-22: path can contain "../" and escape output directory.
        const fs::path destination = fs::path("output") / output_file;
        std::ofstream out(destination, std::ios::binary | std::ios::trunc);
        if (!out) throw std::runtime_error("Cannot create output file");
        out.write(reinterpret_cast<const char*>(compressed.data()),
                  static_cast<std::streamsize>(compressed.size()));
        if (!out) throw std::runtime_error("Output write failed");
        out.close();
        if (!out) throw std::runtime_error("Output close failed");

        std::cout << "Label: " << label << "\n"
                  << "zlib version: " << zlibVersion() << "\n"
                  << "Input: " << bytes.size() << " bytes\n"
                  << "Compressed: " << compressed.size() << " bytes\n"
                  << "Saved: " << destination << "\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << "\n";
        return 1;
    }
}
