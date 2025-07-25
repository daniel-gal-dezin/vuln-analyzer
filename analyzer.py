#!/usr/bin/env python3
import sys
from llm_engine import LLMEngine

def main():
    print("Starting analyzer...")
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <file1>")
        sys.exit(1)

    # Initialize the LLM engine with the local model path
    engine = LLMEngine()

    # Analyze each file provided as an argument
    for file_path in sys.argv[1:]:
        print(f"\n🔍 Analyzing file: {file_path}\n" + "-"*50)
        try:
            # Split the file into chunks and analyze each one
            report = engine.analyze_file(file_path, max_tokens=768)
            print("\n=== SCAN REPORT ===\n")
            print(report)
            print("\n" + "="*60 + "\n")
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
