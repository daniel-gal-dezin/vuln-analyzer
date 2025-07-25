
**Vulnerability Analyzer Development Report Overview**
In this assignment I was tasked with creating a vulnerability scanner for C/C++ source files, powered by a local large‑language model (LLM). The primary goal was to deliver a command‑line tool that could accept one or more source files, analyse them using an LLM, and output any vulnerabilities in a well‑defined format:


# analyzer <file>
Line <number>: <vulnerability‑type> — <brief cause> — FIX: <brief fix>
If no vulnerabilities were found, the tool should instead output:
# analyzer <file>
No vulnerabilities found.



Alongside this, the project needed to be packaged into a Python package with a setup.py, include a CLI with useful options, and be deployable via Docker. My report here outlines my decision‑making and the sequence of improvements I made while building and refining the tool.

Initial Setup
I began by reviewing the assignment specification (in exercise-oss-sw-engineer.pdf) to extract the critical requirements. The tool had to:

Load a local LLM (via the llama_cpp library) and analyse C/C++ source code.

Support scanning one or more files from the command line.

Produce structured output matching the required format.

Be installable as a package (pip install .) and include a working CLI.

Provide a Dockerfile for containerised deployment.

first i built the classes files—cli.py, llm_engine.py, and a simple analyzer.py script—to understand how the tool currently worked. This initial version did some of the required tasks, but there were several shortcomings around prompt construction, output parsing, packaging, and runtime efficiency.

Understanding the LLM and Prompting
The first challenge was ensuring that the LLM understood and followed the instructions. I noticed that the initial implementation simply passed a large text prompt to the model using a “completion” API. While this might work for older text‑only models, the Phi‑4 model we wanted to use expects a chat‑style prompt with separate system and user messages. Without that, the model often echoed the code block back verbatim and failed to list any vulnerabilities.

To address this, I added a chat‑aware interface to LLMEngine. The generate_text method now detects whether the model supports chat (via the create_chat_completion method). For chat models it constructs a system message (“You are a secure C/C++ code reviewer…”) and a user message containing the full instructions and code block. This change alone made the model much more reliable in returning vulnerability lists.

Splitting Large Files vs. Full Context
Another consideration was how to handle large source files. The assignment allowed for splitting a file into multiple blocks to fit within the model’s context window. Initially the code used a rough estimate of token count by counting words, but this could under‑ or over‑estimate the length of each block. I debated writing a tokeniser call using the model’s own tokenize method, but due to time constraints I kept the approximate approach and documented it. I did however add a --nosplit option to let the user send the entire file at once, which is often better for small files because it preserves full context and avoids missing vulnerabilities across chunk boundaries.

Parsing Model Responses
One of the trickiest aspects was determining which lines of the model’s response actually represented vulnerabilities. The original implementation captured any line that started with “Line ” and a colon, which unfortunately also matched benign lines like #include <iostream>. To filter more accurately, I wrote a regular expression that requires a colon, at least one alphabetic character (the vulnerability type) and an en‑dash or em‑dash separating the type from the explanation. This helped ensure we only captured lines in the prescribed “Line X: Type — Cause — FIX: …” format.

I also added logic to deduplicate lines (in case the model repeated itself), sort them by line number, and always prepend a header with the file name. If nothing matched, the engine now returns # analyzer <file>\nNo vulnerabilities found. which satisfies the specification.

Improving the CLI
The initial CLI in cli.py provided basic options, but it lacked helpful descriptions. I expanded the help text, particularly for the --nosplit flag, to explain why sending the entire file at once might yield better results (full context) and when splitting is useful (large files or limited memory). I also made the CLI print a scan banner and clearly separate each report.

Another small improvement was handling errors gracefully. The CLI now catches exceptions per file, prints a friendly error message, and continues scanning other files rather than exiting immediately.

Packaging and Setup
To make the tool installable, I created a setup.py that declares the package metadata, lists llama-cpp-python as a dependency (pinned to the version used during development), and exposes a console entry point vuln-analyzer. I removed unnecessary dependencies (like argparse, which is part of the standard library) and tested that pip install -e . installed the tool correctly. I also added a .dockerignore to avoid copying large model files into the image.

Dockerization
I wrote a lightweight Dockerfile based on python:3.11-slim. It installs build tools needed for llama-cpp-python, copies over the project files, runs pip install ., and sets the default entry point to the vuln-analyzer CLI. To conserve space, I removed unused packages such as git. The Docker image expects the user to mount their GGUF model file via a volume, keeping the image small and flexible.

Testing and Iteration
With the core engine and CLI in place, I tested the scanner against the provided notes.cpp file. Early runs produced no vulnerabilities because the model output was simply the echoed code block; switching to the chat API fixed that. I also experimented with different token budgets and context sizes. I found that increasing the --tokens limit (e.g. to 1024) helped the model list more issues without cutting off early, while --ctx 4096 was sufficient for most files, given my available RAM. For very large files I documented that the user should omit --nosplit to let the tool automatically chunk the input.

Final Thoughts and Next Steps
In the end, the tool meets the core requirements: it loads a local LLM, scans C/C++ files, and outputs a clear, structured report. Along the way I had to refine prompt engineering, improve regex parsing, enhance the CLI, and make the project installation‑friendly. If I had more time, I would:

Use the LLM’s tokeniser to accurately count input tokens and split files more predictably.

Provide multiple prompt templates (e.g. for different models or languages) and allow the user to select them.

Add unit tests for the engine and CLI to guard against regressions.

Explore asynchronous or parallel processing for scanning multiple files faster.

Implement model fine-tuning through pre-training on security-focused datasets to improve vulnerability detection accuracy.

Add agent-to-agent communication where a second LLM agent reviews and sharpens the initial analysis results for higher precision.

Integrate LoRA (Low-Rank Adaptation) modules to optimize model calculations and enable efficient fine-tuning without full model retraining.

Overall, this exercise was a valuable exploration into orchestrating a local LLM for static code analysis, balancing the model’s capabilities with careful prompting and practical engineering choices.