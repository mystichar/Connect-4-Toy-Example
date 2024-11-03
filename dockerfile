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

# Install PyTorch with CUDA 11.8 support
RUN pip3 install torch --extra-index-url https://download.pytorch.org/whl/cu118

# install cirq seperately since it takes a while
RUN pip3 install --no-cache-dir cirq 

# Install other Python dependencies including CuPy for CUDA 11.8
RUN pip3 install --no-cache-dir cirq \
    pytest \
    pytest-dependency \
    pydantic \
    numpy \
    scipy \
    cupy-cuda11x \
    numba

# Check if libnvrtc is installed and create a symbolic link if necessary
RUN if [ ! -f /usr/local/cuda/lib64/libnvrtc.so.11.8 ]; then \
        echo "libnvrtc not found, attempting to install additional CUDA libraries..."; \
        apt-get update && \
        apt-get install -y --no-install-recommends cuda-libraries-11-8 && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*; \
    fi

# Verify that libnvrtc is installed and available
RUN if [ ! -f /usr/local/cuda/lib64/libnvrtc.so.11.8 ]; then \
        echo "libnvrtc.so.11.8 still not found, creating symbolic link to libnvrtc.so"; \
        ln -s /usr/local/cuda/lib64/libnvrtc.so /usr/local/cuda/lib64/libnvrtc.so.11.8; \
    fi

# Define the working directory inside the container
WORKDIR /workspace/src

# Default command
CMD ["bash"]
