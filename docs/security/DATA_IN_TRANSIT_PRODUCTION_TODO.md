# Data in Transit - Production Deployment TODO

**Document Version:** 1.0  
**Date:** December 1, 2024  
**Status:** Future Implementation

---

## Overview

This document outlines the steps required to enable HTTPS/TLS encryption for production deployment, including multi-tenant support for custom studio domains.

---

## Prerequisites

- [ ] Domain name purchased and configured
- [ ] Server with ports 80/443 open in firewall
- [ ] DNS A record pointing to server IP
- [ ] Backend deployed and accessible

---

## Option A: Cloudflare (Recommended for Multi-Tenant)

Best for: Multiple studio subdomains + custom domains

### Setup Steps

1. [ ] Create Cloudflare account (free tier available)
2. [ ] Add main domain to Cloudflare
3. [ ] Update nameservers at domain registrar
4. [ ] Enable "Full (Strict)" SSL mode in Cloudflare dashboard
5. [ ] Enable "Always Use HTTPS" option

### For Custom Studio Domains

Each studio with a custom domain needs to:
1. Add their domain to Cloudflare (or use CNAME setup)
2. Point DNS to your origin server
3. Cloudflare handles SSL automatically

### Pros
- Free SSL for unlimited domains
- Auto-renewal
- DDoS protection included
- No server configuration needed

### Cons
- Traffic routes through Cloudflare
- Requires DNS through Cloudflare (or CNAME setup)

---

## Option B: Caddy with On-Demand SSL

Best for: Self-hosted with automatic SSL for any domain

### Setup Steps

1. [ ] Install Caddy on server
   ```bash
   sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
   sudo apt update
   sudo apt install caddy
   ```

2. [ ] Create Caddyfile at `/etc/caddy/Caddyfile`:
   ```
   {
       on_demand_tls {
           ask http://localhost:8000/api/internal/verify-domain
       }
   }

   :443 {
       tls {
           on_demand
       }
       
       # Frontend
       reverse_proxy /api/* localhost:8000
       reverse_proxy /* localhost:3001
   }

   :80 {
       redir https://{host}{uri} permanent
   }
   ```

3. [ ] Create domain verification endpoint in backend:
   ```python
   @router.get("/api/internal/verify-domain")
   def verify_domain(domain: str, db: Session = Depends(get_db)):
       """Caddy calls this to verify domain belongs to a studio."""
       from app.db.models import StudioDomain
       studio_domain = db.query(StudioDomain).filter_by(
           domain=domain, 
           is_verified=True
       ).first()
       if studio_domain:
           return Response(status_code=200)
       return Response(status_code=404)
   ```

4. [ ] Start Caddy:
   ```bash
   sudo systemctl enable caddy
   sudo systemctl start caddy
   ```

### Pros
- Automatic Let's Encrypt for any domain
- Zero-config SSL
- Self-hosted (no third party)

### Cons
- Each custom domain needs DNS pointing to your server
- Need to install and maintain Caddy

---

## Option C: Nginx + Let's Encrypt

Best for: Traditional setup with subdomains only

### Setup Steps

1. [ ] Install Nginx and Certbot:
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx
   ```

2. [ ] Get wildcard certificate (for subdomains):
   ```bash
   sudo certbot certonly --manual --preferred-challenges dns \
     -d "*.photoproof.com" -d "photoproof.com"
   ```

3. [ ] Create Nginx config at `/etc/nginx/sites-available/photoproof`:
   ```nginx
   server {
       listen 80;
       server_name *.photoproof.com photoproof.com;
       return 301 https://$host$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name *.photoproof.com photoproof.com;

       ssl_certificate /etc/letsencrypt/live/photoproof.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/photoproof.com/privkey.pem;
       
       # Modern TLS configuration
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
       ssl_prefer_server_ciphers off;
       
       # HSTS
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

       location /api {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location / {
           proxy_pass http://127.0.0.1:3001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. [ ] Enable site and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/photoproof /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. [ ] Setup auto-renewal:
   ```bash
   sudo crontab -e
   # Add: 0 0 1 * * certbot renew --quiet
   ```

### For Custom Domains (Manual)
Each custom domain needs:
```bash
sudo certbot --nginx -d customdomain.com
```

### Pros
- Industry standard
- Full control
- Well documented

### Cons
- Manual cert management for custom domains
- More configuration required

---

## Environment Variables for Production

Update `.env` or set environment variables:

```env
# Required for production
APP_ENV=production

# Cookie security (MUST be true with HTTPS)
COOKIE_SECURE=true
COOKIE_SAMESITE=strict

# For subdomains (optional)
# Use leading dot to share cookies across subdomains
# Leave empty/unset for custom domains to work
COOKIE_DOMAIN=.photoproof.com
```

---

## Testing Checklist

### Browser DevTools
- [ ] Cookies have `Secure` flag (Application > Cookies)
- [ ] Cookies have `SameSite=Strict`
- [ ] No mixed content warnings in Console

### Response Headers
- [ ] `Strict-Transport-Security` header present
- [ ] `X-Frame-Options: DENY` present
- [ ] `X-Content-Type-Options: nosniff` present

### SSL Labs Test
- [ ] Visit https://www.ssllabs.com/ssltest/
- [ ] Enter your domain
- [ ] Achieve Grade A or higher

### Functional Tests
- [ ] HTTP requests redirect to HTTPS
- [ ] Login works and sets cookies correctly
- [ ] Token refresh works
- [ ] Logout clears cookies
- [ ] Cross-subdomain auth works (if using COOKIE_DOMAIN)

---

## Multi-Tenant Domain Considerations

| Domain Type | SSL Solution | Cookie Domain |
|-------------|--------------|---------------|
| Main app (photoproof.com) | Wildcard cert | `.photoproof.com` |
| Studio subdomains (studio1.photoproof.com) | Wildcard cert | `.photoproof.com` |
| Custom domains (photos.mystudio.com) | On-demand (Caddy) or Cloudflare | `None` (auto) |

### Important Notes

1. **Cookie Domain for Custom Domains**: When using custom domains, leave `COOKIE_DOMAIN` unset or empty. Setting a specific domain will break cookies on custom domains.

2. **Mixed Setup**: You can use different solutions together:
   - Cloudflare for main domain + subdomains
   - Caddy for custom studio domains

3. **DNS Requirements**: Custom domains must have:
   - A record pointing to your server IP, OR
   - CNAME pointing to your main domain (if using Cloudflare)

---

## Rollback Plan

If issues occur after enabling HTTPS:

1. Set `COOKIE_SECURE=false` in environment
2. Restart backend service
3. Clear browser cookies
4. Investigate logs for errors

---

## Security Compliance

After implementing HTTPS, you will meet:

| Requirement | Status |
|-------------|--------|
| Data encrypted in transit | ✅ |
| Secure cookie transmission | ✅ |
| HSTS enabled | ✅ |
| Modern TLS (1.2+) | ✅ |
| Protection against MITM | ✅ |

---

## Related Documentation

- [Security Overview](../../Photo_Proof_v1/docs/background_upload/security/01_SECURITY_OVERVIEW.md)
- [HTTPS/TLS Configuration](../../Photo_Proof_v1/docs/background_upload/security/04_HTTPS_TLS_CONFIGURATION.md)
- [Implementation Checklist](../../Photo_Proof_v1/docs/background_upload/security/05_IMPLEMENTATION_CHECKLIST.md)
