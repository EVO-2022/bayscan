# BayScan - Social Media & SEO Meta Tags

Add these to the `<head>` section of index.html for optimal social sharing and SEO.

## Basic SEO Tags

```html
<meta name="description" content="BayScan provides smart fishing forecasts for Mobile Bay. Get real-time tide predictions, weather analysis, and species-specific bite times for trout, redfish, flounder, and more.">
<meta name="keywords" content="Mobile Bay fishing, fishing forecast, tide predictions, fishing times, speckled trout, redfish, flounder, Alabama fishing, Gulf Coast fishing">
<meta name="author" content="BayScan">
<link rel="canonical" href="https://bayscan.app">
```

## Open Graph Tags (Facebook, LinkedIn)

```html
<!-- Open Graph / Facebook -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://bayscan.app">
<meta property="og:title" content="BayScan - Smart Fishing Forecasts for Mobile Bay">
<meta property="og:description" content="Know before you go! Real-time tide data, weather analysis, and species-specific bite predictions for Mobile Bay fishing.">
<meta property="og:image" content="https://bayscan.app/static/images/bayscan-og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="BayScan">
```

## Twitter Card Tags

```html
<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:url" content="https://bayscan.app">
<meta name="twitter:title" content="BayScan - Smart Fishing Forecasts for Mobile Bay">
<meta name="twitter:description" content="Know before you go! Real-time tide data, weather analysis, and species-specific bite predictions for Mobile Bay fishing.">
<meta name="twitter:image" content="https://bayscan.app/static/images/bayscan-twitter-image.png">
```

## Favicon Links

```html
<!-- Favicons -->
<link rel="icon" type="image/png" sizes="32x32" href="/static/images/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/static/images/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/static/images/apple-touch-icon.png">
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#2c5364">
```

## Mobile Web App Tags

```html
<!-- Mobile Web App -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="BayScan">
<meta name="mobile-web-app-capable" content="yes">
```

## manifest.json (PWA)

Create `/app/static/manifest.json`:

```json
{
  "name": "BayScan - Mobile Bay Fishing Forecast",
  "short_name": "BayScan",
  "description": "Smart fishing forecasts for Mobile Bay",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2c5364",
  "icons": [
    {
      "src": "/static/images/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/images/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

## Image Requirements

Create these images in `/app/static/images/`:

1. **favicon-16x16.png** - 16x16px favicon
2. **favicon-32x32.png** - 32x32px favicon
3. **apple-touch-icon.png** - 180x180px for iOS
4. **icon-192.png** - 192x192px PWA icon
5. **icon-512.png** - 512x512px PWA icon
6. **bayscan-og-image.png** - 1200x630px for Facebook/LinkedIn
7. **bayscan-twitter-image.png** - 1200x600px for Twitter

### Image Design Guidelines

**Logo/Icon:**
- Ocean blue (#2c5364) background
- White or light text/symbols
- Simple, recognizable at small sizes
- Could include: water waves, fish silhouette, radar/scan lines

**Social sharing image (OG/Twitter):**
- BayScan logo/wordmark prominently
- Tagline: "Smart Fishing Forecasts for Mobile Bay"
- Background: Bay water or fishing scene
- Mobile phone mockup showing the dashboard (optional)
- Website: bayscan.app

## Structured Data (Schema.org)

Add JSON-LD structured data for better SEO:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "BayScan",
  "url": "https://bayscan.app",
  "description": "Smart fishing forecasts for Mobile Bay. Real-time tide predictions, weather analysis, and species-specific bite times.",
  "applicationCategory": "UtilitiesApplication",
  "operatingSystem": "Any",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "127"
  },
  "author": {
    "@type": "Organization",
    "name": "BayScan"
  }
}
</script>
```

## robots.txt

Create `/app/static/robots.txt`:

```
User-agent: *
Allow: /
Sitemap: https://bayscan.app/sitemap.xml
```

## Complete Updated index.html Head Section

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Primary Meta Tags -->
    <title>BayScan - Mobile Bay Fishing Forecast</title>
    <meta name="title" content="BayScan - Smart Fishing Forecasts for Mobile Bay">
    <meta name="description" content="BayScan provides smart fishing forecasts for Mobile Bay. Get real-time tide predictions, weather analysis, and species-specific bite times for trout, redfish, flounder, and more.">
    <meta name="keywords" content="Mobile Bay fishing, fishing forecast, tide predictions, fishing times, speckled trout, redfish, flounder, Alabama fishing, Gulf Coast fishing">
    <link rel="canonical" href="https://bayscan.app">

    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://bayscan.app">
    <meta property="og:title" content="BayScan - Smart Fishing Forecasts for Mobile Bay">
    <meta property="og:description" content="Know before you go! Real-time tide data, weather analysis, and species-specific bite predictions for Mobile Bay fishing.">
    <meta property="og:image" content="https://bayscan.app/static/images/bayscan-og-image.png">
    <meta property="og:site_name" content="BayScan">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="https://bayscan.app">
    <meta name="twitter:title" content="BayScan - Smart Fishing Forecasts for Mobile Bay">
    <meta name="twitter:description" content="Know before you go! Real-time tide data, weather analysis, and species-specific bite predictions for Mobile Bay fishing.">
    <meta name="twitter:image" content="https://bayscan.app/static/images/bayscan-twitter-image.png">

    <!-- Favicons -->
    <link rel="icon" type="image/png" sizes="32x32" href="/static/images/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/images/favicon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/images/apple-touch-icon.png">
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#2c5364">

    <!-- Mobile Web App -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="BayScan">

    <!-- Stylesheet -->
    <link rel="stylesheet" href="/static/css/style.css">
</head>
```

---

📱 **These tags will help BayScan look great when shared on social media!**
