cmake_minimum_required(VERSION 3.10)
project(libhashtab C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Main library
add_library(hashtab STATIC 
    libhashtab.c
    libhashtab.h
)

# Installation settings
install(TARGETS hashtab DESTINATION lib)
install(FILES libhashtab.h DESTINATION include)

# Testing executable
add_executable(hashtab_test hashtab_test.c)
target_link_libraries(hashtab_test hashtab)
