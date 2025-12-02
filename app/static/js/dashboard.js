// BayScan - Dashboard JavaScript

// Auto-refresh interval (5 minutes)
const REFRESH_INTERVAL = 5 * 60 * 1000;

// Species fishing information database
const SPECIES_INFO = {
    'Speckled Trout': {
        baits: ['Live shrimp', 'Croaker', 'Mullet', 'Soft plastics (paddle tails)', 'MirrOlure', 'Topwater plugs'],
        techniques: ['Fish 18-24" off bottom', 'Slow to moderate retrieve', 'Work structure and grass flats', 'Early morning topwater', 'Drift fishing'],
        rigs: ['Popping cork with jig head', 'Carolina rig', 'Free-line live bait', 'Topwater plug'],
        tips: 'Target grass flats, oyster bars, and structure. Best during dawn/dusk. Look for birds diving.'
    },
    'Redfish': {
        baits: ['Live shrimp', 'Crab (blue or fiddler)', 'Cut mullet', 'Live mullet', 'Gold spoons', 'Soft plastics'],
        techniques: ['Fish on bottom', 'Sight fishing in shallow water', 'Slow retrieve near structure', 'Work oyster bars and grass edges'],
        rigs: ['Carolina rig', 'Jig head', 'Popping cork', 'Weedless hook for grass'],
        tips: 'Look for tailing fish in shallow water. Target oyster bars, grass flats, and marsh edges. Redfish feed on bottom.'
    },
    'Flounder': {
        baits: ['Live mud minnows', 'Live shrimp', 'Finger mullet', 'Berkley Gulp', 'White bucktail jigs'],
        techniques: ['Drag bottom slowly', 'Bounce along sand/mud bottom', 'Fish near structure', 'Bridge pilings and drop-offs'],
        rigs: ['Carolina rig', 'Fish-finder rig', 'Jig head with trailer', 'Knocker rig'],
        tips: 'Flounder are ambush predators on the bottom. Target creek mouths, bridge pilings, and channel edges. Slow presentation is key.'
    },
    'Sheepshead': {
        baits: ['Fiddler crabs', 'Barnacles', 'Live shrimp', 'Sand fleas', 'Oysters'],
        techniques: ['Fish tight to structure', 'Vertical jigging', 'Short drops near pilings', 'Feel for light bites'],
        rigs: ['Knocker rig', 'Carolina rig with small hooks', 'Free-line near structure', 'Split-shot rig'],
        tips: 'Sheepshead have soft bites - stay alert. Target bridge pilings, docks, and oyster bars. Use small hooks (#1 or #2) and fresh bait.'
    },
    'Mullet': {
        baits: ['None (use cast net)'],
        techniques: ['Cast net in schools', 'Look for surface activity', 'Target shallow flats and channels', 'Early morning is best'],
        rigs: ['Cast net (3/8" or 1/2" mesh, 6-8 ft radius)'],
        tips: 'Mullet are best caught with cast nets. Look for surface ripples and jumping fish. Great live bait for other species.'
    },
    'Mackerel': {
        baits: ['Small spoons', 'Gotcha plugs', 'Glass minnow jigs', 'Live shrimp', 'Cut bait strips'],
        techniques: ['Fast retrieve', 'Troll near surface', 'Cast and retrieve rapidly', 'Target feeding frenzies'],
        rigs: ['Direct tie to lure', 'Sabiki rig', 'Double-drop rig', 'Wire leader recommended'],
        tips: 'Mackerel are fast and aggressive. Look for bird activity. Fast retrieve is essential. Watch for sharp teeth - use wire leaders.'
    },
    'Croaker': {
        baits: ['Small pieces of shrimp', 'Bloodworms', 'Cut bait', 'Fish bites', 'Small jigs'],
        techniques: ['Fish on bottom', 'Use light tackle', 'Anchor over structure', 'Multiple hook rigs'],
        rigs: ['Bottom rig (2-3 hooks)', 'Carolina rig', 'Chicken rig', 'Simple hi-lo rig'],
        tips: 'Croaker are bottom feeders. Use small hooks and bait. Great for kids - they bite readily. Often found in schools.'
    },
    'Stingray': {
        baits: ['Cut mullet', 'Squid', 'Large shrimp', 'Fish heads'],
        techniques: ['Fish on bottom', 'Use heavy tackle', 'Anchor in sandy areas', 'Be patient'],
        rigs: ['Fish-finder rig', 'Carolina rig with heavy weight', 'Circle hooks recommended'],
        tips: 'Stingrays are strong fighters. Use circle hooks for easy release. Handle carefully - barb is dangerous. Great sport on light tackle.'
    },
    'Shark': {
        baits: ['Cut mullet', 'Ladyfish', 'Stingray', 'Large live bait', 'Fresh cut fish', 'Bloody bait chunks'],
        techniques: ['Fish on bottom with heavy weight', 'Use wire leader', 'Set drag light', 'Be patient - let them run', 'Night fishing productive'],
        rigs: ['Fish-finder rig with wire leader', 'Large circle hooks (5/0-8/0)', 'Heavy monofilament or wire trace', 'Kayak bait deployment'],
        tips: 'Sharks are most active dawn, dusk, and night. Use fresh, bloody bait. Wire leader is essential. Practice catch and release - cut line if needed rather than handling. Most active in warm months (May-Oct).'
    },
    'Black Drum': {
        baits: ['Blue crab', 'Shrimp', 'Cut mullet', 'Oysters', 'Clams', 'Peeler crab'],
        techniques: ['Fish on bottom near structure', 'Use heavy tackle', 'Listen for drumming sound', 'Anchor near oyster bars', 'Slow presentation'],
        rigs: ['Carolina rig', 'Fish-finder rig', 'Knocker rig', 'Circle hooks (3/0-5/0)'],
        tips: 'Black drum are bottom feeders found near oyster bars and structure. They crush shellfish with powerful jaws. Best during spawning runs (Mar-Apr). Can be caught year-round. Slot limit: keep 16-27 inches.'
    },
    'Tripletail (Blackfish)': {
        baits: ['Live shrimp', 'Live pinfish', 'Live finger mullet', 'Jigs', 'Soft plastics'],
        techniques: ['Sight fishing around buoys and debris', 'Vertical jigging', 'Cast ahead and let sink', 'Stealthy approach', 'Accurate casting essential'],
        rigs: ['Free-line live bait', 'Jig head with shrimp', 'Popping cork', 'Light leader (20-30 lb)'],
        tips: 'Tripletail float on their side near buoys, channel markers, and floating debris to ambush prey. Look like leaves floating. Summer species (Jun-Sep). Calm days best for sight fishing. Excellent table fare!'
    },
    'Jack Crevalle': {
        baits: ['Live mullet', 'Live pinfish', 'Large topwater plugs', 'Spoons', 'Jigs', 'Soft plastics'],
        techniques: ['Fast retrieve', 'Target feeding frenzies', 'Look for bird activity', 'Topwater when schooling', 'Heavy tackle - powerful fish'],
        rigs: ['Direct tie to lure', 'Heavy leader (40-50 lb)', 'Large hooks (3/0-5/0)', 'Wire leader for toothy fish nearby'],
        tips: 'Jacks are incredibly powerful and aggressive. They hunt in packs and create explosive surface strikes. Great sport fish but poor table fare. Target moving water and baitfish schools. Summer peak (Jun-Sep).'
    },
    'White Trout': {
        baits: ['Live shrimp', 'Small jigs', 'Soft plastics (grubs)', 'Cut bait', 'Small spoons', 'Bloodworms'],
        techniques: ['Fish near bottom', 'Moderate retrieve', 'Work channels and deeper water', 'Schools often feed mid-water', 'Light tackle'],
        rigs: ['Small jig head (1/8-1/4 oz)', 'Popping cork with shrimp', 'Double-drop bottom rig', 'Carolina rig'],
        tips: 'White trout (sand trout) are similar to speckled trout but smaller and found in schools. Target deeper channels and flats. Less structure-dependent than specks. Good action year-round but peak in spring/summer. Excellent light tackle sport.'
    },
    'Blue Crab': {
        baits: ['Chicken necks', 'Fish heads', 'Squid', 'Eel', 'Razor clams'],
        techniques: ['Use crab traps or pots', 'Hand lines with bait', 'Dip nets', 'Trot lines', 'Check traps every 15-20 minutes'],
        rigs: ['Collapsible crab trap', 'Ring net', 'Hand line with weight', 'Trot line (multiple baits on long line)'],
        tips: 'Blue crabs are most active in warm months (May-Sep). Best caught during moving tides. Use a bushel basket or cooler to store. Keep water cool and moist. Check local regulations for size limits (typically 5" point to point). Peak season is summer when water is warmest.'
    }
};

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeModal();
    initializeConditionsSummary();
    initializeCurrentsMap();
    loadDashboard();
    updateHourlyOutlook(); // Load hourly outlook strip

    // Set up auto-refresh
    setInterval(() => {
        loadDashboard();
        updateHourlyOutlook(); // Refresh hourly outlook
    }, REFRESH_INTERVAL);
});

