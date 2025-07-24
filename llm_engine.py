import re
from llama_cpp import Llama, llama_cpp
import os


class LLMEngine:
    def __init__(self, model_path: str = "models/phi-4.Q4_1.gguf"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        print(f"Loading model from {model_path}")
        self.model = Llama(model_path=model_path, n_ctx=4096, n_threads=8, verbose=True) #load the model with  max of 4096 tokens


    def generate_text(self, prompt: str, max_tokens: int = 1000):
        print("sending prompt to model")
        response = self.model(prompt, max_tokens=max_tokens, stop = ["</s>"]) #generate response
        return response["choices"][0]["text"].strip()


    def analyze_file(self, file_path: str, max_tokens: int = 1000):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()

        lines = file_content.splitlines()
        blocks = []
        current_block = []
        token_count = 0

        for line in lines:
            token_count += len(line.split())  
            current_block.append(line)
            if token_count >= max_tokens:
                blocks.append("\n".join(current_block))
                current_block = []
                token_count = 0
                

        for line in lines:
            token_count += len(line.split())  
            current_block.append(line)
            if token_count + len(line.split()) > max_tokens:
                blocks.append("\n".join(current_block))
                current_block = []
                token_count = 0

            current_block.append(line)
            token_count += len(line.split())

        responses = []
        for i, block in enumerate(blocks, start=1):
            prompt = f"""
                        You are a secure code reviewer. Analyze the following C/C++ code block for vulnerabilities.
                        For each vulnerability, provide:
                        1. Type of vulnerability (e.g., Buffer Overflow)
                        2. The line number (if possible)
                        3. A suggested fix

                        Code Block ({i}/{len(blocks)}):
                        ------------------------------
                        {block}
                        ------------------------------

                        Respond in a clear and structured format.
                        """
            response = self.analyze_code(prompt, max_tokens=max_tokens)
            responses.append(response)

        return responses