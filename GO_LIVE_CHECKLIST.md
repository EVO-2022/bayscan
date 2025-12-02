# BayScan Go-Live Checklist

## 🎯 Goal
Get BayScan live at **bayscan.app**

## ⚡ Quick Summary

**Your Server IP:** `99.107.152.134`
**Domain:** `bayscan.app` (from Porkbun)

---

## ✅ Step-by-Step Checklist

### □ Step 1: Deploy BayScan on Your Server (5 minutes)

Run the automated deployment script:

```bash
cd /home/evo/fishing-forecast
sudo ./deploy.sh
```

**What this does:**
- ✅ Installs Nginx
- ✅ Configures reverse proxy
- ✅ Sets up firewall
- ✅ Installs BayScan as a service
- ✅ Starts BayScan

**Verify it worked:**
```bash
# Check BayScan is running
sudo systemctl status bayscan.service

# Test locally
curl http://localhost:8080
```

---

### □ Step 2: Configure Porkbun DNS (2 minutes)

1. **Go to:** [Porkbun.com](https://porkbun.com)
2. **Click:** Your domain → **bayscan.app**
3. **Click:** **DNS** tab
4. **Add these two records:**

**Record 1:**
```
Type:    A
Host:    @
Answer:  99.107.152.134
TTL:     600
```

**Record 2:**
```
Type:    A
Host:    www
Answer:  99.107.152.134
TTL:     600
```

5. **Click:** Save/Update

**Need help?** See `PORKBUN_DNS_SETUP.md` for detailed screenshots and troubleshooting.

---

### □ Step 3: Wait for DNS Propagation (15-30 minutes)

DNS needs time to propagate globally.

**Check if it's ready:**
```bash
# From your terminal
nslookup bayscan.app

# Should return: 99.107.152.134
```

**Or check online:**
- https://dnschecker.org (enter: bayscan.app)
- https://www.whatsmydns.net (enter: bayscan.app)

**Look for:** Multiple green checkmarks showing `99.107.152.134`

☕ **Grab a coffee while you wait!**

---

### □ Step 4: Test HTTP Access (1 minute)

Once DNS propagates, test the site:

**In your browser:**
```
http://bayscan.app
```

You should see the BayScan dashboard! 🎉

**Troubleshooting:**
- If you see a timeout: DNS hasn't propagated yet, wait longer
- If you see Nginx default page: Check BayScan service is running
- If you see error: Check logs with `sudo journalctl -u bayscan.service -f`

---

### □ Step 5: Get SSL Certificate (2 minutes)

Once HTTP works, get a free SSL certificate:

```bash
sudo certbot --nginx -d bayscan.app -d www.bayscan.app
```

**Follow the prompts:**
1. Enter your email address
2. Agree to terms (Y)
3. Share email? (N is fine)
4. Certbot will automatically configure HTTPS

**Test HTTPS:**
```
https://bayscan.app
```

You should see the 🔒 padlock in your browser!

**SSL auto-renewal:**
Certbot automatically renews certificates. Test it:
```bash
sudo certbot renew --dry-run
```

---

### □ Step 6: Verify Everything Works (5 minutes)

**Final checks:**

1. **HTTPS redirect works:**
   ```
   http://bayscan.app → redirects to → https://bayscan.app
   ```

2. **WWW works:**
   ```
   https://www.bayscan.app → shows BayScan
   ```

3. **Dashboard loads:**
   - See current tide data
   - See weather conditions
   - See species forecasts
   - Wait 2-3 minutes for initial data fetch if needed

4. **Mobile access:**
   - Open https://bayscan.app on your phone
   - Should work perfectly!

5. **Service is running:**
   ```bash
   sudo systemctl status bayscan.service
   # Should show: active (running)
   ```

---

## 🎉 Success Criteria

You'll know it's working when:
- ✅ https://bayscan.app loads the dashboard
- ✅ Green padlock (SSL) in browser
- ✅ Tide and weather data showing
- ✅ Species forecasts visible
- ✅ Works on phone

---

## 📊 Monitoring Your Site

**Check service status:**
```bash
sudo systemctl status bayscan.service
```

**View live logs:**
```bash
sudo journalctl -u bayscan.service -f
```

**Restart if needed:**
```bash
sudo systemctl restart bayscan.service
```

**Nginx status:**
```bash
sudo systemctl status nginx
```

---

## 🔧 Common Issues & Fixes

### BayScan service won't start
```bash
# Check logs
sudo journalctl -u bayscan.service -n 50

# Common fix: permissions
cd /home/evo/fishing-forecast
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
# If this works, the service file might need adjustment
```

### Nginx shows error
```bash
# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Site is slow / no data
```bash
# Check if data is being fetched
sudo journalctl -u bayscan.service | grep "Fetching"

# Should see:
# "Fetching tide data..."
# "Fetching weather data..."

# Wait 2-3 minutes after first start for initial data
```

### SSL certificate issues
```bash
# Try again
sudo certbot --nginx -d bayscan.app -d www.bayscan.app

# Or renew existing
sudo certbot renew
```

---

## 🚀 Next Steps After Going Live

1. **Test from different devices:**
   - Desktop browser
   - Phone browser
   - Tablet

2. **Bookmark on your phone** for easy access

3. **Share with friends:**
   - "Check out bayscan.app for Mobile Bay fishing forecasts!"

4. **Monitor for a few days:**
   - Check logs daily
   - Verify data updates every 15 minutes
   - Watch for any errors

5. **Set up monitoring (optional):**
   - Use UptimeRobot.com (free)
   - Get alerts if site goes down

6. **Future enhancements:**
   - Add your logo
   - Customize species thresholds
   - Add more locations

---

## 📞 Support Resources

**Documentation:**
- `README.md` - Complete user guide
- `DEPLOYMENT.md` - Advanced deployment info
- `PORKBUN_DNS_SETUP.md` - DNS help

**Check BayScan health:**
```bash
curl https://bayscan.app/api/health
```

**API documentation:**
```
https://bayscan.app/docs
```

---

## ⏱️ Total Time Estimate

- Server deployment: **5 minutes**
- DNS configuration: **2 minutes**
- DNS propagation wait: **15-30 minutes**
- SSL setup: **2 minutes**
- Testing: **5 minutes**

**Total: ~30-45 minutes**

---

🎣 **You're about to have BayScan live at bayscan.app!**

**Start with Step 1 above and work your way down the checklist.**
