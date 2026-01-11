FROM apify/actor-python-playwright:3.13

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

RUN python3 -m compileall -q src/

ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

CMD ["xvfb-run", "-a", "-s", "-ac -screen 0 1920x1080x24 -nolisten tcp", "python3", "-m", "src"]
