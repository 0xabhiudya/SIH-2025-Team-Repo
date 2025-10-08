#ifndef SUB_OBFUSCATION_PASS_H
#define SUB_OBFUSCATION_PASS_H

#include "llvm/IR/PassManager.h"

struct SubObfuscationPass : public llvm::PassInfoMixin<SubObfuscationPass> {
  llvm::PreservedAnalyses run(llvm::Function &F, llvm::FunctionAnalysisManager &AM);
};

#endif // SUB_OBFUSCATION_PASS_H
