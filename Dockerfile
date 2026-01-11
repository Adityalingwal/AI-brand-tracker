# Use Playwright base image for browser automation
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

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

# Create entrypoint script that starts Xvfb
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1920x1080x24 &\nsleep 2\nexec python3 -u -m src' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Set display for headed mode
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Run with xvfb
CMD ["/app/entrypoint.sh"]
