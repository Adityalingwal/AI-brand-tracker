FROM apify/actor-python:3.13

# Copy requirements first for better caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . ./

# Compile Python files
RUN python3 -m compileall -q src/

# Run the actor
CMD ["python3", "-m", "src"]
