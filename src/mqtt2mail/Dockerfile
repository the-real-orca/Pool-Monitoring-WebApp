FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN adduser -D -g '' appuser

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt
COPY app/mqtt2mail.py /app/mqtt2mail.py

USER appuser

CMD ["python", "/app/mqtt2mail.py"]
