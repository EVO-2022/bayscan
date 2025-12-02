#!/bin/bash
# BayScan Deployment Script for bayscan.app

set -e

echo "=================================="
echo "BayScan Deployment to bayscan.app"
echo "=================================="
echo ""

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script needs sudo access. Please run with sudo or as root."
    echo "Usage: sudo ./deploy.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
HOME_DIR="/home/$ACTUAL_USER/fishing-forecast"

echo "Deploying for user: $ACTUAL_USER"
echo "Project directory: $HOME_DIR"
echo ""

# Step 1: Install Nginx
echo "Step 1: Installing Nginx..."
apt update
apt install -y nginx
systemctl enable nginx
echo "✓ Nginx installed"
echo ""

# Step 2: Configure Nginx
echo "Step 2: Configuring Nginx for BayScan..."
cp "$HOME_DIR/nginx-bayscan.conf" /etc/nginx/sites-available/bayscan
ln -sf /etc/nginx/sites-available/bayscan /etc/nginx/sites-enabled/bayscan

# Remove default site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Test Nginx configuration
nginx -t
systemctl restart nginx
echo "✓ Nginx configured"
echo ""

# Step 3: Configure Firewall
echo "Step 3: Configuring Firewall..."
ufw --force enable
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
echo "✓ Firewall configured"
echo ""

# Step 4: Install BayScan Service
echo "Step 4: Installing BayScan systemd service..."
cp "$HOME_DIR/bayscan.service" /etc/systemd/system/bayscan.service
systemctl daemon-reload
systemctl enable bayscan.service
systemctl start bayscan.service
echo "✓ BayScan service installed and started"
echo ""

# Step 5: Check service status
echo "Step 5: Checking BayScan status..."
sleep 3
systemctl status bayscan.service --no-pager -l
echo ""

# Step 6: Install Certbot for SSL
echo "Step 6: Installing Certbot for SSL certificates..."
apt install -y certbot python3-certbot-nginx
echo "✓ Certbot installed"
echo ""

echo "=================================="
echo "Initial Deployment Complete!"
echo "=================================="
echo ""
echo "Your server IP: $(curl -4 -s ifconfig.me)"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Configure Porkbun DNS:"
echo "   - Go to Porkbun.com → Your Domains → bayscan.app → DNS"
echo "   - Add these records:"
echo "     Type: A    | Host: @   | Answer: $(curl -4 -s ifconfig.me)"
echo "     Type: A    | Host: www | Answer: $(curl -4 -s ifconfig.me)"
echo ""
echo "2. Wait 5-15 minutes for DNS to propagate"
echo ""
echo "3. Test your site:"
echo "   http://bayscan.app"
echo ""
echo "4. Once DNS works, get SSL certificate:"
echo "   sudo certbot --nginx -d bayscan.app -d www.bayscan.app"
echo ""
echo "5. Monitor your site:"
echo "   sudo systemctl status bayscan.service"
echo "   sudo journalctl -u bayscan.service -f"
echo ""
echo "BayScan is running on port 8080 behind Nginx!"
echo ""
