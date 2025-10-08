#include "BogusControlFlowPass.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/Support/raw_ostream.h"
#include <vector>
#include <cstdlib> // Required for std::getenv and std::atoi

using namespace llvm;

PreservedAnalyses BogusControlFlowPass::run(Function &F, FunctionAnalysisManager &AM) {
  // Filter for sensitive functions
  StringRef funcName = F.getName();
  if (funcName.startswith(".master_decryptor") || 
      funcName.startswith("inplace_decrypt_runtime") ||
      funcName.startswith("__cxx_global_var_init") ||
      funcName.startswith("_GLOBAL__sub_I_")) {
    return PreservedAnalyses::all();
  }
  
  // --- THIS IS THE FIX ---
  // Read the obfuscation level without using exception handling.
  int obfuscationLevel = 1; // Default level
  if (const char* levelStr = std::getenv("BCF_LEVEL")) {
    int parsedLevel = std::atoi(levelStr); // Use atoi which returns 0 on error
    if (parsedLevel > 0) {
      obfuscationLevel = parsedLevel;
    }
  }

  bool IRWasModified = false;
  int bogusBlocksAdded = 0;
  int fakeLoopsAdded = 0;
  
  for (int i = 0; i < obfuscationLevel; ++i) {
    std::vector<BasicBlock*> originalBlocks;
    for (BasicBlock &BB : F) {
      originalBlocks.push_back(&BB);
    }

    for (BasicBlock *BB : originalBlocks) {
      if (BB->size() > 1 && BB->getTerminator() && !BB->getTerminator()->mayThrow()) {
        Instruction *splitPoint = &*(++BB->begin());
        BasicBlock *splitBlock = BB->splitBasicBlock(splitPoint, "split_block");

        BasicBlock *bogusBlock = BasicBlock::Create(F.getContext(), "bogus_block", &F, splitBlock);
        IRBuilder<> bogusBuilder(bogusBlock);
        
        Type *Int32Ty = Type::getInt32Ty(F.getContext());
        Value *startVal = ConstantInt::get(Int32Ty, 0);
        Value *endVal = ConstantInt::get(Int32Ty, 10);
        
        BasicBlock *loopHeader = BasicBlock::Create(F.getContext(), "fake.loop.header", &F, splitBlock);
        BasicBlock *loopBody = BasicBlock::Create(F.getContext(), "fake.loop.body", &F, splitBlock);
        
        bogusBuilder.CreateBr(loopHeader);
        
        bogusBuilder.SetInsertPoint(loopHeader);
        PHINode *iv = bogusBuilder.CreatePHI(Int32Ty, 2, "i");
        iv->addIncoming(startVal, bogusBlock);
        Value *cond = bogusBuilder.CreateICmpSLT(iv, endVal, "cond");
        bogusBuilder.CreateCondBr(cond, loopBody, splitBlock);
        
        bogusBuilder.SetInsertPoint(loopBody);
        Value *next_iv = bogusBuilder.CreateAdd(iv, ConstantInt::get(Int32Ty, 1));
        iv->addIncoming(next_iv, loopBody);
        bogusBuilder.CreateBr(loopHeader);

        fakeLoopsAdded++;

        auto *oldTerminator = BB->getTerminator();
        IRBuilder<> builder(oldTerminator);
        Value *opaquePredicate = ConstantInt::getTrue(F.getContext());
        builder.CreateCondBr(opaquePredicate, splitBlock, bogusBlock);
        oldTerminator->eraseFromParent();
        
        bogusBlocksAdded++;
        IRWasModified = true;
        goto next_iteration;
      }
    }
    next_iteration:;
  }

  if (IRWasModified) {
    errs() << "BogusControlFlowPass: " << bogusBlocksAdded << " bogus blocks added in function " << F.getName() << ".\n";
    errs() << "BogusControlFlowPass: " << fakeLoopsAdded << " fake loops inserted in function " << F.getName() << ".\n";
  }

  return IRWasModified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}