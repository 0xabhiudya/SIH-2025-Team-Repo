#!/bin/bash

# --- Uninstallation Script for SIH Obfuscator ---

# 1. Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run this script with sudo."
  exit 1
fi

echo "🗑️  Starting SIH Obfuscator uninstallation..."

# 2. Define paths and name
INSTALL_BIN_PATH="/usr/local/bin"
INSTALL_LIB_PATH="/usr/local/lib/sih-obfuscator"
EXECUTABLE_NAME="sih-obfuscator"

# 3. Remove files and directories
echo "  -> Removing executable: $INSTALL_BIN_PATH/$EXECUTABLE_NAME"
rm -f "$INSTALL_BIN_PATH/$EXECUTABLE_NAME"

echo "  -> Removing library directory: $INSTALL_LIB_PATH"
rm -rf "$INSTALL_LIB_PATH"

echo ""
echo "✅ Uninstallation complete!"
