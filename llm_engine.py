import os
import re

# Attempt to import llama_cpp.  In environments where it is not
# installed, we delay failure until the engine is initialized so we can
# produce a clear error message.
try:
    from llama_cpp import Llama  # type: ignore
except ImportError:
    Llama = None  # type: ignore[misc]


class LLMEngine:
    def __init__(
        self,
        *,
        model_path: str = "models/phi-4-Q4_1.gguf",
        n_ctx: int = 4096,
        n_threads: int = 8,
        debug: bool = False,
    ) -> None:
        """Create a new LLM engine.

        :param model_path: Path to the GGUF model to load.
        :param n_ctx: Context window size for the model.
        :param n_threads: Number of CPU threads to use.
        :param debug: If True, prints raw model output for debugging.
        """
        # Ensure the model file exists before attempting to load it.
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Verify that the llama_cpp module is available.  If not,
        # provide a helpful error.  This avoids confusing failures
        # elsewhere if llama_cpp is missing.
        if Llama is None:
            raise ImportError(
                "llama_cpp is not installed. Please install the `llama-cpp-python` "
                "package to use LLMEngine."
            )

        print(f"Loading model from {model_path}")
        # Initialize the Llama model with provided settings.
        self.model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=True,
        )
        self.debug = debug

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 512,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """Generate text from the model given a prompt.

        If the underlying model supports chat completions (as required by
        some chat-format GGUF models such as Phi‑4), this method will
        automatically call `create_chat_completion` with a system and
        user message.  Otherwise it falls back to using the raw prompt
        string.

        :param prompt: The user message or full prompt to send.
        :param max_tokens: Maximum number of tokens to generate.
        :param system_prompt: Optional system prompt for chat models.
        :return: The generated text with leading/trailing whitespace stripped.
        """
        # If the model exposes create_chat_completion (chat interface), use it
        if hasattr(self.model, "create_chat_completion"):
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                # For chat models, we send the remaining prompt as a user message.
                messages.append({"role": "user", "content": prompt})
            else:
                messages.append({"role": "user", "content": prompt})
            response = self.model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.4,
                repeat_penalty=1.3,
            )
            # Depending on the API version, the generated text may be under
            # 'message'->'content' or directly under 'choices'->'text'.  We
            # attempt to access both.
            choice = response.get("choices", [{}])[0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
            if "text" in choice:
                return choice["text"].strip()
            # Fallback: return empty string
            return ""

        # For legacy models, use the original text completion API
        completion = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            repeat_penalty=1.3,
            stop=["</s>"],
        )
        return completion["choices"][0]["text"].strip()

    def analyze_file(
        self,
        file_path: str,
        max_tokens: int = 256,
        nosplit: bool = False,
    ) -> str:
        """Analyze a C/C++ source file for potential vulnerabilities.

        The file is optionally split into blocks to fit within the model's
        token budget.  Each block is sent to the model with instructions
        specifying how to format its response.  The results are
        aggregated, deduplicated, and sorted by line number.

        :param file_path: Path to the source file.
        :param max_tokens: The generation budget for each block.
        :param nosplit: If True, send the entire file as a single block.
        :return: A report string summarizing discovered vulnerabilities.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read all lines from the file.
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        # Determine how to split the file into blocks.  Each block is a
        # tuple (block_text, starting_line_number).  Splitting by words
        # approximates token count, helping to fit within max_tokens.
        token_count = 0
        current_block: list[str] = []
        start_line = 1
        if nosplit:
            blocks = [("\n".join(lines), start_line)]
        else:
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

        # Collect vulnerability descriptions from the model outputs.
        issues: list[str] = []

        # Regex to capture only vulnerability lines that follow our desired
        # template.  It requires that, after the line prefix and line
        # numbers, there is a colon followed by an alphabetic word and
        # then an em/en dash indicating the start of the explanation.  This
        # prevents lines like "Line 1: #include <stdio.h>" from being
        # erroneously collected.
        LINE_RE = re.compile(
            r"^\s*Line[s]?\s+\d+(?:\s*(?:-|–|—|,|/|&)\s*\d+)*\s*:\s*"
            r"[A-Za-z][^–—-]*[–—-]",
            re.IGNORECASE,
        )

        for idx, (block, blk_start) in enumerate(blocks, start=1):
            if not nosplit:
                print(f"🧩 Processing block {idx}/{len(blocks)}…")

            # Define the system message for chat models.  It sets the
            # reviewer persona and high-level task.
            system_message = (
                "You are a secure C/C++ code reviewer. You are given a code block "
                "and you need to analyze it for vulnerabilities."
            )

            # Build the user message containing detailed instructions and the code.
            user_message = f"""
You are a security expert. ANALYZE the following C/C++ code for vulnerabilities.

CRITICAL: Do NOT repeat or echo the code. ONLY output vulnerability findings.

Make sure to identify **every** vulnerability or security flaw in the code. Do not omit any issue.
Each issue you find must be reported using the required format below.

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

ANALYZE THIS CODE FOR SECURITY VULNERABILITIES:
------------------------------
{block}
------------------------------

PROVIDE ONLY THE VULNERABILITY ANALYSIS ABOVE, NOT THE CODE.
"""

            # Request a completion from the model using the chat API when available.
            raw = self.generate_text(
                user_message,
                max_tokens=max_tokens,
                system_prompt=system_message,
            )

            if self.debug:
                print("\n--- RAW MODEL OUTPUT ---")
                print(raw)
                print("--- END RAW ---\n")

            # Extract only vulnerability lines from the model output.
            for line in raw.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                # Skip header lines like '# analyzer filename'
                if re.match(r"^#\s*analyzer", stripped, re.IGNORECASE):
                    continue
                # Keep lines that match the vulnerability pattern.
                if LINE_RE.match(stripped):
                    issues.append(stripped)

        # Deduplicate and sort by the first line number mentioned.
        unique_lines = sorted(
            set(issues),
            key=lambda s: int(re.search(r"\d+", s).group()) if re.search(r"\d+", s) else 0,
        )

        header = f"# analyzer {os.path.basename(file_path)}"
        if not unique_lines:
            return f"{header}\nNo vulnerabilities found."
        return "\n".join([header] + unique_lines)