#ifndef BOGUS_CONTROL_FLOW_PASS_H
#define BOGUS_CONTROL_FLOW_PASS_H

#include "llvm/IR/PassManager.h"

struct BogusControlFlowPass : public llvm::PassInfoMixin<BogusControlFlowPass> {
  llvm::PreservedAnalyses run(llvm::Function &F, llvm::FunctionAnalysisManager &AM);
};

#endif // BOGUS_CONTROL_FLOW_PASS_H
