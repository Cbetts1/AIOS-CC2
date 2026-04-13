# AI-OS CC2 — Deployment Guide

## Contents
1. [Requirements](#requirements)
2. [Bare-metal (Python)](#bare-metal-python)
3. [Docker](#docker)
4. [Remote access (ngrok / reverse proxy)](#remote-access)
5. [Systemd (long-running demo host)](#systemd)
6. [Heroku / Render (PaaS)](#heroku--render)
7. [Security notes](#security-notes)

---

## Requirements

- **Python 3.8+** (no extra packages — stdlib only)
- **Windows only**: `pip install windows-curses` if you want the terminal UI
- Port **1313** free (or choose another with `--port`)

---

## Bare-metal (Python)

### Quick start
```bash
git clone https://github.com/Cbetts1/AIOS-CC2
cd AIOS-CC2

# Preflight check
bash start.sh check

# Launch (web UI mode — recommended for demos)
bash start.sh web 1313

# Or background mode (just the API server)
python aios/main.py --ui none --port 1313

# Windows
start.bat web 1313
```

Open `http://localhost:1313` in your browser.

### Debug mode
```bash
python aios/main.py --ui none --debug
# Verbose exception output + logs/debug.log written
```

### All CLI options
```
python aios/main.py [--ui terminal|web|none] [--port PORT]
                    [--operator-token TOKEN] [--debug]
```

---

## Docker

### Build and run
```bash
docker build -t aios-cc2 .
docker run -p 1313:1313 -v $(pwd)/logs:/aios/logs aios-cc2
```

Open `http://localhost:1313`.

### One-command demo (docker compose)
```bash
docker compose up          # foreground
docker compose up -d       # detached
docker compose down        # stop
```

Log files are persisted on the host in the `./logs/` directory via the volume mount.

### Health check
Docker will poll `/api/health` every 15 seconds.  `docker ps` shows `(healthy)` once ready.

### Terminal UI inside Docker
The curses UI requires a PTY:
```bash
docker run -it -p 1313:1313 aios-cc2 python aios/main.py --ui terminal
```

---

## Remote Access

The web server binds `0.0.0.0:1313`, so it's reachable from any IP that can
reach the host — but you still need to forward that port.

### ngrok (easiest, no configuration)
```bash
# In one terminal: start AI-OS
python aios/main.py --ui none

# In another terminal: expose to internet
ngrok http 1313
# → https://xxxx.ngrok.io
```

Share the ngrok HTTPS URL.  The admin password (`7212`) protects `/api/command`
and `/api/debug`.

### Reverse proxy (nginx)
```nginx
server {
    listen 80;
    server_name aios.example.com;

    location / {
        proxy_pass http://127.0.0.1:1313;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Add TLS via Let's Encrypt (`certbot --nginx`).

### Firewall
If running on a cloud VM (EC2, GCP, Azure, etc.), open port 1313 in the
security-group / firewall rules.

---

## Systemd

For a long-running demo on a dedicated Linux host:

```bash
# 1. Copy files
sudo cp -r . /opt/aios-cc2
sudo cp aios.service /etc/systemd/system/

# 2. Edit the WorkingDirectory and ExecStart paths in aios.service if needed

# 3. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now aios-cc2

# 4. Check status
sudo systemctl status aios-cc2
sudo journalctl -u aios-cc2 -f
```

---

## Heroku / Render

The `Procfile` at the repo root makes deployment straightforward:

```
web: python aios/main.py --ui none --port $PORT
```

```bash
# Heroku
heroku create
git push heroku main
heroku open

# Render — connect the GitHub repo, set runtime to Python, Render reads Procfile automatically
```

> **Note:** Free-tier dynos sleep after 30 minutes of inactivity.  Use a paid
> tier or a self-hosted container for a continuous demo.

---

## Security Notes

1. **Admin password** — `/api/command` and `/api/debug` require password `7212`.
   Change `_ADMIN_PASSWORD` in `aios/web/server.py` before any public deployment.

2. **Operator token** — the `IdentityLock` token is derived from the
   `operator + created` fields in `aios/identity/identity.lock`.  Since the
   file is committed to the repo, anyone can compute the token.  For a private
   deployment, update the `created` timestamp and keep the new value secret:
   ```python
   import hashlib
   raw = "Chris-<YOUR-NEW-TIMESTAMP>".encode()
   print(hashlib.sha256(raw).hexdigest())
   ```
   Update `identity.lock` with the new timestamp before deploying.

3. **CORS** — all endpoints reply `Access-Control-Allow-Origin: *`.  Restrict
   this in `server.py` if the API must not be reachable from arbitrary origins.

4. **No TLS** — the built-in HTTP server does not support HTTPS.  Always put a
   TLS-terminating reverse proxy (nginx, Caddy, ngrok) in front before exposing
   to the internet.
