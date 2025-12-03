# Deployment Guide

## 1. Local Development Setup

### 1.1 Install Dependencies

```bash
conda activate your_env
pip install -r requirements.txt
```

### 1.2 Run Application

```bash
uvicorn src.webapp.main:app --reload
```

---

## 2. Environment Variables

The following variables must be set:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT signing key |
| `APP_USERNAME` | Login username |
| `APP_PASSWORD` | Login password |

---

## 3. Cloudflare Tunnel Deployment

### 3.1 Install Cloudflare Tunnel

Follow instructions at: <https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/>

Then authenticate:

```bash
cloudflared tunnel login
cloudflared tunnel create jea-app
```

### 3.2 Configure Tunnel

Create `config.yml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /path/to/.cloudflared/<TUNNEL_ID>.json
Map your FastAPI server:
```

ingress:

- hostname: app.yourdomain.com
  service: <http://localhost:8000>
- service: http_status:404

```bash
cloudflared tunnel route dns jea-app app.yourdomain.com
```

### 3.3 Start Tunnel

```bash
cloudflared tunnel run jea-app
```

All traffic is now:

- HTTPS
- Identity-protected (if using Cloudflare Access)
- Private

---

## 4. Optional Cloud Deployment

### Supported Platforms

- Render.com
- Railway.app
- Fly.io

FastAPI runs easily on all three.

---

## 5. Production Notes

- Always enable HTTPS
- Set cookies to Secure=True
- Use long, random JWT secret keys
- Regularly rotate credentials
- Monitor access logs for anomalies
- Consider IP allowlisting for added security
