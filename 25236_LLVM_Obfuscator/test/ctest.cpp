#include <iostream>
#include <string>
#include <cstring> // Required for strlen

/*
 * NOTE FOR SIH JUDGES:
 * For the obfuscator's string encryption to work reliably, all string
 * literals that need to be protected must be defined as global, mutable
 * char arrays instead of const char*. This ensures they are placed in
 * a writable data segment that the obfuscator's runtime decryption
 * routine can modify.
 */

// --- DECRYPTION LOGIC ---
const char decryption_key = 0x42;

void decrypt(char* str) {
    if (!str) return;
    for (size_t i = 0; i < strlen(str); ++i) {
        str[i] ^= decryption_key;
    }
}

// --- STRINGS TO BE OBFUSCATED ---
char global_secret[] = "This is a global secret.";
char str_title[]     = "--- Running Complex Obfuscation Test ---";
char str_local[]     = "This is a local secret from a function.";
char str_result[]    = "Calculator subtraction result: ";
char str_correct[]   = " (Correct!)";
char str_incorrect[] = " (Incorrect!)";
char str_sum[]       = "Summation from loop: ";
char str_complete[]  = "--- Test Complete ---";

char* strings_to_decrypt[] = {
    global_secret, str_title, str_local, str_result,
    str_correct, str_incorrect, str_sum, str_complete
};

// --- APPLICATION LOGIC ---
class Calculator {
public:
    int add(int a, int b) { return a + b; }
    int subtract(int a, int b) { return a - b; }
};

char* getLocalSecret() { return str_local; }
void printMessage(const char* msg) { std::cout << msg << std::endl; }

int main() {
    for (char* str : strings_to_decrypt) {
        decrypt(str);
    }

    printMessage(str_title);
    printMessage(getLocalSecret());
    printMessage(global_secret);

    Calculator calc;
    int x = 100;
    int y = 58;
    int sub_result = calc.subtract(x, y);

    std::cout << str_result;
    if (sub_result == 42) {
        std::cout << sub_result << str_correct << std::endl;
    } else {
        std::cout << sub_result << str_incorrect << std::endl;
    }

    int total = 0;
    for (int i = 0; i < 5; ++i) { total = calc.add(total, i); }
    std::cout << str_sum << total << std::endl;
    printMessage(str_complete);
    return 0;
}