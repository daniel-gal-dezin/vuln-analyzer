import re
from llama_cpp import Llama, llama_cpp
import os


class LLMEngine:
    def __init__(self, model_path="models/phi-4.Q4_1.gguf", n_ctx=4096, n_threads=8):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        print(f"Loading model from {model_path}")
        # Use the Phi-4 model again (4 K context window)
        self.model = Llama(model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        verbose=True)


    def generate_text(self, prompt: str, max_tokens: int = 512):
        """Send prompt to the model and return the **final** text.

        We disable streaming so we only get the completed response, and we use a low
        temperature plus a mild repetition penalty to encourage the model to follow
        the strict format we asked for.
        """
        print("sending prompt to model")
        completion = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.4,
            top_p=0.9,          # add this back
            repeat_penalty=1.3, # a tad lower so it can mention several lines
            stop=["</s>"]
        )

        return completion["choices"][0]["text"].strip()


    def analyze_file(self, file_path: str, max_tokens: int = 512):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.read().splitlines()

        blocks: list[tuple[str, int]] = []
        current_block: list[str] = []
        token_count = 0
        start_line = 1

        # Single pass to split the file into blocks that fit into max_tokens
        for line_no, line in enumerate(lines, start=1):
            words_in_line = len(line.split())

            # If adding this line would exceed the limit, start a new block first
            if token_count + words_in_line > max_tokens and current_block:
                blocks.append(("\n".join(current_block), start_line))
                current_block = []
                token_count = 0
                start_line = line_no        # next block starts here

            current_block.append(line)
            token_count += words_in_line

        # Add the final block (if any)
        if current_block:
            blocks.append(("\n".join(current_block), start_line))

        issues: list[str] = []
        for i, (block, start_line) in enumerate(blocks, start=1):
            # Optional progress print
            print(f"\n🧩 Processing block {i}/{len(blocks)} (≈{len(block.split())} words)…")

            prompt = f"""
                    You are a secure C/C++ code reviewer.
                    You are given a code block and you need to analyze it for vulnerabilities.

                    OUTPUT RULES – read carefully:
                    • Output **ONLY** lines that match this template:
                    # analyzer {os.path.basename(file_path)}
                    Line <number>: <vulnerability-type> — <brief cause> — FIX: <brief fix>

                    • Do NOT add headings, bullets, blank lines, explanations, “warning” text,
                    or repeat the code.  
                    • If no issues are found, output exactly:
                    # analyzer {os.path.basename(file_path)}
                    No vulnerabilities found.

                    The first line of this block is **line {start_line}** in the original file.
                    Report absolute line numbers (do not start again at 1).
                    BEGIN CODE
                    ------------------------------
                    {block}
                    ------------------------------
                    END CODE

                    pay attention not to repeat the code!! answer just in the next template,
                    Line <number>: <vulnerability-type> — <brief cause> — FIX: <brief fix>.
                    """

            raw_response = self.generate_text(prompt, max_tokens=max_tokens)

            LINE_RE = re.compile(r'^\s*Line +\d+\s*[:–-]')  # colon or dash
            issues.extend(
                ln.rstrip() for ln in raw_response.splitlines() if LINE_RE.match(ln)
            )

        LINE_RE = re.compile(r'^\s*Line +\d+')
        unique_sorted = sorted(
            set(issues),
            key=lambda s: int(re.search(r'\d+', s).group())
        )

        if not unique_sorted:
            final_output = f"# analyzer {os.path.basename(file_path)}\nNo vulnerabilities found."
        else:
            final_output = "\n".join(unique_sorted)

        print("\n=== FINAL REPORT ===\n" + final_output)

        return final_output