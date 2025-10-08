#include "FunctionIndirectionPass.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/Instructions.h"
#include "llvm/Support/raw_ostream.h"
#include <vector>

using namespace llvm;

PreservedAnalyses FunctionIndirectionPass::run(Function &F, FunctionAnalysisManager &AM) {
  // Add a filter to prevent this pass from running on sensitive functions.
  StringRef funcName = F.getName();
  if (funcName.startswith(".master_decryptor") || 
      funcName.startswith("inplace_decrypt_runtime") ||
      funcName.startswith("__cxx_global_var_init") ||
      funcName.startswith("_GLOBAL__sub_I_")) {
    return PreservedAnalyses::all();
  }

  bool IRWasModified = false;
  std::vector<CallInst*> toModify;

  for (BasicBlock &BB : F) {
    for (Instruction &I : BB) {
      if (auto *CI = dyn_cast<CallInst>(&I)) {
        Function *calledFunc = CI->getCalledFunction();
        
        if (calledFunc && !calledFunc->isIntrinsic() && !calledFunc->isDeclaration()) {
          StringRef calledFuncName = calledFunc->getName();
          if (!calledFuncName.startswith("_Z")) {
            toModify.push_back(CI);
          }
        }
      }
    }
  }

  if (toModify.empty()) {
    return PreservedAnalyses::all();
  }

  for (CallInst *originalCall : toModify) {
    Function *calledFunc = originalCall->getCalledFunction();
    Module *M = F.getParent();
      
    errs() << "Applying indirection to call of function: " << calledFunc->getName() << "\n";

    Type *funcPtrType = calledFunc->getType();
    GlobalVariable *funcPtr = new GlobalVariable(
        *M, funcPtrType, false, GlobalValue::PrivateLinkage, calledFunc,
        "ptr_" + calledFunc->getName());

    IRBuilder<> builder(originalCall);
    LoadInst *loadedFunc = builder.CreateLoad(funcPtrType, funcPtr);

    std::vector<Value*> args;
    for (const auto &arg : originalCall->args()) {
      args.push_back(arg);
    }
    CallInst *newCall = builder.CreateCall(calledFunc->getFunctionType(), loadedFunc, args);

    originalCall->replaceAllUsesWith(newCall);
    originalCall->eraseFromParent();
    IRWasModified = true;
  }

  return IRWasModified ? PreservedAnalyses::none() : PreservedAnalyses::all();
}
