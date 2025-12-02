#!/bin/bash
# Quick restart script for BayScan service

echo "Restarting BayScan service..."
sudo systemctl restart bayscan.service

echo "Waiting for service to start..."
sleep 3

echo ""
echo "Service status:"
sudo systemctl status bayscan.service --no-pager | head -20

echo ""
echo "Recent logs:"
sudo journalctl -u bayscan.service -n 20 --no-pager

echo ""
echo "Done! BayScan should be running with latest code."
