# Use Apify's Python Playwright image (optimized for Apify platform)
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

# Run the actor
CMD ["python3", "-m", "src"]