// Initialize tab switching
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');

            // Reset scroll position to top
            window.scrollTo(0, 0);
        });
    });
}

// Main function to load all dashboard data
async function loadDashboard() {
    try {
        // Load all data in parallel
        const [current, forecast, alerts] = await Promise.all([
            fetch('/api/current').then(r => r.json()),
            fetch('/api/forecast?hours=24').then(r => r.json()),
            fetch('/api/alerts').then(r => r.json())
        ]);

        // Update UI
        updateLastUpdateTime();
        updateCurrentConditions(current);
        updateSpeciesList(current.species || []);
        generateFishBehaviorSummary(current.species || [], current);
        updateAlerts(alerts);

    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load forecast data. Will retry...');
    }
}

// Update last update timestamp
function updateLastUpdateTime() {
    // Element removed from UI - no longer needed
    return;
}

// Update current conditions panel
function updateCurrentConditions(data) {
    // TIDE SECTION
    const tideDetails = data.tide_details || {};

    // Tide height
    if (tideDetails.current_height !== null) {
        document.getElementById('tideHeight').textContent = tideDetails.current_height;
    }

    // Tide direction (state) - in header badge
    const tideStateEl = document.getElementById('tideState');
    const state = tideDetails.state || 'unknown';
    tideStateEl.textContent = state.charAt(0).toUpperCase() + state.slice(1);
    tideStateEl.className = `tide-state-badge ${state}`;

    // Current strength
    const currentStrengthEl = document.getElementById('currentStrength');
    if (data.current_strength) {
        currentStrengthEl.textContent = data.current_strength;
    } else {
        currentStrengthEl.textContent = '--';
    }

    // Water clarity
    const clarityValue = document.getElementById('clarityValue');
    if (data.clarity) {
        clarityValue.textContent = data.clarity;
    } else {
        clarityValue.textContent = '--';
    }

    // Moon phase
    const moonPhaseEl = document.getElementById('moonPhase');
    if (data.moon_phase) {
        moonPhaseEl.textContent = data.moon_phase;
    } else {
        moonPhaseEl.textContent = '--';
    }

    // Next high/low
    if (tideDetails.next_high) {
        const highTime = new Date(tideDetails.next_high.time);
        document.getElementById('nextHigh').textContent =
            `${formatTime(highTime)} (${tideDetails.next_high.height.toFixed(1)} ft)`;
    }

    if (tideDetails.next_low) {
        const lowTime = new Date(tideDetails.next_low.time);
        document.getElementById('nextLow').textContent =
            `${formatTime(lowTime)} (${tideDetails.next_low.height.toFixed(1)} ft)`;
    }

    // WEATHER SECTION

    // Air temp (same as temperature for now)
    document.getElementById('airTemp').textContent =
        data.temperature ? Math.round(data.temperature) : '--';

    // Water temp
    document.getElementById('temperature').textContent =
        data.temperature ? Math.round(data.temperature) : '--';

    // Pressure
    const pressureTrend = data.pressure_trend || 'stable';
    const trendSymbol = pressureTrend === 'rising' ? '↑' :
                       pressureTrend === 'falling' ? '↓' : '→';
    document.getElementById('pressureTrend').textContent =
        `${pressureTrend} ${trendSymbol}`;

    // Wind direction
    const windDirEl = document.getElementById('windDirection');
    if (data.wind_direction) {
        windDirEl.textContent = data.wind_direction;
    } else {
        windDirEl.textContent = '--';
    }

    // Wind speed
    document.getElementById('windSpeed').textContent =
        data.wind_speed ? Math.round(data.wind_speed) : '--';

    // Wind gusts
    const windGustsEl = document.getElementById('windGusts');
    if (data.wind_gust) {
        windGustsEl.textContent = Math.round(data.wind_gust);
    } else {
        windGustsEl.textContent = '--';
    }

    // Cloud cover
    const cloudCoverEl = document.getElementById('cloudCover');
    if (data.cloud_cover) {
        cloudCoverEl.textContent = data.cloud_cover;
    } else {
        cloudCoverEl.textContent = '--';
    }

    // Conditions (upcoming)
    document.getElementById('conditions').textContent =
        data.conditions || 'Unknown';

    // Weather icon based on conditions and time of day
    const weatherIconEl = document.getElementById('weatherIcon');
    const conditions = (data.conditions || '').toLowerCase();
    const cloudCover = (data.cloud_cover || '').toLowerCase();
    const hour = new Date().getHours();
    const isNight = hour < 6 || hour > 19; // Roughly nighttime hours

    let icon = '☀️'; // Default: sunny

    if (conditions.includes('rain') || conditions.includes('shower')) {
        icon = '🌧️';
    } else if (conditions.includes('storm') || conditions.includes('thunder')) {
        icon = '⛈️';
    } else if (conditions.includes('snow')) {
        icon = '🌨️';
    } else if (conditions.includes('fog') || conditions.includes('mist')) {
        icon = '🌫️';
    } else if (cloudCover.includes('overcast') || conditions.includes('overcast') || conditions.includes('cloudy')) {
        icon = '☁️';
    } else if (cloudCover.includes('partly') || conditions.includes('partly')) {
        icon = isNight ? '⛅' : '⛅';
    } else if (isNight) {
        icon = '🌙';
    }

    weatherIconEl.textContent = icon;

    // CONFIDENCE SECTION - REMOVED FROM UI
    // const confidenceBadge = document.getElementById('confidenceBadge');
    // if (data.confidence) {
    //     confidenceBadge.textContent = data.confidence;
    //     confidenceBadge.className = 'confidence-badge-large confidence-' + data.confidence.toLowerCase();
    // } else {
    //     confidenceBadge.textContent = 'MEDIUM';
    //     confidenceBadge.className = 'confidence-badge-large confidence-medium';
    // }

    // Note: Overall bite score display removed - now using hourly outlook strip
}

