cmake_minimum_required(VERSION 3.20)
project(security_archiver_lab LANGUAGES C CXX)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(LAB_FIXED "Build fixed app instead of intentionally vulnerable app" OFF)
option(LAB_ASAN "Enable AddressSanitizer for experiments" OFF)
option(LAB_USE_SYSTEM_ZLIB "OFFLINE CORE TEST ONLY: bypass pinned zlib and use host zlib" OFF)

if(LAB_FIXED)
  set(APP_MAIN src_fixed/main.cpp)
  set(ZLIB_VERSION_PIN "1.3.2")
  set(ZLIB_SHA256 "bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16")
else()
  set(APP_MAIN src_vulnerable/main.cpp)
  set(ZLIB_VERSION_PIN "1.2.11")
  set(ZLIB_SHA256 "c3e5e9fdd5004dcb542feda5ee4f0ff0744628baf8ed2dd5d66f8ca1197cb1a1")
endif()

# Fetch and STATICALLY link the exact upstream source version to avoid using
# the system libz on Linux. The insecure version is for a local lab only.
if(LAB_USE_SYSTEM_ZLIB)
  message(WARNING "SYSTEM ZLIB: this tests app logic only. Do NOT use as SCA evidence.")
  find_package(ZLIB REQUIRED)
  set(LAB_ZLIB_TARGET ZLIB::ZLIB)
else()
  include(FetchContent)
  FetchContent_Declare(
    pinned_zlib
    URL "https://zlib.net/fossils/zlib-${ZLIB_VERSION_PIN}.tar.gz"
    URL_HASH "SHA256=${ZLIB_SHA256}"
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    SOURCE_SUBDIR "no_cmake_subproject_in_this_path"
  )
  FetchContent_MakeAvailable(pinned_zlib)
  set(ZSRC "${pinned_zlib_SOURCE_DIR}")
  add_library(pinned_zlib_static STATIC
    "${ZSRC}/adler32.c" "${ZSRC}/compress.c" "${ZSRC}/crc32.c"
    "${ZSRC}/deflate.c" "${ZSRC}/gzclose.c" "${ZSRC}/gzlib.c"
    "${ZSRC}/gzread.c" "${ZSRC}/gzwrite.c" "${ZSRC}/inflate.c"
    "${ZSRC}/infback.c" "${ZSRC}/inftrees.c" "${ZSRC}/inffast.c"
    "${ZSRC}/trees.c" "${ZSRC}/uncompr.c" "${ZSRC}/zutil.c"
  )
  target_include_directories(pinned_zlib_static PUBLIC "${ZSRC}")
  set(LAB_ZLIB_TARGET pinned_zlib_static)
endif()

add_executable(security_archiver "${APP_MAIN}" src_common/archiver.cpp)
target_include_directories(security_archiver PRIVATE src_common)
target_link_libraries(security_archiver PRIVATE "${LAB_ZLIB_TARGET}")
if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(security_archiver PRIVATE -Wall -Wextra -Wpedantic)
endif()
if(LAB_ASAN)
  if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    message(FATAL_ERROR "ASan build requires Clang or GCC")
  endif()
  target_compile_options(security_archiver PRIVATE -fsanitize=address -fno-omit-frame-pointer -g)
  target_link_options(security_archiver PRIVATE -fsanitize=address)
endif()
message(STATUS "LAB_FIXED=${LAB_FIXED}; pinned upstream zlib=${ZLIB_VERSION_PIN}; LAB_USE_SYSTEM_ZLIB=${LAB_USE_SYSTEM_ZLIB}")
