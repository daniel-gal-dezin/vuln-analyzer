import os
import re
from llama_cpp import Llama


class LLMEngine:
    def __init__(self,
                 *,
                 model_path: str = "models/phi-4-Q4_1.gguf",
                 n_ctx: int = 4096,
                 n_threads: int = 8,
                 debug: bool = False):
        """Create a new LLM engine."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        print(f"Loading model from {model_path}")
        self.model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=True
        )
        self.debug = debug

    def generate_text(self, prompt: str, max_tokens: int = 512) -> str:
        """Send prompt to the model and return the final text."""
        completion = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.4,
            repeat_penalty=1.3,
            stop=["</s>"]
        )
        return completion["choices"][0]["text"].strip()

    def analyze_file(self,
                     file_path: str,
                     max_tokens: int = 256,
                     nosplit: bool = False) -> str:
        """Analyze a C/C++ source file for vulnerabilities."""

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read all lines
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        # Prepare for both split and nosplit flows
        token_count = 0
        current_block: list[str] = []
        start_line = 1

        if nosplit:
            # Send entire file as single block
            blocks = [("\n".join(lines), start_line)]
        else:
            # Split into blocks that fit within max_tokens
            blocks: list[tuple[str, int]] = []
            for line_no, line in enumerate(lines, start=1):
                words = len(line.split())
                if token_count + words > max_tokens and current_block:
                    blocks.append(("\n".join(current_block), start_line))
                    current_block = []
                    token_count = 0
                    start_line = line_no
                current_block.append(line)
                token_count += words

            if current_block:
                blocks.append(("\n".join(current_block), start_line))

        issues: list[str] = []
        # Regex to catch "Line 123:" or "Lines 12-14:" etc.
        LINE_RE = re.compile(r'^\s*Line[s]?\s+\d+([,\/\-\& ]\d+)*\s*[:–—-]', re.I)

        for idx, (block, blk_start) in enumerate(blocks, start=1):
            if not nosplit:
                print(f"🧩 Processing block {idx}/{len(blocks)}…")

            prompt = f"""
You are a secure C/C++ code reviewer.
You are given a code block and you need to analyze it for vulnerabilities.

OUTPUT RULES – read carefully:
• Output **ONLY** lines that match this template:
# analyzer {os.path.basename(file_path)}
Line <number>: <vulnerability-type> — <brief cause> — FIX: <brief fix>

• Do NOT add headings, bullets, blank lines, explanations, or repeat the code.
• If no issues are found, output exactly:
# analyzer {os.path.basename(file_path)}
No vulnerabilities found.

The first line of this block is **line {blk_start}** in the original file.
Report absolute line numbers.

BEGIN CODE
------------------------------
{block}
------------------------------
END CODE
"""

            raw = self.generate_text(prompt, max_tokens=max_tokens)

            if self.debug:
                print("\n--- RAW MODEL OUTPUT ---")
                print(raw)
                print("--- END RAW ---\n")

            for line in raw.splitlines():
                if LINE_RE.match(line):
                    issues.append(line.strip())

        # Deduplicate and sort by reported line number
        unique_sorted = sorted(
            set(issues),
            key=lambda s: int(re.search(r'\d+', s).group())
        )

        if not unique_sorted:
            return f"# analyzer {os.path.basename(file_path)}\nNo vulnerabilities found."
        return "\n".join(unique_sorted)
