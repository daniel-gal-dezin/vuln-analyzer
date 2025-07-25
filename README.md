# VULN-ANALYZER: Complete Workflow Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Application Components](#application-components)
5. [Detailed Workflow](#detailed-workflow)
6. [Usage Examples](#usage-examples)
7. [Docker Deployment](#docker-deployment)
8. [Development Guide](#development-guide)
9. [Troubleshooting](#troubleshooting)

---

## Overview

**Vuln-Analyzer** is an LLM-powered vulnerability scanner specifically designed for C/C++ source code. It uses a local Large Language Model (via llama-cpp-python) to analyze code and identify potential security vulnerabilities, buffer overflows, memory leaks, and other common C/C++ programming issues.

### Key Features
- 🔍 **AI-Powered Analysis**: Uses local LLM for intelligent code understanding
- 📝 **Detailed Reports**: Provides line-specific vulnerability descriptions with fixes
- 🚀 **Batch Processing**: Can analyze multiple files in one command
- 🔧 **Configurable**: Adjustable model parameters and analysis settings
- 🐳 **Docker Support**: Ready-to-deploy containerized version
- 📊 **Structured Output**: Consistent report format for easy parsing

---

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │───▶│  LLM Engine     │───▶│ Local LLM Model │
│   (cli.py)      │    │  (llm_engine.py)│    │ (GGUF format)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ C/C++ Files     │    │ Text Chunking   │    │ Vulnerability   │
│ (input)         │    │ & Processing    │    │ Analysis        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                     ┌─────────────────┐
                     │ Report Output   │
                     │ (formatted)     │
                     └─────────────────┘
```

---

## Installation & Setup

### 🐳 Quick Start with Docker (Recommended)

**No dependencies needed!** Everything is pre-built in the Docker container.

#### 1. Clone the Project
```bash
git clone https://github.com/daniel-gal-dezin/vuln-analyzer.git
cd vuln-analyzer
```

#### 2. Build Docker Image
```bash
docker build -t vuln-analyzer .
```

#### 3. Download a Model
You need a GGUF model file:
- **Phi-4** (Recommended): ~7GB, good for code analysis
- **Code Llama**: ~4GB, specialized for programming
- **Phi-3-mini**: ~2GB, faster but less accurate

```bash
mkdir models
# Download your chosen model to models/phi-4-Q4_1.gguf
# Example: wget https://huggingface.co/microsoft/Phi-4-GGUF/resolve/main/phi-4-q4_1.gguf -O models/phi-4-Q4_1.gguf
```

#### 4. Run Analysis
```bash
# Analyze a file
docker run --rm \
  -v ./models:/app/models \
  -v ./:/data \
  vuln-analyzer analyze /data/library.c

# Get help
docker run --rm vuln-analyzer --help
```

**That's it!** No Python setup, no dependency issues, no compilation needed.

### 🤔 Docker vs Manual Installation

| Method | Pros | Cons | When to Use |
|--------|------|------|-------------|
| **🐳 Docker** | ✅ No dependencies<br/>✅ Consistent environment<br/>✅ No compilation<br/>✅ Works everywhere | ❌ Requires Docker<br/>❌ Larger download | **Recommended for most users** |
| **💻 Manual** | ✅ Direct Python access<br/>✅ Faster startup<br/>✅ Easy debugging | ❌ Complex setup<br/>❌ Dependency issues<br/>❌ Long compilation | **Only for development** |

---

### 💻 Manual Installation (For Development Only)

Only use this if you want to modify the code or don't want to use Docker.

#### Prerequisites
- Python 3.10+
- C++ Build Tools (for llama-cpp-python compilation)
- 4+ GB RAM (recommended 8+ GB for larger models)

#### Steps
```bash
# 1. Create Virtual Environment
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate

# 2. Install Dependencies (this takes time!)
pip install llama-cpp-python==0.3.14
pip install -e .

# 3. Download model (same as Docker method)
mkdir models
# Download model to models/phi-4-Q4_1.gguf

# 4. Run
python -m cli analyze library.c
```

---

## Application Components

### 1. **cli.py** - Command Line Interface
**Purpose**: Main entry point for user interaction

**Key Functions**:
- `main()`: Entry point, parses arguments and routes commands
- `build_parser()`: Defines CLI arguments and options
- `cmd_analyze()`: Handles the analysis command

**Available Arguments**:
```bash
vuln-analyzer analyze [FILES...] [OPTIONS]

Options:
  -m, --model PATH       Model file path (default: models/phi-4-Q4_1.gguf)
  -t, --tokens NUM       Max tokens per block (default: 512)
  -j, --threads NUM      CPU threads (default: 8)
  --ctx NUM             Context window size (default: 4096)
  -v, --verbose         Show raw model output
  --nosplit             Analyze entire file at once
```

### 2. **llm_engine.py** - LLM Processing Engine
**Purpose**: Handles all LLM interactions and text processing

**Key Classes**:
- `LLMEngine`: Main engine for model loading and inference

**Key Methods**:
- `__init__()`: Loads the GGUF model using llama-cpp-python
- `generate_text()`: Sends prompts to model and gets responses
- `analyze_file()`: Main analysis logic with chunking and processing

**Text Chunking Strategy**:
1. Reads source file line by line
2. Splits into blocks based on token limit (approximated by word count)
3. Each block maintains line number context
4. Processes blocks independently to handle large files





## Detailed Workflow

### Phase 1: Initialization
```
1. CLI parses command-line arguments
2. LLMEngine loads the specified GGUF model
3. Model initializes with:
   - Context window (n_ctx): Memory for conversation
   - Thread count (n_threads): CPU cores to use
   - Verbose mode: Debug output control
```

### Phase 2: File Processing
```
1. For each input file:
   a. Verify file exists and is readable
   b. Read all lines into memory
   c. Calculate text chunking strategy:
      - If --nosplit: Send entire file as one block
      - Else: Split by token budget (approximated by words)
   d. Create blocks with line number tracking
```

### Phase 3: AI Analysis
```
1. For each text block:
   a. Construct analysis prompt with:
      - Security-focused instructions
      - Code block with line numbers
      - Output format requirements
      - Context about file type (C/C++)
   
   b. Send to LLM with parameters:
      - Temperature: 0.4 (focused, deterministic)
      - Max tokens: Configurable (default 512)
      - Stop sequences: ["</s>"] (end of response)
      - Repeat penalty: 1.3 (avoid repetition)
   
   c. Process model response:
      - Extract vulnerability lines using regex
      - Filter out headers and non-vulnerability text
      - Validate line format matches expected pattern
```

### Phase 4: Report Generation
```
1. Collect all vulnerability findings
2. Deduplicate identical findings
3. Sort by line number (ascending)
4. Format final report:
   - Header with filename
   - List of vulnerabilities or "No vulnerabilities found"
   - Each vulnerability shows: Line, Type, Cause, Fix suggestion
```

### Example Prompt Structure
```
You are a secure C/C++ code reviewer.
You are given a code block and you need to analyze it for vulnerabilities.

Make sure to identify **every** vulnerability or security flaw in the code.

OUTPUT RULES:
• Output **ONLY** lines that match this template:
Line <number>: <vulnerability-type> — <brief cause> — FIX: <brief fix>

• Do NOT add headings, bullets, blank lines, explanations
• If no issues are found, output exactly:
No vulnerabilities found.

The first line of this block is **line 45** in the original file.
Report absolute line numbers.

ANALYZE THIS CODE FOR SECURITY VULNERABILITIES:
------------------------------
char buffer[10];
gets(buffer);  // Vulnerable function
printf(buffer); // Format string vulnerability
------------------------------
PROVIDE ONLY THE VULNERABILITY ANALYSIS ABOVE, NOT THE CODE.
```

### Example Expected Output
```
Line 46: Buffer Overflow — gets() doesn't check bounds — FIX: Use fgets() with size limit
Line 47: Format String Vulnerability — User input passed directly to printf — FIX: Use printf("%s", buffer)
```

---

## Usage Examples

### Basic File Analysis
```bash
# Analyze single file
vuln-analyzer analyze vulnerable.c

# Analyze multiple files
vuln-analyzer analyze file1.c file2.cpp file3.c
```

### Advanced Usage
```bash
# Use different model
vuln-analyzer analyze code.c -m models/codellama-7b.gguf

# Increase analysis depth (more tokens)
vuln-analyzer analyze code.c -t 1024

# Debug mode (see raw LLM output)
vuln-analyzer analyze code.c --verbose

# Analyze large file without splitting
vuln-analyzer analyze huge_file.c --nosplit

# Performance tuning
vuln-analyzer analyze code.c -j 16 --ctx 8192
```

### Batch Processing Script
```bash
#!/bin/bash
# Analyze all C files in project
find . -name "*.c" -o -name "*.cpp" | xargs vuln-analyzer analyze
```

---

## Docker Advanced Usage

### Additional Examples
```bash

# Analyze file
docker run --rm \
  -v ./models:/app/models \
  -v ./:/data \
  vuln-analyzer analyze /data/file1.c 
  #--------------> syntax for linux



   docker run --rm 
   -v "$(pwd)/models:/app/models" 
   -v "$(pwd):/data" 
   vuln-analyzer analyze /data/notes.cpp  #----------------------->syntax for windows






# Analyze multiple files
docker run --rm \
  -v ./models:/app/models \
  -v ./:/data \
  vuln-analyzer analyze /data/file1.c /data/file2.cpp

# Use different model
docker run --rm \
  -v ./models:/app/models \
  -v ./:/data \
  vuln-analyzer analyze /data/code.c -m /app/models/different-model.gguf

# Verbose mode with custom settings
docker run --rm \
  -v ./models:/app/models \
  -v ./:/data \
  vuln-analyzer analyze /data/code.c --verbose -t 800 -j 16

# Interactive shell (for debugging)
docker run -it --rm \
  -v ./models:/app/models \
  -v ./:/data \
  vuln-analyzer bash
```

### Docker Compose Example
```yaml
version: '3.8'
services:
  vuln-analyzer:
    build: .
    volumes:
      - ./models/phi-4-Q4_1.gguf:/app/models/phi-4-Q4_1.gguf
      - ./src:/data
    command: analyze /data/main.c
```

---

## Development Guide

### Project Structure
```
vuln-analyzer/
├── cli.py              # Main CLI interface
├── llm_engine.py       # LLM processing engine
├── setup.py           # Package configuration
├── Dockerfile         # Container build instructions
├── .dockerignore      # Docker build exclusions
├── library.c          # Example vulnerable C code
├── notes.cpp          # Example vulnerable C++ code
├── models/            # Directory for GGUF model files
└── .venv/            # Python virtual environment
```

### Adding New Features

#### 1. New Analysis Rules
Edit the prompt in `llm_engine.py` around line 120:
```python
prompt = f"""
You are a secure C/C++ code reviewer.
# Add your new instructions here
# Example: Pay special attention to cryptographic functions
"""
```

#### 2. New Output Formats
Modify the regex pattern in `llm_engine.py` around line 125:
```python
LINE_RE = re.compile(
    r"^\s*Line[s]?\s+\d+(?:\s*(?:-|–|—|,|/|&)\s*\d+)*\s*:\s*"
    r"[A-Za-z][^–—-]*[–—-]",  # Current pattern
    re.IGNORECASE,
)
```

#### 3. New CLI Options
Add to `build_parser()` in `cli.py`:
```python
scan.add_argument("--new-option", 
                  help="Description of new option")
```

### Testing During Development
```bash
# Test CLI changes
python -m cli analyze test.c --verbose

# Test engine changes directly
python -c "
from llm_engine import LLMEngine
engine = LLMEngine(debug=True)
print(engine.analyze_file('test.c'))
"

# Test with different models
python -m cli analyze test.c -m models/different-model.gguf
```

---

## Troubleshooting

### Common Issues

#### 1. Model Not Found
```
Error: Model file not found: models/phi-4-Q4_1.gguf
```
**Solution**: 
- Download a GGUF model file
- Place in `models/` directory  
- Use `-m` flag to specify different path

#### 2. llama-cpp-python Installation Issues
```
ERROR: Failed building wheel for llama-cpp-python
```
**Solutions**:
- **Windows**: Install Visual Studio Build Tools 2022
- **Linux**: Install `build-essential cmake`
- **All**: Use pre-built wheel: `pip install llama-cpp-python --prefer-binary`

#### 3. Memory Issues
```
RuntimeError: CUDA out of memory / Killed (OOM)
```
**Solutions**:
- Reduce context window: `--ctx 2048`
- Reduce max tokens: `-t 256`  
- Use smaller model
- Add more RAM/swap

#### 4. Slow Performance
**Optimizations**:
- Increase thread count: `-j 16`
- Use GPU acceleration (if available)
- Use quantized models (Q4, Q5)
- Enable CPU optimizations in llama-cpp-python

#### 5. No Vulnerabilities Detected
**Debugging**:
- Use `--verbose` to see raw LLM output
- Try different model (some are better at security analysis)
- Increase token limit for more detailed analysis
- Check if code actually has vulnerabilities

#### 6. Docker Issues
```
docker: permission denied
```
**Solution**: Add user to docker group or use `sudo`

```
Model loading fails in container
```
**Solution**: Ensure model file is properly mounted and readable

### Performance Tuning

#### Model Selection
- **Fast**: Small quantized models (Q4_0, Q4_1)
- **Accurate**: Larger models (Q5_1, Q8_0)
- **Balanced**: Q4_1 or Q5_0 variants

#### Hardware Optimization
```bash
# CPU-optimized
vuln-analyzer analyze code.c -j $(nproc) --ctx 4096

# Memory-constrained
vuln-analyzer analyze code.c --ctx 2048 -t 256

# small file handling
vuln-analyzer analyze big_file.c --nosplit -t 2048
```

#### Batch Processing Tips
```bash
# Process files in parallel
find . -name "*.c" | xargs -P 4 -I {} vuln-analyzer analyze {}

# Save results to files
vuln-analyzer analyze code.c > results/code_analysis.txt
```

---

## Advanced Configuration

### Environment Variables
```bash
export VULN_ANALYZER_MODEL="/path/to/model.gguf"
export VULN_ANALYZER_THREADS=16
export VULN_ANALYZER_CTX=8192
```

### Configuration File Support
Create `~/.vuln-analyzer.conf`:
```ini
[default]
model = /home/user/models/phi-4-Q4_1.gguf
threads = 8
context = 4096
tokens = 512
```

### Integration with CI/CD
```yaml
# GitHub Actions example
- name: Security Analysis
  run: |
    vuln-analyzer analyze src/**/*.c > security_report.txt
    if grep -q "Line.*:" security_report.txt; then
      echo "Security vulnerabilities found!"
      exit 1
    fi
```

---

## Conclusion

The vuln-analyzer provides a powerful, AI-driven approach to C/C++ security analysis. By combining local LLM inference with structured prompting and intelligent text processing, it offers detailed vulnerability detection while maintaining privacy and control over your code.

The modular architecture makes it easy to extend, customize, and integrate into existing development workflows. Whether used as a standalone tool, CI/CD component, or Docker service, vuln-analyzer helps improve code security through automated, intelligent analysis.

For additional support, check the project repository or create issues for bugs and feature requests. 
