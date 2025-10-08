#ifndef STRING_ENCRYPTION_PASS_H
#define STRING_ENCRYPTION_PASS_H

#include "llvm/IR/PassManager.h"

struct StringEncryptionPass : public llvm::PassInfoMixin<StringEncryptionPass> {
  llvm::PreservedAnalyses run(llvm::Module &M, llvm::ModuleAnalysisManager &AM);
};

#endif