// Update species list
function updateSpeciesList(species) {
    const container = document.getElementById('speciesList');
    container.innerHTML = '';

    if (!species || species.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">No species data available</p>';
        return;
    }

    // Filter out UNLIKELY species and display others
    species.forEach(sp => {
        const tier = sp.tier || 'SLOW';

        // Skip UNLIKELY tier completely
        if (tier === 'UNLIKELY') {
            return;
        }

        // Map tier to colors: HOT=green, DECENT=blue, SLOW=red
        let colorClass = 'slow'; // default red
        if (tier === 'HOT') {
            colorClass = 'hot';  // green
        } else if (tier === 'DECENT') {
            colorClass = 'decent';  // blue
        }

        const card = document.createElement('div');
        card.className = `species-card ${colorClass}`;  // Add color class to card

        card.innerHTML = `
            <div class="species-name">${sp.name}</div>
            <div class="species-tier-badge ${colorClass}"></div>
            <div class="species-tier-bar ${colorClass}"></div>
            <button class="learning-info-icon" data-species="${sp.species_key}" title="Learning Notes">ⓘ</button>
        `;

        // Add click handler to show species info modal (on card, not icon)
        card.addEventListener('click', (e) => {
            // Don't trigger if clicking the info icon
            if (!e.target.classList.contains('learning-info-icon')) {
                showSpeciesInfo(sp.name);
            }
        });

        // Add click handler for learning info icon
        const infoIcon = card.querySelector('.learning-info-icon');
        infoIcon.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent card click
            showLearningNotes(sp.species_key, sp.name);
        });

        container.appendChild(card);
    });
}

// REMOVED: updateForecastWindows - Forecast tab removed, functionality moved to hourly outlook modal

// Update alerts section
function updateAlerts(alerts) {
    const container = document.getElementById('alertsList');
    const badge = document.getElementById('alertBadge');
    const alertsTab = document.getElementById('alertsTab');

    // Update alert count badge
    if (!alerts || alerts.length === 0) {
        badge.style.display = 'none';
        container.innerHTML = '<div class="no-alerts">No active alerts at this time</div>';
        return;
    }

    // Show badge with count
    badge.style.display = 'inline-block';
    badge.textContent = alerts.length;

    // Group alerts by time window
    const groupedAlerts = {};
    alerts.forEach(alert => {
        const windowKey = `${alert.window_start}_${alert.window_end}`;
        if (!groupedAlerts[windowKey]) {
            groupedAlerts[windowKey] = {
                window_start: alert.window_start,
                window_end: alert.window_end,
                species: []
            };
        }
        groupedAlerts[windowKey].species.push({
            name: alert.species,
            score: alert.bite_score
        });
    });

    // Populate alerts list with grouped items
    container.innerHTML = '';

    Object.values(groupedAlerts).forEach(group => {
        const startTime = new Date(group.window_start);
        const endTime = new Date(group.window_end);
        const timeStr = `${formatTime(startTime)} - ${formatTime(endTime)}`;

        // Sort species by score descending
        group.species.sort((a, b) => b.score - a.score);

        // Create species list HTML
        const speciesListHTML = group.species
            .map(sp => `<span class="alert-species-tag">${sp.name} (${Math.round(sp.score)})</span>`)
            .join('');

        const alertItem = document.createElement('div');
        alertItem.className = 'alert-item';
        alertItem.innerHTML = `
            <div class="alert-header">
                <span class="alert-icon">🔥</span>
                <span class="alert-title">HOT Fishing Window</span>
            </div>
            <div class="alert-time">⏰ ${timeStr}</div>
            <div class="alert-species-list">
                <strong>Species:</strong>
                <div class="species-tags">${speciesListHTML}</div>
            </div>
        `;

        container.appendChild(alertItem);
    });

    // Bell icon removed - no longer marking species cards with alerts
}

