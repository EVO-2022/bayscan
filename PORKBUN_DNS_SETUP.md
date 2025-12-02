# Porkbun DNS Setup for BayScan

## Your Server Information

**Public IP Address:** `99.107.152.134`
**Domain:** `bayscan.app`

## Step-by-Step DNS Configuration

### 1. Login to Porkbun

Go to [Porkbun.com](https://porkbun.com) and log in to your account.

### 2. Access DNS Settings

1. Click on your domain: **bayscan.app**
2. Click on the **DNS** tab or **DNS Records** section

### 3. Add DNS Records

You need to add **TWO** A records:

#### Record 1: Root domain (@)
```
Type:    A
Host:    @ (or leave blank, or "bayscan.app")
Answer:  99.107.152.134
TTL:     600 (or default)
```

#### Record 2: WWW subdomain
```
Type:    A
Host:    www
Answer:  99.107.152.134
TTL:     600 (or default)
```

### Visual Example

Your DNS records should look like this:

```
┌──────┬──────────────┬─────────────────┬─────┐
│ Type │ Host         │ Answer          │ TTL │
├──────┼──────────────┼─────────────────┼─────┤
│ A    │ @            │ 99.107.152.134  │ 600 │
│ A    │ www          │ 99.107.152.134  │ 600 │
└──────┴──────────────┴─────────────────┴─────┘
```

### 4. Delete Existing Records (if needed)

If Porkbun added default parking page records, you may need to:
- Delete any existing A records for `@` and `www`
- Delete any CNAME records for `www`

### 5. Save Changes

Click **Save** or **Update DNS Records**

## DNS Propagation

- **Initial propagation**: 5-15 minutes
- **Full propagation**: Up to 24 hours (usually much faster)

### Check DNS Propagation

After adding records, check if DNS is working:

**From your computer:**
```bash
# Check root domain
nslookup bayscan.app

# Check www subdomain
nslookup www.bayscan.app

# Or use dig
dig bayscan.app
dig www.bayscan.app
```

**Expected result:**
```
bayscan.app has address 99.107.152.134
www.bayscan.app has address 99.107.152.134
```

**Online tools:**
- https://dnschecker.org (enter: bayscan.app)
- https://www.whatsmydns.net (enter: bayscan.app)

## Common Porkbun Interface Variations

Porkbun's interface may show fields slightly differently:

### Option A: Simple Form
- **Type:** Select "A" from dropdown
- **Host:** Enter `@` (for root) or `www`
- **Answer:** Enter `99.107.152.134`
- **TTL:** Use default or 600

### Option B: Advanced Form
- **Record Type:** A
- **Hostname:** `@` or `www` or `bayscan.app`
- **IP Address:** `99.107.152.134`
- **Priority:** (leave blank for A records)

## Troubleshooting

### DNS not resolving after 30 minutes?

1. **Check if records were saved:**
   - Refresh the DNS page in Porkbun
   - Verify your A records are listed

2. **Clear your local DNS cache:**
   ```bash
   # Linux/Mac
   sudo systemd-resolve --flush-caches
   # or
   sudo killall -HUP mDNSResponder

   # Windows
   ipconfig /flushdns
   ```

3. **Use a different DNS checker:**
   - Try from your phone (using cellular data, not WiFi)
   - Use https://dnschecker.org

4. **Verify nameservers:**
   - Check that Porkbun's nameservers are active
   - In Porkbun domain settings, should see:
     - `curitiba.ns.porkbun.com`
     - `fortaleza.ns.porkbun.com`
     - `maceio.ns.porkbun.com`
     - `salvador.ns.porkbun.com`

### Domain shows "This site can't be reached"

This is **NORMAL** until DNS propagates. Wait 15-30 minutes and try again.

### Domain shows parking page or error

- Make sure you **deleted** any default Porkbun parking records
- Make sure your A records point to `99.107.152.134`
- Clear browser cache and try in incognito/private mode

## After DNS Works

Once `bayscan.app` resolves to your server:

1. **Test HTTP access:**
   ```bash
   curl http://bayscan.app
   ```

2. **Get SSL certificate:**
   ```bash
   sudo certbot --nginx -d bayscan.app -d www.bayscan.app
   ```

3. **Access your site:**
   - http://bayscan.app (HTTP - temporary)
   - https://bayscan.app (HTTPS - after SSL)

---

🌐 **Your domain will be live at bayscan.app!**
