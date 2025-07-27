FROM python:3.12

# Install system packages and build dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y git curl ffmpeg aria2 build-essential g++ && \
    rm -rf /var/lib/apt/lists/*

# Update pip
RUN pip install -U pip

# Clone the repo and install requirements
RUN echo "Cloning Repo..." && \
    git clone https://github.com/Wacky007-git/TXT-EXTRACTOR /app && \
    cd /app && \
    # Set C++ standard to fix Pandas compilation
    export CXXFLAGS="-std=c++17" && \
    pip install -r requirements.txt

# Set working directory
WORKDIR /app

# Create a start script (infers from your original Dockerfile; customize as needed)
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'echo "Starting Bot..."' >> /start.sh && \
    echo 'python -m Extractor' >> /start.sh && \
    chmod +x /start.sh

# Expose any ports if needed (e.g., if the bot has a web interface)
# EXPOSE 8000

# Run the bot
CMD ["/start.sh"]