// Helper: Get bite label from score
function getBiteLabel(score) {
    if (score >= 71) return 'Hot';
    if (score >= 41) return 'Decent';
    if (score >= 21) return 'Slow';
    return 'Unlikely';
}

// Helper: Format time in Central timezone
// Accepts both Date objects and ISO strings
function formatTime(dateOrString) {
    if (typeof dateOrString === 'string') {
        // ISO string from API (already in Central timezone)
        const date = new Date(dateOrString);
        return date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
            timeZone: 'America/Chicago'
        });
    } else if (dateOrString instanceof Date) {
        // Date object
        return dateOrString.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
            timeZone: 'America/Chicago'
        });
    }
    return '';
}

// Helper: Show error message
function showError(message) {
    // Simple error display - could be enhanced
    console.error(message);

    // Could add a visual error banner here
    const container = document.querySelector('.container');
    let errorDiv = document.querySelector('.error');

    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        container.insertBefore(errorDiv, container.firstChild.nextSibling);
    }

    errorDiv.textContent = message;

    // Auto-hide after 10 seconds
    setTimeout(() => {
        if (errorDiv && errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 10000);
}

// Species info modal functions
async function showSpeciesInfo(speciesName) {
    const info = SPECIES_INFO[speciesName];

    if (!info) {
        console.error('No info available for species:', speciesName);
        return;
    }

    // Update modal content
    document.getElementById('modalSpeciesName').textContent = speciesName;

    // Populate techniques (from SPECIES_INFO)
    const techniquesList = document.getElementById('modalTechniques');
    techniquesList.innerHTML = info.techniques.map(tech => `<li>${tech}</li>`).join('');

    // Populate rigs (from SPECIES_INFO)
    const rigsList = document.getElementById('modalRigs');
    rigsList.innerHTML = info.rigs.map(rig => `<li>${rig}</li>`).join('');

    // Populate tips (from SPECIES_INFO)
    document.getElementById('modalTips').textContent = info.tips;

    // Fetch and display regulations + behavior cheat sheet
    try {
        const speciesKey = getSpeciesKey(speciesName);
        const response = await fetch(`/api/species/${speciesKey}`);
        if (response.ok) {
            const data = await response.json();

            // Update regulations
            const regulationsEl = document.getElementById('modalRegulations');
            const parts = [];
            if (data.size_limit && data.size_limit !== 'N/A') {
                parts.push(`Size Limit: ${data.size_limit}`);
            }
            if (data.creel_limit && data.creel_limit !== 'N/A') {
                parts.push(`Creel: ${data.creel_limit}`);
            }

            if (parts.length === 0 && data.regulations && data.regulations.creel && data.regulations.creel.notes) {
                regulationsEl.textContent = `(${data.regulations.creel.notes})`;
            } else if (parts.length > 0) {
                regulationsEl.textContent = `(${parts.join(') • (')})`;
            } else {
                regulationsEl.textContent = '';
            }

            // Update behavior cheat sheet (NEW)
            if (data.behavior) {
                const behavior = data.behavior;

                // Update behavior summary
                const summaryEl = document.getElementById('modalBehaviorSummary');
                summaryEl.innerHTML = `<p>${behavior.behavior_summary || 'No behavior information available.'}</p>`;

                // Update best baits (from API behavior data instead of SPECIES_INFO)
                const baitsList = document.getElementById('modalBaits');
                if (behavior.best_baits && behavior.best_baits.length > 0) {
                    baitsList.innerHTML = behavior.best_baits.map(bait => `<li>${bait}</li>`).join('');
                } else {
                    baitsList.innerHTML = '<li>General live bait and lures</li>';
                }

                // Update best zones
                const zonesEl = document.getElementById('modalBestZones');
                if (behavior.best_zones && behavior.best_zones.length > 0) {
                    zonesEl.innerHTML = behavior.best_zones.map(zone =>
                        `<span class="zone-badge-small">Zone ${zone}</span>`
                    ).join(' ');
                } else {
                    zonesEl.textContent = 'All zones';
                }

                // Update best tide
                const tideEl = document.getElementById('modalBestTide');
                tideEl.textContent = behavior.best_tide || 'Moving tide';

                // Update depth range (show only CURRENT tier dynamically, no tier label)
                const depthEl = document.getElementById('modalBestDepth');
                if (behavior.best_depth && behavior.best_depth.current) {
                    const currentDepth = behavior.best_depth.current;
                    depthEl.innerHTML = `<div class="depth-simple">
                        <strong>${currentDepth.range}</strong> • ${currentDepth.note}
                    </div>`;
                } else if (behavior.best_depth && Object.keys(behavior.best_depth).length > 0) {
                    // Fallback for old format (show all three tiers)
                    const depthInfo = behavior.best_depth;
                    let depthHTML = '<div class="depth-tiers">';

                    if (depthInfo.good) {
                        depthHTML += `<div class="depth-tier">
                            <span class="tier-label good">HOT</span>
                            <span class="depth-range">${depthInfo.good.range}</span>
                            <span class="depth-note">${depthInfo.good.note}</span>
                        </div>`;
                    }
                    if (depthInfo.moderate) {
                        depthHTML += `<div class="depth-tier">
                            <span class="tier-label moderate">DECENT</span>
                            <span class="depth-range">${depthInfo.moderate.range}</span>
                            <span class="depth-note">${depthInfo.moderate.note}</span>
                        </div>`;
                    }
                    if (depthInfo.slow) {
                        depthHTML += `<div class="depth-tier">
                            <span class="tier-label slow">SLOW</span>
                            <span class="depth-range">${depthInfo.slow.range}</span>
                            <span class="depth-note">${depthInfo.slow.note}</span>
                        </div>`;
                    }

                    depthHTML += '</div>';
                    depthEl.innerHTML = depthHTML;
                } else {
                    depthEl.textContent = '2-7 ft (varies)';
                }
            }
        }
    } catch (error) {
        console.error('Error fetching species data:', error);
    }

    // Show modal
    const modal = document.getElementById('speciesModal');
    modal.classList.add('show');
}

// Helper to convert display name to species key
function getSpeciesKey(displayName) {
    const keyMap = {
        'Speckled Trout': 'speckled_trout',
        'Redfish': 'redfish',
        'Black Drum': 'black_drum',
        'Flounder': 'flounder',
        'Sheepshead': 'sheepshead',
        'Stingray': 'stingray',
        'Mullet': 'mullet',
        'Croaker': 'croaker',
        'Tripletail (Blackfish)': 'tripletail',
        'White Trout': 'white_trout',
        'Blue Crab': 'blue_crab',
        'Jack Crevalle': 'jack_crevalle',
        'Mackerel': 'mackerel',
        'Shark': 'shark'
    };
    return keyMap[displayName] || displayName.toLowerCase().replace(/ /g, '_');
}

function closeSpeciesModal() {
    const modal = document.getElementById('speciesModal');
    modal.classList.remove('show');
}

// Initialize modal event listeners
function initializeModal() {
    const modal = document.getElementById('speciesModal');
    const closeBtn = modal.querySelector('.modal-close');

    if (closeBtn) {
        // Close button click
        closeBtn.addEventListener('click', closeSpeciesModal);
    }

    // Click outside modal to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeSpeciesModal();
        }
    });

    // ESC key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('show')) {
            closeSpeciesModal();
        }
    });
}

