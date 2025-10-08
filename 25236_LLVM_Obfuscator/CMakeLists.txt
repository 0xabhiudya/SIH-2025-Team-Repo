cmake_minimum_required(VERSION 3.13.4)
project(ObfuscatorPasses)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_program(LLVM_CONFIG "llvm-config-15" REQUIRED)
message(STATUS "Found llvm-config: ${LLVM_CONFIG}")

execute_process(COMMAND ${LLVM_CONFIG} --includedir OUTPUT_VARIABLE LLVM_INCLUDE_DIRS OUTPUT_STRIP_TRAILING_WHITESPACE)
execute_process(COMMAND ${LLVM_CONFIG} --cxxflags OUTPUT_VARIABLE LLVM_CXX_FLAGS OUTPUT_STRIP_TRAILING_WHITESPACE)
# --- THIS IS THE FIX: Removed the invalid 'utils' component ---
execute_process(COMMAND ${LLVM_CONFIG} --libs core passes analysis support OUTPUT_VARIABLE LLVM_LIBS OUTPUT_STRIP_TRAILING_WHITESPACE)
execute_process(COMMAND ${LLVM_CONFIG} --system-libs OUTPUT_VARIABLE LLVM_SYSTEM_LIBS OUTPUT_STRIP_TRAILING_WHITESPACE)

include_directories(${LLVM_INCLUDE_DIRS})
string(REPLACE " " ";" CXX_FLAGS_LIST ${LLVM_CXX_FLAGS})
add_compile_options(${CXX_FLAGS_LIST})

file(GLOB PASS_SOURCES "src/*.cpp")
add_library(ObfuscationPasses SHARED ${PASS_SOURCES})

if(LLVM_LIBS)
  string(REPLACE " " ";" LLVM_LIBS_LIST ${LLVM_LIBS})
endif()
if(LLVM_SYSTEM_LIBS)
  string(REPLACE " " ";" LLVM_SYSTEM_LIBS_LIST ${LLVM_SYSTEM_LIBS})
endif()

target_link_libraries(ObfuscationPasses
  PRIVATE
  ${LLVM_LIBS_LIST}
  ${LLVM_SYSTEM_LIBS_LIST}
)

set_target_properties(ObfuscationPasses PROPERTIES
  OUTPUT_NAME "ObfuscationPasses"
)
