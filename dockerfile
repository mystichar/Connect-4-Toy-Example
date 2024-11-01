# Dockerfile

# Use an official NVIDIA CUDA image with a specific CUDA version
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set environment variables for CUDA
ENV CUDA_VERSION=11.8
ENV CUDNN_VERSION=8

# Update and install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive-latex-base \
    latexmk \
    sudo \
    python3-pip \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python packages
RUN pip3 install --upgrade pip

# Install PyTorch with CUDA support
RUN pip3 install torch --extra-index-url https://download.pytorch.org/whl/cu118

# Install other Python dependencies
RUN pip3 install --no-cache-dir cirq \
    pytest \
    pytest-dependency \
    pydantic

# Define the working directory inside the container
WORKDIR /workspace/src

# Default command
CMD ["bash"]