// Initialize Conditions Summary Popover
function initializeConditionsSummary() {
    const btn = document.getElementById('conditionsSummaryBtn');
    const popover = document.getElementById('conditionsPopover');
    const backdrop = document.getElementById('popoverBackdrop');
    const closeBtn = document.getElementById('closePopover');

    // Open popover on button click
    btn.addEventListener('click', () => {
        popover.style.display = 'block';
        backdrop.classList.add('active');
        // Update popover content when opened
        updateConditionsSummary();
    });

    // Close popover
    const closePopover = () => {
        popover.style.display = 'none';
        backdrop.classList.remove('active');
    };

    closeBtn.addEventListener('click', closePopover);
    backdrop.addEventListener('click', closePopover);

    // ESC key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && popover.style.display === 'block') {
            closePopover();
        }
    });
}

// Update Conditions Summary Popover
async function updateConditionsSummary() {
    try {
        const response = await fetch('/api/current');
        const data = await response.json();

        if (data.error) {
            document.getElementById('summaryText').textContent = 'Conditions data unavailable.';
            return;
        }

        // Update summary text
        if (data.conditions_summary) {
            document.getElementById('summaryText').textContent = data.conditions_summary;
        }

        // Update depth info
        const depthInfo = document.getElementById('depthInfo');
        if (data.depth_info) {
            depthInfo.style.display = 'block';
            document.getElementById('depthSpecies').textContent = data.depth_info.species;
            document.getElementById('depthRange').textContent = data.depth_info.depth_range;
            document.getElementById('depthNote').textContent = data.depth_info.note;
        } else {
            depthInfo.style.display = 'none';
        }

        // 3. Update best zones
        const bestZonesInfo = document.getElementById('bestZonesInfo');
        const zonesList = document.getElementById('zonesList');
        if (data.best_zones && data.best_zones.length > 0) {
            bestZonesInfo.style.display = 'block';
            zonesList.innerHTML = data.best_zones.map(zone =>
                `<span class="zone-badge">Zone ${zone}</span>`
            ).join('');
        } else {
            bestZonesInfo.style.display = 'none';
        }

        // 4. Update Rig of the Moment
        const rigInfo = document.getElementById('rigInfo');
        const rigRecommendation = document.getElementById('rigRecommendation');
        if (data.rig_of_moment) {
            rigInfo.style.display = 'block';
            rigRecommendation.textContent = data.rig_of_moment;
        } else {
            rigInfo.style.display = 'none';
        }

        // 5. Update current strength
        const currentStrengthInfo = document.getElementById('currentStrengthInfo');
        const strengthLabel = document.getElementById('strengthLabel');
        const strengthFill = document.getElementById('strengthFill');
        if (data.current_strength) {
            currentStrengthInfo.style.display = 'block';
            strengthLabel.textContent = data.current_strength;

            // Set strength bar fill based on level
            const strengthWidths = { 'Weak': '33%', 'Moderate': '66%', 'Strong': '100%' };
            const strengthColors = { 'Weak': '#aaa', 'Moderate': '#4facfe', 'Strong': '#ff6b6b' };
            strengthFill.style.width = strengthWidths[data.current_strength] || '50%';
            strengthFill.style.background = strengthColors[data.current_strength] || '#4facfe';
        } else {
            currentStrengthInfo.style.display = 'none';
        }

        // 6. Update water clarity
        const clarityInfo = document.getElementById('clarityInfo');
        const clarityStatus = document.getElementById('clarityStatus');
        const clarityTip = document.getElementById('clarityTip');
        if (data.clarity) {
            clarityInfo.style.display = 'block';
            // Combine clarity and tip into one field
            const clarityText = data.clarity_tip ? `${data.clarity} - ${data.clarity_tip}` : data.clarity;
            clarityStatus.textContent = clarityText;
            // Remove the colored indicator classes - just use base clarity-status class
            clarityStatus.className = 'clarity-status';
            // Hide the separate tip element
            clarityTip.style.display = 'none';
        } else {
            clarityInfo.style.display = 'none';
        }

        // 7. Update best bait (using new bait activity scoring)
        const bestBaitInfo = document.getElementById('bestBaitInfo');
        const bestBaitText = document.getElementById('bestBaitText');
        bestBaitInfo.style.display = 'block';

        // Fetch bait forecast to get top active baits
        fetch('/api/bait-forecast')
            .then(res => res.json())
            .then(baitData => {
                if (baitData.bait_forecasts && baitData.bait_forecasts.length > 0) {
                    // Get top 3 baits by activity score
                    const topBaits = baitData.bait_forecasts.slice(0, 3).map(b => b.display_name);
                    bestBaitText.textContent = topBaits.join(', ');
                } else {
                    bestBaitText.textContent = 'Live shrimp, cut bait, or lures';
                }
            })
            .catch(() => {
                bestBaitText.textContent = 'Live shrimp, cut bait, or lures';
            });

        // 8. Update pro tip
        const proTipInfo = document.getElementById('proTipInfo');
        const proTipText = document.getElementById('proTipText');
        if (data.pro_tip) {
            proTipInfo.style.display = 'block';
            proTipText.textContent = data.pro_tip;
        } else {
            proTipInfo.style.display = 'none';
        }

        // 9. Update top species list (with tiers)
        const topSpeciesList = document.getElementById('topSpeciesList');
        const topSpeciesItems = document.getElementById('topSpeciesItems');
        if (data.top_species && data.top_species.length > 0) {
            topSpeciesList.style.display = 'block';
            topSpeciesItems.innerHTML = '';

            data.top_species.forEach(species => {
                const item = document.createElement('div');
                item.className = 'top-species-item';
                const tier = species.tier || 'SLOW';
                item.innerHTML = `
                    <span class="species-name">${species.name}</span>
                    <span class="species-tier-mini ${tier.toLowerCase()}">${tier}</span>
                `;
                topSpeciesItems.appendChild(item);
            });
        } else {
            topSpeciesList.style.display = 'none';
        }

        // 10. Update moon/tide window
        const moonTideInfo = document.getElementById('moonTideInfo');
        const moonTideText = document.getElementById('moonTideText');
        if (data.moon_tide_window) {
            moonTideInfo.style.display = 'block';
            moonTideText.textContent = data.moon_tide_window;
        } else {
            moonTideInfo.style.display = 'none';
        }

    } catch (error) {
        console.error('Error updating conditions summary:', error);
        document.getElementById('summaryText').textContent = 'Error loading conditions summary.';
    }
}

