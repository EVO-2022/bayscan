# BayScan - Quick Start Guide

Get your BayScan fishing forecast running in 5 minutes!

🌐 **Production Site:** [bayscan.app](https://bayscan.app)

**For local installation:**

## Step 1: Setup

```bash
cd /home/evo/fishing-forecast
./setup.sh
```

## Step 2: Start the Server

```bash
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Step 3: Access Dashboard

### From the server:
Open browser to: `http://localhost:8080`

### From your phone (same WiFi network):

1. Find your server IP:
   ```bash
   hostname -I
   ```

2. On your phone's browser, go to:
   ```
   http://YOUR_SERVER_IP:8080
   ```
   Example: `http://192.168.1.100:8080`

## What You'll See

After startup:
1. Wait 1-2 minutes for initial data fetch
2. Dashboard will show:
   - Current tide height and direction
   - Weather conditions
   - Overall bite score
   - Per-species forecasts
   - 24-hour forecast windows
   - Alerts for hot fishing conditions

## Make It Start Automatically (Optional)

```bash
# Install as system service
sudo cp bayscan.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bayscan.service
sudo systemctl start bayscan.service

# Check status
sudo systemctl status bayscan.service
```

## Troubleshooting

**No data showing?**
- Wait 2-3 minutes for first data fetch
- Check logs: `sudo journalctl -u bayscan.service -f`

**Can't access from phone?**
- Make sure phone and server are on same WiFi
- Check firewall: `sudo ufw allow 8080`

**Port already in use?**
- Change port in config.yaml, or
- Stop other service using port 8080

## Next Steps

- Read the full README.md for advanced configuration
- Adjust alert thresholds in config.yaml
- Bookmark the dashboard on your phone

**Good fishing!** 🎣
