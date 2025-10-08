#!/bin/bash

# --- Configuration ---
PASS_LIB_PATH="/path/to/be/replaced/by/install.sh"
CLANG=$(command -v clang++-15)
OPT=$(command -v opt-15)

# --- Argument Parsing Loop ---
INPUT_FILE=""
OUTPUT_NAME="a.out"
CYCLES=1      # Default to 1 cycle
BCF_LEVEL=1   # Default to 1 bogus block per function
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --cycles)
      CYCLES="$2"; shift; shift;;
    -o)
      OUTPUT_NAME="$2"; shift; shift;;
    # --- NEW: Handle --bcf-level ---
    --bcf-level)
      BCF_LEVEL="$2"; shift; shift;;
    *) 
      if [ -z "$INPUT_FILE" ]; then INPUT_FILE="$1"; fi
      shift;;
  esac
done

# --- Pre-flight Checks ---
if [ -z "$CLANG" ] || [ -z "$OPT" ]; then echo "❌ Error: clang++-15 or opt-15 not found."; exit 1; fi
if [ -z "$INPUT_FILE" ]; then echo "Usage: $0 <input.cpp> [-o <out>] [--cycles <N>] [--bcf-level <N>]"; exit 1; fi

if [ "$PASS_LIB_PATH" == "/path/to/be/replaced/by/install.sh" ]; then
    PASS_LIB_PATH="$(pwd)/build/libObfuscationPasses.so"
fi
if [ ! -f "$PASS_LIB_PATH" ]; then
  echo "❌ Error: Pass library not found at $PASS_LIB_PATH.";
  exit 1
fi

# --- Main Logic ---
echo "--- LLVM Obfuscator Tool ---"
declare -A ALL_PASSES
ALL_PASSES[1]="subobf"; ALL_PASSES[2]="strenc"; ALL_PASSES[3]="funcind"; ALL_PASSES[4]="bcfobf"
echo "Available Obfuscation Passes:"
echo "  1. Instruction Substitution (subobf)"; echo "  2. String Encryption (strenc)";
echo "  3. Function Indirection (funcind)"; echo "  4. Bogus Control Flow (bcfobf)"; echo ""
read -p "Enter the pass numbers to apply (e.g., 1,3,4 or 'all'): " USER_CHOICE
SELECTED_PASSES=()
if [ "$USER_CHOICE" == "all" ]; then
  for i in {1..4}; do SELECTED_PASSES+=(${ALL_PASSES[$i]}); done
else
  IFS=',' read -ra CHOICES <<< "$USER_CHOICE"
  for choice in "${CHOICES[@]}"; do
    if [[ -n ${ALL_PASSES[$choice]} ]]; then SELECTED_PASSES+=(${ALL_PASSES[$choice]}); fi
  done
