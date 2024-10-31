# Dockerfile

# Start from an official Python image with a specific version, like Python 3.10
FROM python:3.10-slim

# Update and install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive-latex-base \
    latexmk \
    sudo \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Cirq using pip
RUN pip install --no-cache-dir cirq
RUN pip install --no-cache-dir pytest
RUN pip install --no-cache-dir pytest-dependency
RUN pip install --no-cache-dir pydantic
RUN pip install --upgrade pip

# Define the working directory inside the container
WORKDIR /workspace/src

# Default command
CMD ["bash"]
