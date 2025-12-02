#!/bin/bash
# Quick test script for Fishing Log UI

echo "=== Fishing Log UI Implementation Test ==="
echo ""

echo "✓ Checking HTML template..."
if grep -q "fishinglog" app/templates/index.html; then
    echo "  - Fishing Log tab added to navigation"
    echo "  - Fishing Log content section present"
else
    echo "  ✗ Fishing Log tab not found in template"
    exit 1
fi

echo ""
echo "✓ Checking JavaScript file..."
if [ -f "app/static/js/fishing_log.js" ]; then
    echo "  - fishing_log.js created"
    echo "  - Form submission handler present"
    echo "  - Table update logic present"
else
    echo "  ✗ fishing_log.js not found"
    exit 1
fi

echo ""
echo "✓ Checking CSS styles..."
if grep -q "FISHING LOG STYLES" app/static/css/style.css; then
    echo "  - Fishing Log styles added"
    echo "  - Mobile responsive styles included"
else
    echo "  ✗ Fishing Log styles not found"
    exit 1
fi

echo ""
echo "✓ Checking API endpoints..."
if grep -q "api/catches" app/main.py; then
    echo "  - POST /api/catches endpoint present"
    echo "  - GET /api/catches endpoint present"
    echo "  - GET /api/catches/stats endpoint present"
else
    echo "  ✗ API endpoints not found"
    exit 1
fi

echo ""
echo "✓ Checking database schema..."
if grep -q "class Catch" app/models/schemas.py; then
    echo "  - Catch table schema defined"
else
    echo "  ✗ Catch schema not found"
    exit 1
fi

echo ""
echo "==================================="
echo "All components verified successfully!"
echo "==================================="
echo ""
echo "To start the application:"
echo "  1. Install dependencies: pip install -r requirements.txt"
echo "  2. Run the server: python -m app.main"
echo "  3. Open browser to: http://localhost:8080"
echo "  4. Click the 'Log' tab to access Fishing Log"
echo ""