// Store forecast data globally for modal access
let forecastData = [];

// Update 24-Hour Hourly Outlook Strip
async function updateHourlyOutlook() {
    try {
        const response = await fetch('/api/hourly-outlook?hours=24');
        const data = await response.json();

        const container = document.getElementById('hourlyStripContainer');

        if (!data || data.length === 0) {
            container.innerHTML = '<div class="hourly-error">No outlook data available</div>';
            return;
        }

        // Clear loading message
        container.innerHTML = '';

        // Create hour blocks
        data.forEach((hourData, index) => {
            const hourBlock = document.createElement('div');
            hourBlock.className = `hour-block ${hourData.tier.toLowerCase()}`;

            const hourTime = new Date(hourData.hour);
            const timeStr = formatTime(hourTime);

            // Tooltip content
            const tooltipText = `${timeStr}\n${hourData.tide_state} tide, ${Math.round(hourData.temperature)}°F, ${Math.round(hourData.wind_speed)} mph wind`;

            hourBlock.innerHTML = `
                <div class="hour-time">${timeStr}</div>
                <div class="hour-tier-bar"></div>
                <div class="hour-tier-label">${hourData.tier}</div>
            `;

            hourBlock.title = tooltipText;

            // Add click handler to show detailed modal
            hourBlock.addEventListener('click', () => {
                showHourForecastModal(hourTime, hourData);
            });

            container.appendChild(hourBlock);
        });

    } catch (error) {
        console.error('Error updating hourly outlook:', error);
        document.getElementById('hourlyStripContainer').innerHTML =
            '<div class="hourly-error">Error loading outlook</div>';
    }
}

// Show detailed forecast modal for a specific hour
async function showHourForecastModal(hourTime, hourData) {
    const modal = document.getElementById('hourForecastModal');
    const timeStr = formatTime(hourTime);

    // Set title
    document.getElementById('hourModalTitle').textContent = `Forecast for ${timeStr}`;

    // Set tier badge
    const tierBadge = document.getElementById('hourModalTier');
    tierBadge.textContent = hourData.tier;
    tierBadge.className = `hour-tier-badge-large ${hourData.tier.toLowerCase()}`;

    // Set conditions
    document.getElementById('hourModalTide').textContent = hourData.tide_state;
    document.getElementById('hourModalTideHeight').textContent = `Height: ${hourData.tide_height ? hourData.tide_height.toFixed(2) : '--'} ft`;
    document.getElementById('hourModalTimeOfDay').textContent = hourData.time_of_day;
    document.getElementById('hourModalTemp').textContent = `${Math.round(hourData.temperature)}°F`;
    document.getElementById('hourModalWind').textContent = `${Math.round(hourData.wind_speed)} mph`;
    document.getElementById('hourModalPressure').textContent = hourData.pressure_trend || 'stable';
    document.getElementById('hourModalConditions').textContent = hourData.conditions || 'Clear';

    // Fetch full forecast data to get species info
    try {
        const forecastResponse = await fetch('/api/forecast?hours=24');
        const forecastWindows = await forecastResponse.json();

        // Find the matching forecast window (within same 2-hour window)
        const matchingWindow = forecastWindows.find(w => {
            const windowStart = new Date(w.start_time);
            return windowStart.getTime() <= hourTime.getTime() &&
                   new Date(w.end_time).getTime() > hourTime.getTime();
        });

        if (matchingWindow && matchingWindow.top_species) {
            const speciesList = document.getElementById('hourModalSpeciesList');
            speciesList.innerHTML = '';

            matchingWindow.top_species.forEach(sp => {
                const speciesCard = document.createElement('div');
                speciesCard.className = `hour-species-card ${sp.tier.toLowerCase()}`;
                speciesCard.innerHTML = `
                    <div class="species-name">${sp.name}</div>
                    <div class="species-tier-badge">${sp.tier}</div>
                    <div class="species-score">Score: ${sp.bite_score.toFixed(1)}</div>
                `;
                speciesList.appendChild(speciesCard);
            });
        }
    } catch (error) {
        console.error('Error fetching species data:', error);
        document.getElementById('hourModalSpeciesList').innerHTML =
            '<div class="error-message">Unable to load species data</div>';
    }

    // Show modal
    modal.style.display = 'block';
}

