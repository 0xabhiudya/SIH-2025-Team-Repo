#!/bin/bash

# --- All-in-One Build and Installation Script for SIH Obfuscator ---

# 1. Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo "❌ This script must be run with sudo."
  exit 1
fi

echo "🚀 Starting SIH Obfuscator setup..."

# 2. Detect Linux Distribution and Install Dependencies
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ Cannot detect Linux distribution. Exiting."
    exit 1
fi

echo "  -> Detected operating system: $OS"

if [[ "$OS" == "ubuntu" || "$OS" == "debian" || "$OS" == "parrot" ]]; then
    echo "  -> Updating package lists..."
    apt-get update -y
    
    echo "  -> Installing dependencies (build-essential, cmake, llvm-15, clang-15)..."
    apt-get install -y build-essential cmake llvm-15 clang-15
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies. Please try again."
        exit 1
    fi
else
    echo "⚠️  Warning: Your operating system ($OS) is not automatically supported by this script."
    echo "Please manually install the following dependencies:"
    echo "  - build-essential (or equivalent for g++, make)"
    echo "  - cmake"
    echo "  - llvm-15"
    echo "  - clang-15"
    read -p "Press [Enter] to continue the installation attempt, or Ctrl+C to exit."
fi

# 3. Check for the existence of required LLVM tools
CLANG=$(command -v clang++-15)
if [ -z "$CLANG" ]; then
  echo "❌ Error: clang++-15 could not be found after installation."
  echo "Please ensure the LLVM 15 toolchain is correctly installed and in your PATH."
  exit 1
fi

# 4. Build the obfuscator library
echo "  -> Compiling the obfuscation passes..."
rm -rf build
mkdir build
cd build
cmake ..
make
cd ..

# 5. Define paths and check for compiled library
INSTALL_BIN_PATH="/usr/local/bin"
INSTALL_LIB_PATH="/usr/local/lib/sih-obfuscator"
EXECUTABLE_NAME="sih-obfuscator"
SOURCE_SCRIPT="./obfuscate-cli.sh"
SOURCE_LIB="./build/libObfuscationPasses.so"

if [ ! -f "$SOURCE_LIB" ]; then
  echo "❌ Error: Compilation failed. The library file was not created."
  exit 1
fi

# 6. Install the tool
echo "  -> Installing files..."
mkdir -p "$INSTALL_LIB_PATH"
cp "$SOURCE_LIB" "$INSTALL_LIB_PATH/"
cp "$SOURCE_SCRIPT" "$INSTALL_BIN_PATH/$EXECUTABLE_NAME"
chmod +x "$INSTALL_BIN_PATH/$EXECUTABLE_NAME"
sed -i "s|PASS_LIB_PATH=.*|PASS_LIB_PATH=\"$INSTALL_LIB_PATH/libObfuscationPasses.so\"|" "$INSTALL_BIN_PATH/$EXECUTABLE_NAME"

echo ""
echo "✅ Installation complete!"
echo "You can now run the tool from anywhere by typing: $EXECUTABLE_NAME your_file.cpp"