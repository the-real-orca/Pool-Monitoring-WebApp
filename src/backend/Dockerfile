FROM python:3.12-alpine

RUN adduser -D -g '' appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

# Pre-create the live-data directory so the volume bind-mount is writable
# by the non-root appuser inside the container.
RUN mkdir -p /data/history && chown appuser:appuser /data/history

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
