# Deployment Guide

## Current Setup

**Live Site:** https://kevinl-ai.com  
**Repository:** https://github.com/kyl579678/kevinl-ai-website  
**Deployed:** 2026-03-22

## Architecture

```
User → Cloudflare Tunnel → localhost:8080 → Python HTTP Server
```

### Components

1. **Web Server:** Python `http.server` on port 8080
2. **Tunnel:** Cloudflare Tunnel (ID: `9beac328-b15b-49ef-973a-933ea3904ec8`)
3. **Domain:** kevinl-ai.com (DNS via Cloudflare)

## Running Services

### Start Web Server
```bash
cd /home/lin/.openclaw/workspace/kevinl-ai-website
python3 -m http.server 8080
```

### Start Tunnel
```bash
cloudflared tunnel run kevinl-ai
```

### Check Status
```bash
# Check if services are running
ps aux | grep python3
ps aux | grep cloudflared

# Check tunnel connections
tail -f /home/lin/.cloudflared/tunnel.log
```

## Configuration Files

- **Tunnel Config:** `/home/lin/.cloudflared/config.yml`
- **Credentials:** `/home/lin/.cloudflared/9beac328-b15b-49ef-973a-933ea3904ec8.json`
- **Certificate:** `/home/lin/.cloudflared/cert.pem`

## Updating the Site

```bash
cd /home/lin/.openclaw/workspace/kevinl-ai-website

# Make changes to files
# ...

# Commit and push
git add .
git commit -m "Update site"
git push origin main

# No restart needed - Python http.server serves files directly
```

## Troubleshooting

### Site not accessible
```bash
# Check if services are running
curl http://localhost:8080

# Restart tunnel
pkill cloudflared
cloudflared tunnel run kevinl-ai &
```

### DNS issues
- DNS propagation can take up to 5 minutes
- Check: https://dnschecker.org/#CNAME/kevinl-ai.com

---
**Created:** 2026-03-22  
**Owner:** kyl579678
