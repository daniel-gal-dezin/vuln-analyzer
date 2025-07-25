from setuptools import setup

# Package metadata.  Adjust as needed for your project.
setup(
    name="vuln-analyzer",
    version="0.1.0",
    py_modules=["cli", "llm_engine"],
    description="LLM-powered C/C++ vulnerability scanner",
    python_requires=">=3.10",
    install_requires=[
        "llama-cpp-python==0.3.14",
    ],
    entry_points={
        "console_scripts": [
            "vuln-analyzer=cli:main",
        ],
    },
)