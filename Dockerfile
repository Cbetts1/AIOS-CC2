# AI-OS CC2 — Docker image
# Runs the web server on port 1313 (no terminal UI — curses requires a PTY)
#
# Build:  docker build -t aios-cc2 .
# Run:    docker run -p 1313:1313 aios-cc2
#         Open http://localhost:1313 in your browser.
#         Admin password: 7212
#
# Debug:  docker run -p 1313:1313 aios-cc2 python aios/main.py --ui none --debug

FROM python:3.11-slim

# No extra packages — AI-OS uses stdlib only
WORKDIR /aios

COPY . .

# Create logs directory
RUN mkdir -p logs

EXPOSE 1313

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:1313/api/health', timeout=4)"

CMD ["python", "aios/main.py", "--ui", "none", "--port", "1313"]
