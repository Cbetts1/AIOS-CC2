# AI-OS CC2 — Container image
# Build:  docker build -t aios-cc2 .
# Run:    docker run -p 1313:1313 -v aios_data:/data aios-cc2

FROM python:3.11-slim

LABEL org.opencontainers.image.title="AI-OS CC2"
LABEL org.opencontainers.image.description="Stable, self-extending, web-backed AI OS"

WORKDIR /app

# Copy project files
COPY . .

# Create a non-root user and own the work directory
RUN useradd -m -u 1000 aios && chown -R aios:aios /app

USER aios

# Persistent data lives on a volume mounted at /data
ENV AIOS_DATA_DIR=/data

VOLUME ["/data"]

EXPOSE 1313

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:1313/api/heartbeat', timeout=5)" || exit 1

CMD ["python", "aios/main.py", "--ui", "none", "--port", "1313"]
