FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY publisher.py ./

ENV LOG_LEVEL=INFO \
    INTERVAL_SECONDS=5 \
    PUMP_TOGGLE_EVERY=12

# tini gives us clean SIGTERM forwarding so the publisher loop exits promptly.
RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--", "python", "publisher.py"]