fi
if [ ${#SELECTED_PASSES[@]} -eq 0 ]; then echo "❌ Error: No valid passes selected."; exit 1; fi
echo "✅ Passes selected: $(IFS=,; echo "${SELECTED_PASSES[*]}")"; echo ""
echo "⚙️  Starting the obfuscation process..."

# --- Path Definitions ---
OUTPUT_DIR=$(dirname "$INPUT_FILE")
IR_FILE="$OUTPUT_DIR/temp.ll"
OBF_IR_FILE="$OUTPUT_DIR/temp.obf.ll"
OBJ_FILE="$OUTPUT_DIR/temp.o"
FINAL_OUTPUT_PATH="$OUTPUT_DIR/$OUTPUT_NAME"
REPORT_PATH="$OUTPUT_DIR/report.txt"

# --- Obfuscation Steps ---
echo "    [1/4] Compiling $INPUT_FILE to LLVM IR..."
$CLANG -S -emit-llvm -Xclang -disable-O0-optnone "$INPUT_FILE" -o "$IR_FILE"
if [ $? -ne 0 ]; then echo "❌ Error: clang failed to compile to IR."; exit 1; fi

# Construct the pass argument string
MODULE_PASSES=(); FUNCTION_PASSES=()
for pass in "${SELECTED_PASSES[@]}"; do
  if [[ "$pass" == "strenc" ]]; then MODULE_PASSES+=("$pass"); else FUNCTION_PASSES+=("$pass"); fi
done
PASS_ARG_PARTS=()
if [ ${#MODULE_PASSES[@]} -gt 0 ]; then PASS_ARG_PARTS+=($(IFS=,; echo "${MODULE_PASSES[*]}")); fi
if [ ${#FUNCTION_PASSES[@]} -gt 0 ]; then PASS_ARG_PARTS+=("function($(IFS=,; echo "${FUNCTION_PASSES[*]}"))"); fi
FINAL_PASS_ARG=$(IFS=,; echo "${PASS_ARG_PARTS[*]}")
echo "    --> Constructed opt argument: -passes=$FINAL_PASS_ARG"

# --- NEW: Export the BCF_LEVEL for the C++ pass to read ---
export BCF_LEVEL

# Obfuscation Loop
echo "    [2/4] Applying obfuscation passes for $CYCLES cycle(s)..."
CURRENT_IR_IN="$IR_FILE"
CURRENT_IR_OUT="$OUTPUT_DIR/temp.cycle.ll"
total_opt_output=""

for i in $(seq 1 $CYCLES); do
  echo "        -> Cycle $i of $CYCLES"
  opt_output=$($OPT -load-pass-plugin="$PASS_LIB_PATH" -passes="$FINAL_PASS_ARG" "$CURRENT_IR_IN" -S -o "$CURRENT_IR_OUT" 2>&1)
  if [ $? -ne 0 ]; then
    echo "❌ Error: opt failed during cycle $i."; echo "$opt_output"; exit 1
  fi
  total_opt_output+="$opt_output\n"
  mv "$CURRENT_IR_OUT" "$CURRENT_IR_IN"
done

mv "$CURRENT_IR_IN" "$OBF_IR_FILE"
echo -e "$total_opt_output"

echo "    [3/4] Compiling obfuscated IR to an object file..."
$CLANG -c "$OBF_IR_FILE" -o "$OBJ_FILE"
if [ $? -ne 0 ]; then echo "❌ Error: clang failed to compile obfuscated IR."; exit 1; fi

echo "    [4/4] Linking object file into the final executable..."
$CLANG "$OBJ_FILE" -o "$FINAL_OUTPUT_PATH"
if [ $? -ne 0 ]; then echo "❌ Error: clang failed to link executable."; exit 1; fi

echo "    [5/5] Generating report..."
num_strings=$(echo -e "$total_opt_output" | grep "strings encrypted" | awk '{s+=$2} END {print s}')
num_bogus_blocks=$(echo -e "$total_opt_output" | grep "bogus blocks added" | awk '{s+=$2} END {print s}')
num_fake_loops=$(echo -e "$total_opt_output" | grep "fake loops inserted" | awk '{s+=$2} END {print s}')
: ${num_strings:=0}; : ${num_bogus_blocks:=0}; : ${num_fake_loops:=0}
file_size=$(stat -c %s "$FINAL_OUTPUT_PATH")

cat > "$REPORT_PATH" << EOL
--- Obfuscation Report ---
Generated on: $(date)
### Input Parameters ###
Input File:              $INPUT_FILE
Selected Passes:         $(IFS=,; echo "${SELECTED_PASSES[*]}")
Cycles of Obfuscation:   $CYCLES
# --- NEW: Added BCF Level to Report ---
BCF Level:               $BCF_LEVEL

### Output File Attributes ###
Output Executable:       $FINAL_OUTPUT_PATH
Final Size:              $file_size bytes
### Obfuscation Details ###
Methods Used:            $(IFS=,; echo "${SELECTED_PASSES[*]}")
Strings Encrypted:       $num_strings
Bogus Code Blocks Added: $num_bogus_blocks
Fake Loops Inserted:     $num_fake_loops
EOL
rm "$OBF_IR_FILE" "$OBJ_FILE"

echo ""
echo "🎉 Success! Obfuscated executable created at: $FINAL_OUTPUT_PATH"
echo "📄 Report generated at: $REPORT_PATH"