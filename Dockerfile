# syntax=docker/dockerfile:1

#
# Dockerfile for the vuln-analyzer project
# This image installs the Python package and exposes the `vuln-analyzer` CLI.
#

FROM python:3.11-slim

# Install system dependencies needed to build llama-cpp-python
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       cmake \
       git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the files needed for installation first (better caching)
COPY setup.py .
COPY cli.py .
COPY llm_engine.py .


# Install Python dependencies and the project itself
RUN pip install --no-cache-dir .

# Create models directory for user to mount models
RUN mkdir -p /app/models

# Copy any additional files (like test C files)
COPY *.c *.cpp ./

# Default entrypoint: run the vuln-analyzer CLI
# Users need to mount their model file, for example:
#   docker run --rm -v /path/to/model:/app/models vuln-analyzer analyze file.c
ENTRYPOINT ["vuln-analyzer"]
CMD ["--help"]