#ifndef FUNCTION_INDIRECTION_PASS_H
#define FUNCTION_INDIRECTION_PASS_H

#include "llvm/IR/PassManager.h"

struct FunctionIndirectionPass : public llvm::PassInfoMixin<FunctionIndirectionPass> {
  llvm::PreservedAnalyses run(llvm::Function &F, llvm::FunctionAnalysisManager &AM);
};

#endif // FUNCTION_INDIRECTION_PASS_H
