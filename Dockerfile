# Use Playwright base image for browser automation
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Install xvfb for headed mode (ChatGPT blocks headless browsers)
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy source code
COPY . ./

# Compile Python files
RUN python3 -m compileall -q src/

# Run the actor with virtual display (xvfb-run for headed browser)
CMD ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1920x1080x24", "python3", "-m", "src"]
