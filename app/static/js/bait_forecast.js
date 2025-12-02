/**
 * Bait Forecast JavaScript
 * Handles bait tab functionality, bait card display, and bait detail modal
 */

// State management
let baitForecastData = null;
let baitDataLoaded = false;

/**
 * Initialize bait forecast tab system
 */
function initBaitForecastTabs() {
    const tabs = document.querySelectorAll('.forecast-tab');
    const fishContent = document.getElementById('fishTabContent');
    const baitContent = document.getElementById('baitTabContent');

    if (!tabs.length || !fishContent || !baitContent) {
        console.error('Tab elements not found');
        return;
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.forecastTab;

            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');

            // Toggle content visibility
            if (tabName === 'fish') {
                fishContent.classList.add('active');
                baitContent.classList.remove('active');
            } else if (tabName === 'bait') {
                fishContent.classList.remove('active');
                baitContent.classList.add('active');

                // Load bait data on first click
                if (!baitDataLoaded) {
                    loadBaitForecast();
                }
            }
        });
    });

    console.log('Bait forecast tabs initialized');
}

/**
 * Load bait forecast data from API
 */
async function loadBaitForecast() {
    const baitList = document.getElementById('baitList');

    if (!baitList) {
        console.error('Bait list element not found');
        return;
    }

    try {
        // Show loading state
        baitList.innerHTML = '<div class="loading-message">Loading bait forecast...</div>';

        const response = await fetch('/api/bait-forecast');
        if (!response.ok) {
            throw new Error('Failed to load bait forecast');
        }

        const data = await response.json();
        baitForecastData = data;
        baitDataLoaded = true;

        // Render bait cards
        renderBaitCards(data.bait_forecasts);

    } catch (error) {
        console.error('Error loading bait forecast:', error);
        baitList.innerHTML = '<div class="error-message">Error loading bait forecast. Please try again.</div>';
    }
}

/**
 * Render bait forecast cards (weather-style full-width)
 */
function renderBaitCards(baits) {
    const baitList = document.getElementById('baitList');

    if (!baitList || !baits || baits.length === 0) {
        baitList.innerHTML = '<div class="no-data-message">No bait data available</div>';
        return;
    }

    // Filter out UNLIKELY and render cards with tinted backgrounds (IDENTICAL to fish cards)
    baitList.innerHTML = baits
        .filter(bait => bait.tier_label !== 'UNLIKELY')  // Skip UNLIKELY
        .map(bait => {
            // Map tier to colors: HOT=green, DECENT=blue, SLOW=red
            let colorClass = 'slow';  // default red
            if (bait.tier_label === 'HOT') {
                colorClass = 'hot';  // green
            } else if (bait.tier_label === 'DECENT') {
                colorClass = 'decent';  // blue
            }

            // Get display name from bait_species key
            const displayName = getBaitDisplayName(bait.bait_species);

            return `
                <div class="bait-card ${colorClass}" data-bait-key="${bait.bait_species}" onclick="openBaitModal('${bait.bait_species}')">
                    <div class="bait-name">${displayName}</div>
                </div>
            `;
        }).join('');

    console.log(`Rendered ${baits.length} bait cards`);
}

/**
 * Get display name for a bait species
 */