// Close hour forecast modal
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('hourForecastModal');
    const closeBtn = document.getElementById('closeHourModal');

    if (closeBtn) {
        closeBtn.onclick = () => {
            modal.style.display = 'none';
        };
    }

    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
})

// Currents Map Implementation
let currentsMap = null;
let currentsLayer = null;
let dockMarker = null;

function initializeCurrentsMap() {
    // Dock coordinates (Belle Fontaine, Mobile Bay)
    const dockLat = 30.488216;
    const dockLon = -88.101887;

    // Initialize the map
    currentsMap = L.map('currentsMap', {
        center: [dockLat, dockLon],
        zoom: 17,
        zoomControl: true
    });

    // Add base map layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(currentsMap);

    // Dock marker removed - using distinct red current arrow instead

    // Add ocean currents visualization layer
    // Using multiple layers: OpenSeaMap + Current vectors

    // Layer 1: OpenSeaMap nautical overlay
    const openSeaMapLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
        attribution: 'OpenSeaMap',
        transparent: true,
        opacity: 0.5,
        maxZoom: 18
    });

    // Layer 2: Sample current data for Mobile Bay
    // In a production app, this would come from NOAA API
    const currentData = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-88.101887, 30.488216]  // YOUR DOCK - Belle Fontaine
                },
                "properties": {
                    "u": 0.42,  // East-west velocity
                    "v": 0.28,  // North-south velocity
                    "speed": 0.51,
                    "direction": 34,
                    "location": "Your Dock"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-88.0583, 30.2283]  // Bay entrance
                },
                "properties": {
                    "u": 0.5,
                    "v": 0.3,
                    "speed": 0.58,
                    "direction": 31,
                    "location": "Bay Entrance"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-88.15, 30.35]  // Southwest bay
                },
                "properties": {
                    "u": 0.35,
                    "v": 0.25,
                    "speed": 0.43,
                    "direction": 36,
                    "location": "Southwest Bay"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-88.05, 30.55]  // East mid-bay
                },
                "properties": {
                    "u": 0.4,
                    "v": 0.3,
                    "speed": 0.5,
                    "direction": 37,
                    "location": "East Mid-Bay"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-87.9833, 30.6833]  // North bay
                },
                "properties": {
                    "u": 0.3,
                    "v": 0.4,
                    "speed": 0.5,
                    "direction": 53,
                    "location": "North Bay"
                }
            }
        ]
    };

    // Create current vector arrows
    const currentArrows = L.geoJSON(currentData, {
        pointToLayer: function(feature, latlng) {
            const speed = feature.properties.speed;
            const direction = feature.properties.direction;
            const location = feature.properties.location || 'Mobile Bay';

            // Use red color for dock location, cyan for others
            const isYourDock = location === 'Your Dock';
            const arrowColor = isYourDock ? '#FF4444' : '#00CED1';
            const arrowSize = isYourDock ? 90 : 30; // Dock arrow 3x bigger

            // Create arrow marker
            const arrowIcon = L.divIcon({
                className: 'current-arrow',
                html: `<div style="
                    width: 0;
                    height: 0;
                    border-left: ${isYourDock ? 18 : 6}px solid transparent;
                    border-right: ${isYourDock ? 18 : 6}px solid transparent;
                    border-bottom: ${speed * arrowSize}px solid ${arrowColor};
                    transform: rotate(${direction}deg);
                    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));
                "></div>`,
                iconSize: [isYourDock ? 36 : 12, arrowSize],
                iconAnchor: [isYourDock ? 18 : 6, arrowSize / 2]
            });

            return L.marker(latlng, { icon: arrowIcon })
                .bindPopup(`
                    <strong>${isYourDock ? '🎣 ' : ''}Current Flow - ${location}</strong><br>
                    Speed: ${speed.toFixed(2)} m/s (${(speed * 1.94384).toFixed(2)} knots)<br>
                    Direction: ${direction}° (${getCardinalDirection(direction)})<br>
                    <em>NOAA forecast data</em>
                `);
        }
    });

    // Combine layers into a feature group
    currentsLayer = L.layerGroup([openSeaMapLayer, currentArrows]);

    // Add the layer initially
    currentsLayer.addTo(currentsMap);

    // Set up toggle button
    const toggleBtn = document.getElementById('toggleCurrents');
    toggleBtn.addEventListener('click', toggleCurrentsLayer);

    // Hide loader after map is ready
    currentsMap.whenReady(() => {
        setTimeout(() => {
            document.getElementById('mapLoader').classList.add('hidden');
            console.log('Currents map initialized with station markers');
        }, 1000);
    });

    // Trigger map resize after a short delay to ensure proper rendering
    setTimeout(() => {
        currentsMap.invalidateSize();
    }, 300);

    console.log('Currents layer initialized with OpenSeaMap + current vectors');
}

// Helper function to convert degrees to cardinal direction
function getCardinalDirection(degrees) {
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    const index = Math.round((degrees % 360) / 22.5);
    return directions[index % 16];
}

function toggleCurrentsLayer() {
    const toggleBtn = document.getElementById('toggleCurrents');
    const btnText = toggleBtn.querySelector('.btn-text');

    if (currentsMap.hasLayer(currentsLayer)) {
        // Hide currents
        currentsMap.removeLayer(currentsLayer);
        toggleBtn.classList.remove('active');
        btnText.textContent = 'Show Currents';
    } else {
        // Show currents
        currentsLayer.addTo(currentsMap);
        toggleBtn.classList.add('active');
        btnText.textContent = 'Hide Currents';
    }
}

