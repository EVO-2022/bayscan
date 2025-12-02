# BayScan Deployment Guide

This guide covers deploying BayScan to production at bayscan.app.

## Deployment Options

### Option 1: VPS Hosting (Recommended)

Deploy to a VPS provider like DigitalOcean, Linode, or AWS Lightsail.

**Requirements:**
- Ubuntu 20.04 or newer
- 1GB RAM minimum (2GB recommended)
- 10GB storage
- Public IP address

**Steps:**

1. **Set up VPS and domain**:
   ```bash
   # SSH into your server
   ssh root@your-server-ip

   # Update system
   apt update && apt upgrade -y

   # Create user (if not using root)
   adduser bayscan
   usermod -aG sudo bayscan
   su - bayscan
   ```

2. **Clone/upload BayScan**:
   ```bash
   cd /home/bayscan
   # Upload your fishing-forecast directory or clone from git
   ```

3. **Run setup**:
   ```bash
   cd fishing-forecast
   ./setup.sh
   ```

4. **Install and configure Nginx**:
   ```bash
   sudo apt install nginx -y

   # Create Nginx config
   sudo nano /etc/nginx/sites-available/bayscan
   ```

   Add this configuration:
   ```nginx
   server {
       listen 80;
       server_name bayscan.app www.bayscan.app;

       location / {
           proxy_pass http://127.0.0.1:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /static {
           proxy_pass http://127.0.0.1:8080/static;
       }
   }
   ```

   Enable the site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/bayscan /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Configure domain DNS**:
   - Point your domain `bayscan.app` to your server's IP address
   - Add both `@` and `www` A records

6. **Install SSL certificate** (Let's Encrypt):
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d bayscan.app -d www.bayscan.app
   ```

7. **Install BayScan as service**:
   ```bash
   sudo cp bayscan.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable bayscan.service
   sudo systemctl start bayscan.service
   ```

8. **Configure firewall**:
   ```bash
   sudo ufw allow 22      # SSH
   sudo ufw allow 80      # HTTP
   sudo ufw allow 443     # HTTPS
   sudo ufw enable
   ```

9. **Verify deployment**:
   ```bash
   sudo systemctl status bayscan.service
   curl http://localhost:8080/api/health
   ```

   Visit: https://bayscan.app

### Option 2: Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bayscan:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./fishing_forecast.db:/app/fishing_forecast.db
      - ./config.yaml:/app/config.yaml
    restart: unless-stopped
    environment:
      - TZ=America/Chicago
```

Deploy:
```bash
docker-compose up -d
```

### Option 3: Platform as a Service

Deploy to platforms like:
- **Railway.app** - Easy deployment, free tier
- **Render.com** - Free tier, automatic HTTPS
- **Fly.io** - Edge deployment, free tier
- **Heroku** - Classic PaaS (paid)

Most require a `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Production Configuration

### Security Checklist

- [ ] Enable HTTPS (SSL certificate)
- [ ] Configure firewall (UFW/iptables)
- [ ] Disable debug mode in config.yaml
- [ ] Use strong passwords for server access
- [ ] Keep system and dependencies updated
- [ ] Configure fail2ban for SSH protection
- [ ] Regular database backups

### Performance Optimization

1. **Enable Gzip compression** in Nginx:
   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript;
   ```

2. **Set up caching** for static files:
   ```nginx
   location /static {
       proxy_pass http://127.0.0.1:8080/static;
       expires 7d;
       add_header Cache-Control "public, immutable";
   }
   ```

3. **Configure log rotation**:
   ```bash
   sudo nano /etc/logrotate.d/bayscan
   ```

   Add:
   ```
   /var/log/bayscan/*.log {
       daily
       rotate 7
       compress
       delaycompress
       notifempty
       create 0644 bayscan bayscan
   }
   ```

### Monitoring

1. **Check service status**:
   ```bash
   sudo systemctl status bayscan.service
   ```

2. **View logs**:
   ```bash
   sudo journalctl -u bayscan.service -f
   ```

3. **Monitor resources**:
   ```bash
   htop
   df -h
   ```

4. **Set up health check monitoring**:
   - Use UptimeRobot (free)
   - Monitor https://bayscan.app/api/health
   - Get alerts if site goes down

### Backup Strategy

1. **Database backup**:
   ```bash
   # Create backup script
   nano ~/backup-bayscan.sh
   ```

   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   cp /home/bayscan/fishing-forecast/fishing_forecast.db \
      /home/bayscan/backups/fishing_forecast_$DATE.db

   # Keep only last 7 days
   find /home/bayscan/backups -name "*.db" -mtime +7 -delete
   ```

   ```bash
   chmod +x ~/backup-bayscan.sh

   # Add to crontab (daily at 2 AM)
   crontab -e
   # Add: 0 2 * * * /home/bayscan/backup-bayscan.sh
   ```

2. **Config backup**:
   - Keep config.yaml in version control (private repo)
   - Or backup to secure location

## Maintenance

### Updating BayScan

```bash
cd /home/bayscan/fishing-forecast
git pull  # If using git

# Or upload new files

sudo systemctl restart bayscan.service
```

### Database Maintenance

```bash
# Reset database (careful!)
cd /home/bayscan/fishing-forecast
sudo systemctl stop bayscan.service
rm fishing_forecast.db
sudo systemctl start bayscan.service
```

### System Updates

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot  # If kernel updated
```

## Troubleshooting

### Service won't start
```bash
sudo journalctl -u bayscan.service -n 50 --no-pager
```

### Nginx errors
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Database locked
```bash
sudo systemctl restart bayscan.service
```

### High memory usage
```bash
# Check processes
ps aux | grep python

# Restart service
sudo systemctl restart bayscan.service
```

## Cost Estimates

### Monthly hosting costs:

- **VPS (DigitalOcean/Linode)**: $6-12/month
- **Domain (bayscan.app)**: $12/year (~$1/month)
- **SSL Certificate**: Free (Let's Encrypt)
- **Total**: ~$7-13/month

### Free tier options:

- **Railway.app**: Free tier available
- **Render.com**: Free tier (with limitations)
- **Oracle Cloud**: Always free tier (with limited resources)

## Scaling Considerations

For high traffic (100+ concurrent users):

1. **Add caching layer** (Redis)
2. **Use CDN** (Cloudflare - free tier)
3. **Database optimization** (move to PostgreSQL)
4. **Multiple workers** in uvicorn
5. **Load balancer** for multiple instances

Current setup handles:
- **10-50 concurrent users** easily
- **1000+ requests/minute**
- **99.9% uptime** with proper monitoring

---

🚀 **Ready to deploy BayScan!**