function getBaitDisplayName(baitKey) {
    const names = {
        'live_shrimp': 'Live Shrimp',
        'menhaden': 'Menhaden (Pogies)',
        'pinfish': 'Pinfish',
        'mud_minnows': 'Mud Minnows',
        'fiddler_crabs': 'Fiddler Crabs'
    };
    return names[baitKey] || baitKey.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Get condition summary for a bait species
 */
function getBaitConditionSummary(baitKey) {
    const summaries = {
        'live_shrimp': 'Active on moving tide in Zones 2-4',
        'menhaden': 'Schools in open water Zones 4-5',
        'pinfish': 'Around dock pilings in Zones 3-4',
        'mud_minnows': 'In muddy grass areas Zones 3-5',
        'fiddler_crabs': 'On muddy shorelines (not at dock)'
    };
    return summaries[baitKey] || 'Check zones for availability';
}

/**
 * Get how-to-catch summary for a bait species
 */
function getBaitHowToCatch(baitKey) {
    const howTo = {
        'live_shrimp': 'Cast net over grass beds and dock lights at night',
        'menhaden': 'Cast net on bait balls - watch for birds',
        'pinfish': 'Sabiki rig around dock pilings',
        'mud_minnows': 'Minnow trap in muddy shallows',
        'fiddler_crabs': 'Hand catch on muddy banks at low tide'
    };
    return howTo[baitKey] || 'See modal for details';
}

/**
 * Open bait detail modal
 */
async function openBaitModal(baitKey) {
    const modal = document.getElementById('baitModal');
    const modalBaitName = document.getElementById('modalBaitName');
    const modalBaitTier = document.getElementById('modalBaitTier');

    if (!modal) {
        console.error('Bait modal not found');
        return;
    }

    try {
        // Show modal with loading state
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        modalBaitName.textContent = 'Loading...';

        // Fetch bait detail
        const response = await fetch(`/api/bait/${baitKey}`);
        if (!response.ok) {
            throw new Error('Failed to load bait detail');
        }

        const baitData = await response.json();

        // Populate modal
        populateBaitModal(baitData);

    } catch (error) {
        console.error('Error loading bait detail:', error);
        modalBaitName.textContent = 'Error loading bait';
    }
}

/**
 * Populate bait modal with data
 */
function populateBaitModal(baitData) {
    // Header
    document.getElementById('modalBaitName').textContent = baitData.display_name;
    const tierBadge = document.getElementById('modalBaitTier');
    tierBadge.textContent = baitData.current_tier;
    tierBadge.className = `tier-badge bait-tier-${baitData.current_tier}`;

    // Overview
    document.getElementById('modalBaitDescription').textContent = baitData.description;

    // Where to Find
    const zonesBadges = baitData.zones.map(zone =>
        `<span class="bait-zone-badge">Zone ${zone}</span>`
    ).join('');
    document.getElementById('modalBaitZones').innerHTML = zonesBadges;
    document.getElementById('modalBaitZoneNotes').textContent = baitData.zone_notes;

    // When Active
    document.getElementById('modalBaitTidePreference').textContent = baitData.tide_preference;
    document.getElementById('modalBaitTimePreference').textContent = baitData.time_preference;
    document.getElementById('modalBaitClarityNotes').textContent = baitData.clarity_notes;

    // How to Catch - Methods
    const methodTags = baitData.methods.map(method =>
        `<span class="method-tag">${method}</span>`
    ).join('');
    document.getElementById('modalBaitMethods').innerHTML = methodTags;

    // How to Catch - Steps
    const howToCatchList = baitData.how_to_catch.map(step => `<li>${step}</li>`).join('');
    document.getElementById('modalBaitHowToCatch').innerHTML = howToCatchList;

    // Best For - Target Species
    const bestForTags = baitData.best_for.map(species => {
        const displayName = getSpeciesDisplayName(species);
        return `<span class="target-species-tag" onclick="closeBaitModal(); showSpeciesInfo('${species}')">${displayName}</span>`;
    }).join('');
    document.getElementById('modalBaitBestFor').innerHTML = bestForTags;

    // Tips
    const tipsList = baitData.tips.map(tip => `<li>${tip}</li>`).join('');
    document.getElementById('modalBaitTips').innerHTML = tipsList;
}

/**
 * Close bait modal
 */
function closeBaitModal() {
    const modal = document.getElementById('baitModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

/**
 * Convert species key to display name
 */
function getSpeciesDisplayName(speciesKey) {
    const speciesNames = {
        'speckled_trout': 'Speckled Trout',
        'redfish': 'Redfish',
        'flounder': 'Flounder',
        'sheepshead': 'Sheepshead',
        'black_drum': 'Black Drum',
        'white_trout': 'White Trout',
        'croaker': 'Croaker',
        'tripletail': 'Tripletail',
        'blue_crab': 'Blue Crab',
        'mullet': 'Mullet',
        'jack_crevalle': 'Jack Crevalle',
        'mackerel': 'Mackerel',
        'shark': 'Shark',
        'stingray': 'Stingray'
    };
    return speciesNames[speciesKey] || speciesKey.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Set up bait modal close handlers
 */
function setupBaitModalHandlers() {
    // Close button
    const closeBtn = document.getElementById('closeBaitModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeBaitModal);
    }

    // Click outside modal
    const modal = document.getElementById('baitModal');
    if (modal) {
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeBaitModal();
            }
        });
    }

    // ESC key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modal = document.getElementById('baitModal');
            if (modal && modal.style.display === 'block') {
                closeBaitModal();
            }
        }
    });
}

/**
 * Initialize bait forecast system
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing bait forecast system...');
    initBaitForecastTabs();
    setupBaitModalHandlers();
    console.log('Bait forecast system initialized');
});
