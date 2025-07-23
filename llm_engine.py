from llama_cpp import Llama, llama_cpp
import os


class LLMEngine:
    def __init__(self, model_path: str = "models/phi-4.Q4_1.gguf"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        print(f"Loading model from {model_path}")
        self.model = Llama(model_path=model_path, n_ctx=4096, n_threads=8, verbose=True)