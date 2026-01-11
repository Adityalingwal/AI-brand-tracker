# Use Apify's Python Playwright image (includes xvfb)
FROM apify/actor-python-playwright:3.13

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . ./

# Compile Python files for faster startup
RUN python3 -m compileall -q src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# The Apify image already has xvfb-run configured
# We need headless=false with Xvfb virtual display
# Running as root (default) so Xvfb can create /tmp/.X11-unix

# Run the actor with xvfb (virtual display for headed browser)
CMD ["xvfb-run", "-a", "-s", "-ac -screen 0 1920x1080x24 -nolisten tcp", "python3", "-m", "src"]
