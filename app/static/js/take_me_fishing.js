/**
 * Take Me Fishing Mode - JavaScript
 * Simple fullscreen mode showing essential fishing info
 */

// Open Take Me Fishing mode
function openTakeMeFishing() {
    console.log('Opening Take Me Fishing mode...');

    // Show overlay
    const overlay = document.getElementById('takeMeFishingOverlay');
    overlay.style.display = 'block';

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    // Load data
    loadTakeMeFishingData();
}

// Close Take Me Fishing mode
function closeTakeMeFishing() {
    console.log('Closing Take Me Fishing mode...');

    // Hide overlay
    const overlay = document.getElementById('takeMeFishingOverlay');
    overlay.style.display = 'none';

    // Restore body scroll
    document.body.style.overflow = '';
}

// Load data for Take Me Fishing mode
function loadTakeMeFishingData() {
    fetch('/api/current')
        .then(response => response.json())
        .then(data => {
            console.log('Take Me Fishing data:', data);
            displayTakeMeFishingData(data);
        })
        .catch(error => {
            console.error('Error loading Take Me Fishing data:', error);
            showTakeMeFishingError();
        });
}

// Display data in Take Me Fishing mode
function displayTakeMeFishingData(data) {
    // 1. Tier (HOT/DECENT/SLOW/UNLIKELY)
    const tierEl = document.getElementById('tmfTier');
    const tierCard = tierEl.closest('.tmf-tier-card');

    // Get tier from top species or overall score
    let tier = 'DECENT';
    let tierClass = 'tmf-tier-decent';

    if (data.top_species && data.top_species.length > 0) {
        const topSpeciesTier = data.top_species[0].tier;
        if (topSpeciesTier === 'good') {
            tier = 'HOT';
            tierClass = 'tmf-tier-hot';
        } else if (topSpeciesTier === 'moderate') {
            tier = 'DECENT';
            tierClass = 'tmf-tier-decent';
        } else {
            tier = 'SLOW';
            tierClass = 'tmf-tier-slow';
        }
    } else if (data.overall_score) {
        if (data.overall_score >= 80) {
            tier = 'HOT';
            tierClass = 'tmf-tier-hot';
        } else if (data.overall_score >= 50) {
            tier = 'DECENT';
            tierClass = 'tmf-tier-decent';
        } else if (data.overall_score >= 20) {
            tier = 'SLOW';
            tierClass = 'tmf-tier-slow';
        } else {
            tier = 'UNLIKELY';
            tierClass = 'tmf-tier-unlikely';
        }
    }

    tierEl.textContent = tier;

    // Remove all tier classes and add the correct one
    tierCard.classList.remove('tmf-tier-hot', 'tmf-tier-decent', 'tmf-tier-slow', 'tmf-tier-unlikely');
    tierCard.classList.add(tierClass);

    // 2. Best Zone
    const zoneEl = document.getElementById('tmfZone');
    if (data.best_zones && data.best_zones.length > 0) {
        // Show first best zone
        zoneEl.textContent = `Zone ${data.best_zones[0]}`;
    } else if (data.depth_info && data.depth_info.depth) {
        // Fallback: suggest zone based on depth
        const depth = data.depth_info.depth;
        if (depth.includes('shallow')) {
            zoneEl.textContent = 'Zones 1-2';
        } else if (depth.includes('mid')) {
            zoneEl.textContent = 'Zones 3-4';
        } else if (depth.includes('deep')) {
            zoneEl.textContent = 'Zone 5';
        } else {
            zoneEl.textContent = 'Zones 3-4';
        }
    } else {
        zoneEl.textContent = 'Zones 3-4';
    }

    // 3. Best Depth
    const depthEl = document.getElementById('tmfDepth');
    if (data.depth_info && data.depth_info.depth_range) {
        depthEl.textContent = data.depth_info.depth_range;
    } else if (data.top_species && data.top_species.length > 0 && data.species) {
        // Find top species depth info
        const topSpecies = data.species.find(s => s.key === data.top_species[0].key);
        if (topSpecies && topSpecies.depth_range) {
            depthEl.textContent = topSpecies.depth_range;
        } else {
            depthEl.textContent = '3-5 ft';
        }
    } else {
        depthEl.textContent = '3-5 ft';
    }

    // 4. Best Bait
    const baitEl = document.getElementById('tmfBait');
    if (data.top_species && data.top_species.length > 0) {
        const topSpeciesName = data.top_species[0].name;
        // Suggest bait based on species
        const baitMap = {
            'Speckled Trout': 'Live Shrimp',
            'Redfish': 'Live Shrimp',
            'Black Drum': 'Cut Bait',
            'Flounder': 'Live Fish',
            'Sheepshead': 'Live Shrimp',
            'Mullet': 'Cast Net',
            'Blue Crab': 'Trap',
            'Croaker': 'Live Shrimp',
            'White Trout': 'Live Shrimp',
            'Stingray': 'Cut Bait',
            'Tripletail (Blackfish)': 'Live Shrimp',
            'Jack Crevalle': 'Lure',
            'Mackerel': 'Lure',
            'Shark': 'Cut Bait'
        };
        baitEl.textContent = baitMap[topSpeciesName] || 'Live Shrimp';
    } else {
        baitEl.textContent = 'Live Shrimp';
    }

    // 5. Rig of Moment
    const rigEl = document.getElementById('tmfRig');
    if (data.rig_of_moment) {
        rigEl.textContent = data.rig_of_moment;
    } else {
        // Fallback: basic rig recommendation
        rigEl.textContent = 'Use a 1/4oz jig head with live shrimp under a popping cork';
    }

    // 6. Two-Sentence Summary
    const summaryEl = document.getElementById('tmfSummary');
    if (data.conditions_summary) {
        summaryEl.textContent = data.conditions_summary;
    } else {
        summaryEl.textContent = 'Conditions are stable. Fish are active and feeding.';
    }
}

// Show error message
function showTakeMeFishingError() {
    document.getElementById('tmfTier').textContent = 'ERROR';
    document.getElementById('tmfZone').textContent = 'N/A';
    document.getElementById('tmfDepth').textContent = 'N/A';
    document.getElementById('tmfBait').textContent = 'N/A';
    document.getElementById('tmfRig').textContent = 'Unable to load data';
    document.getElementById('tmfSummary').textContent = 'Error loading conditions. Please try again.';
}

// Initialize Take Me Fishing mode
document.addEventListener('DOMContentLoaded', function() {
    console.log('Take Me Fishing JS initialized');

    // Open button
    const openBtn = document.getElementById('takeMeFishingBtn');
    if (openBtn) {
        openBtn.addEventListener('click', openTakeMeFishing);
    }

    // Close button
    const closeBtn = document.getElementById('tmfExitBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeTakeMeFishing);
    }

    // Close on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const overlay = document.getElementById('takeMeFishingOverlay');
            if (overlay && overlay.style.display === 'block') {
                closeTakeMeFishing();
            }
        }
    });
});
