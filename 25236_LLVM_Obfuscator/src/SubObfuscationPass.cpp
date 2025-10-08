#include "SubObfuscationPass.h" // Include the header
#include "llvm/IR/IRBuilder.h"
#include <vector>

using namespace llvm;

PreservedAnalyses SubObfuscationPass::run(Function &F, FunctionAnalysisManager &AM) {
  // ... (the rest of your existing code for this pass is unchanged) ...
  bool IRWasModified = false;
  std::vector<Instruction*> toDelete;

  for (BasicBlock &BB : F) {
    for (Instruction &I : BB) {
      if (auto *BinOp = dyn_cast<BinaryOperator>(&I)) {
        if (BinOp->getOpcode() == Instruction::Sub) {
          IRBuilder<> builder(BinOp);
          Value *LHS = BinOp->getOperand(0);
          Value *RHS = BinOp->getOperand(1);
          Value *NegRHS = builder.CreateNeg(RHS, "neg_op");
          Value *AddLHSNegRHS = builder.CreateAdd(LHS, NegRHS, "add_op");
          BinOp->replaceAllUsesWith(AddLHSNegRHS);
          toDelete.push_back(BinOp);
          IRWasModified = true;
        }
      }
    }
  }

  for (Instruction *I : toDelete) {
    I->eraseFromParent();
  }

  return IRWasModified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}
