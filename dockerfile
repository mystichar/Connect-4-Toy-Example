# Use an official NVIDIA CUDA image with a specific CUDA version
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Set environment variables for CUDA
ENV CUDA_VERSION=11.8
ENV CUDNN_VERSION=8
ENV PATH="/usr/local/cuda/bin:${PATH}"

# Update and install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive-latex-base \
    latexmk \
    sudo \
    python3-pip \
    g++ \
    build-essential \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python packages
RUN pip3 install --upgrade pip

# Install PyTorch with CUDA support
RUN pip3 install torch --extra-index-url https://download.pytorch.org/whl/cu118

# Install other Python dependencies
RUN pip3 install --no-cache-dir cirq 
RUN pip3 install --no-cache-dir pytest \
    pytest-dependency \
    pydantic \
    numpy \
    scipy

#RUN apt get install nvcc

# Install pycuda
RUN apt-get update
RUN apt-get install python3.10-dev -y
RUN pip3 install --no-cache-dir pycuda 

RUN pip3 install --no-cache-dir qadence clifford matplotlib numpy

# Define the working directory inside the container
WORKDIR /workspace/src

# Default command
CMD ["bash"]
