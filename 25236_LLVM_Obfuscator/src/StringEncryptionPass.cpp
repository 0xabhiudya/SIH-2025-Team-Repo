#include "StringEncryptionPass.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/Pass.h"
#include "llvm/Support/raw_ostream.h"
#include <vector>

using namespace llvm;

PreservedAnalyses StringEncryptionPass::run(Module &M, ModuleAnalysisManager &AM) {
    std::vector<GlobalVariable*> stringGlobals;
    
    for (GlobalVariable &GV : M.globals()) {
        if (GV.hasInitializer() && !GV.isConstant()) {
            if (auto *CDA = dyn_cast<ConstantDataArray>(GV.getInitializer())) {
                if (CDA->isString()) {
                    stringGlobals.push_back(&GV);
                }
            }
        }
    }

    if (stringGlobals.empty()) {
        errs() << "StringEncryptionPass: No mutable global strings found to encrypt.\n";
        return PreservedAnalyses::all();
    }
    
    int stringsEncrypted = 0;
    for (GlobalVariable *GV : stringGlobals) {
        ConstantDataArray *CDA = cast<ConstantDataArray>(GV->getInitializer());
        
        // --- THIS IS THE FINAL FIX ---
        // We will manually iterate byte-by-byte to ensure the size is identical.
        size_t numElements = CDA->getNumElements();
        if (numElements <= 1) continue; // Skip empty or single-char strings

        std::vector<char> encryptedChars;
        char key = 0x42;

        for (size_t i = 0; i < numElements; ++i) {
            char originalChar = CDA->getElementAsInteger(i);
            encryptedChars.push_back(originalChar ^ key);
        }
        
        // Create the new constant using the vector of chars.
        // This guarantees the new constant has the exact same number of elements.
        Constant *newInitializer = ConstantDataArray::get(M.getContext(), encryptedChars);
        
        // The type check is no longer needed but is good practice to keep.
        if (newInitializer->getType() != GV->getInitializer()->getType()) {
             errs() << "FATAL ERROR: Type mismatch despite manual copy.\n";
             continue;
        }

        GV->setInitializer(newInitializer);
        stringsEncrypted++;
    }

    errs() << "StringEncryptionPass: " << stringsEncrypted << " strings encrypted.\n";
    return PreservedAnalyses::none();
}