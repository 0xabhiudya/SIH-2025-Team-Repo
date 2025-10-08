#include <iostream>
#include <string>

// The string is now a simple constant.
// Our pass will find it, encrypt it, and inject code to decrypt it at startup.
const char* my_str = "Hello SIH!";

int main() {
    int a = 20;
    int b = 8;
    int result = a - b; // Targeted by SubObfuscationPass.

    // No need to call decrypt_string() anymore! It happens automatically.
    std::cout << "The decrypted string is: " << my_str << std::endl;
    std::cout << "The arithmetic result is: " << result << std::endl;

    return 0;
}