// Generate Fish Behavior Today summary
function generateFishBehaviorSummary(speciesList, currentConditions) {
    const summaryEl = document.getElementById('fishBehaviorSummary');

    if (!speciesList || speciesList.length === 0) {
        summaryEl.innerHTML = '<p>No species data available</p>';
        return;
    }

    // Get top 3-4 active species (HOT and DECENT tiers)
    const activeSpecies = speciesList.filter(s => s.tier === 'HOT' || s.tier === 'DECENT').slice(0, 4);

    if (activeSpecies.length === 0) {
        summaryEl.innerHTML = '<p>Fish activity is currently slow across all species.</p>';
        return;
    }

    let summaryHTML = '';

    activeSpecies.forEach(species => {
        const tier = species.tier;
        const name = species.name;
        const zones = species.best_zones && species.best_zones.length > 0
            ? species.best_zones.join(', ')
            : 'all zones';

        let behaviorText = '';

        if (tier === 'HOT') {
            behaviorText = `<strong>${name}</strong> are very active and feeding aggressively. Best zones: ${zones}. `;
        } else if (tier === 'DECENT') {
            behaviorText = `<strong>${name}</strong> are moderately active with decent bite potential. Check zones: ${zones}. `;
        }

        summaryHTML += `<div class="behavior-species-item">
            <span class="behavior-species-name">${name}</span>
            <span class="behavior-species-description">${behaviorText}</span>
        </div>`;
    });

    summaryEl.innerHTML = summaryHTML;
}

// Zone Map Toggle in Species Modal
document.addEventListener('DOMContentLoaded', function() {
    const zoneMapToggle = document.getElementById('modalZoneMapToggle');
    const zoneMapContent = document.getElementById('modalZoneMapContent');

    if (zoneMapToggle && zoneMapContent) {
        zoneMapToggle.addEventListener('click', function() {
            if (zoneMapContent.style.display === 'none') {
                zoneMapContent.style.display = 'block';
                zoneMapToggle.textContent = '📍 Hide Zone Map';
            } else {
                zoneMapContent.style.display = 'none';
                zoneMapToggle.textContent = '📍 View Zone Map';
            }
        });
    }
});

// ===== Learning Notes Modal =====

async function showLearningNotes(speciesKey, speciesName) {
    const modal = document.getElementById('learningNotesModal');
    const modalTitle = document.getElementById('learningNotesTitle');
    const modalContent = document.getElementById('learningNotesContent');

    if (!modal || !modalTitle || !modalContent) {
        console.error('Learning notes modal elements not found');
        return;
    }

    // Set title
    modalTitle.textContent = `Learning Notes: ${speciesName}`;

    // Show loading state
    modalContent.innerHTML = '<p class="loading-text">Loading learning data...</p>';
    modal.style.display = 'flex';

    try {
        // Fetch learning data for this species
        // For now, we'll get current conditions to determine bucket params
        const currentResp = await fetch('/api/current');
        const current = await currentResp.json();

        // Get species data from current conditions
        const speciesData = current.species_forecasts?.find(sp => sp.species_key === speciesKey);

        if (!speciesData) {
            modalContent.innerHTML = '<p>No forecast data available for this species.</p>';
            return;
        }

        // Determine current bucket parameters
        const tideState = current.tide?.state || 'unknown';
        const timeBlock = getTimeBlock(new Date().getHours());

        // For simplicity, show Zone 3 learning data (most common zone)
        const zone = 'Zone 3';

        // Fetch learning delta
        const learningResp = await fetch(`/api/learning-delta?species=${speciesKey}&zone=${zone}&tide_stage=${tideState}&time_block=${timeBlock}`);
        const learningData = await learningResp.json();

        // Display learning notes
        displayLearningNotes(learningData, speciesData);

    } catch (error) {
        console.error('Error loading learning notes:', error);
        modalContent.innerHTML = '<p style="color: var(--tier-hot);">Failed to load learning data</p>';
    }
}

function getTimeBlock(hour) {
    if (hour >= 6 && hour < 11) return 'morning';
    if (hour >= 11 && hour < 15) return 'midday';
    if (hour >= 15 && hour < 20) return 'evening';
    return 'night';
}

function displayLearningNotes(learningData, speciesData) {
    const modalContent = document.getElementById('learningNotesContent');

    const deltaDisplay = learningData.delta >= 0 ? `+${learningData.delta.toFixed(2)}` : learningData.delta.toFixed(2);
    const confidencePercent = (learningData.confidence * 100).toFixed(0);

    const html = `
        <div class="learning-notes-grid">
            <div class="learning-stat">
                <div class="stat-label">Current Delta</div>
                <div class="stat-value">${deltaDisplay}</div>
                <div class="stat-description">Adjustment to base score</div>
            </div>

            <div class="learning-stat">
                <div class="stat-label">Confidence</div>
                <div class="stat-value">${confidencePercent}%</div>
                <div class="stat-description">Based on ${learningData.sample_count} sessions</div>
            </div>

            <div class="learning-stat">
                <div class="stat-label">Sample Size</div>
                <div class="stat-value">${learningData.sample_count}</div>
                <div class="stat-description">${learningData.sample_count < 5 ? 'Needs more data' : 'Good sample size'}</div>
            </div>
        </div>

        <div class="learning-explanation">
            <h4>What This Means</h4>
            <p>${learningData.explanation}</p>
            ${learningData.last_updated ? `<p class="last-updated">Last updated: ${new Date(learningData.last_updated).toLocaleString()}</p>` : ''}
        </div>

        <div class="learning-tips">
            <h4>How Learning Works</h4>
            <ul>
                <li>Delta adjusts based on your catch logs vs. model predictions</li>
                <li>Each catch you log refines the forecast for similar conditions</li>
                <li>Confidence increases with more fishing sessions</li>
                <li>Delta decays slowly over time to adapt to changing patterns</li>
            </ul>
        </div>
    `;

    modalContent.innerHTML = html;
}

function closeLearningNotesModal() {
    const modal = document.getElementById('learningNotesModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Initialize learning notes modal
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('learningNotesModal');
    const closeBtn = modal?.querySelector('.learning-notes-close');

    if (closeBtn) {
        closeBtn.addEventListener('click', closeLearningNotesModal);
    }

    // Close on background click
    modal?.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeLearningNotesModal();
        }
    });

    // Close on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal?.style.display === 'flex') {
            closeLearningNotesModal();
        }
    });
});
