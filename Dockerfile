FROM apify/actor-python-playwright:3.13

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

RUN python3 -m compileall -q src/

ENV PYTHONUNBUFFERED=1

# Note: Apify's base image already handles xvfb-run
# Just run the Python module directly
CMD ["python3", "-m", "src"]
