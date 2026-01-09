# Use Playwright base image for browser automation
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

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

# Run the actor
CMD ["python3", "-m", "src"]
