#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Support/raw_ostream.h"

// Include the new header files to get the full definitions of our passes.
#include "SubObfuscationPass.h"
#include "StringEncryptionPass.h"
#include "FunctionIndirectionPass.h"
#include "BogusControlFlowPass.h"

using namespace llvm;

extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
  return {
    LLVM_PLUGIN_API_VERSION, "Obfuscator", "v0.1",
    [](PassBuilder &PB) {
      PB.registerPipelineParsingCallback(
          [](StringRef Name, FunctionPassManager &FPM,
             ArrayRef<PassBuilder::PipelineElement>) {
            if (Name == "subobf") {
              FPM.addPass(SubObfuscationPass());
              return true;
            }
            if (Name == "funcind") {
              FPM.addPass(FunctionIndirectionPass());
              return true;
            }
            if (Name == "bcfobf") {
              FPM.addPass(BogusControlFlowPass());
              return true;
            }
            return false;
          });

      PB.registerPipelineParsingCallback(
          [](StringRef Name, ModulePassManager &MPM,
             ArrayRef<PassBuilder::PipelineElement>) {
            if (Name == "strenc") {
              MPM.addPass(StringEncryptionPass());
              return true;
            }
            return false;
          });
    }
  };
}
