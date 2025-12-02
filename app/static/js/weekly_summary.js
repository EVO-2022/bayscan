/**
 * Weekly Summary Tab - JavaScript
 * Fetches and displays weekly fishing summary data
 */

// Load weekly summary data when tab is activated
function loadWeeklySummary() {
    console.log('Loading weekly summary...');

    fetch('/api/weekly-summary')
        .then(response => response.json())
        .then(data => {
            console.log('Weekly summary data:', data);
            displayWeeklySummary(data);
        })
        .catch(error => {
            console.error('Error loading weekly summary:', error);
            showNoDataMessage();
        });
}

// Display weekly summary data
function displayWeeklySummary(data) {
    // Check if there's any data
    if (data.total_catches === 0 || data.message) {
        showNoDataMessage();
        return;
    }

    // Hide no-data message
    document.getElementById('weeklyNoData').style.display = 'none';

    // 1. Total Catches (Hero)
    document.getElementById('weeklyTotalCatches').textContent = data.total_catches;

    // 2. Best Species Section
    const bestSpeciesSection = document.getElementById('weeklyBestSpeciesSection');
    if (data.best_species) {
        bestSpeciesSection.innerHTML = `
            <div class="stat-value">${data.best_species.species}</div>
            <div class="stat-count">${data.best_species.count} caught this week</div>
        `;
    } else {
        bestSpeciesSection.innerHTML = '<p>No data available</p>';
    }

    // 3. Best Bait Section
    const bestBaitSection = document.getElementById('weeklyBestBaitSection');
    if (data.best_bait) {
        bestBaitSection.innerHTML = `
            <div class="stat-value">${data.best_bait.bait}</div>
            <div class="stat-count">${data.best_bait.catches} catches</div>
        `;
    } else {
        bestBaitSection.innerHTML = '<p>No data available</p>';
    }

    // 4. Best Zones Section
    const bestZonesSection = document.getElementById('weeklyBestZonesSection');
    if (data.best_zones && data.best_zones.length > 0) {
        const topZones = data.best_zones.slice(0, 3);
        bestZonesSection.innerHTML = topZones.map(zone => `
            <span class="zone-tag">${zone.zone} - ${zone.catches} catches</span>
        `).join('');
    } else {
        bestZonesSection.innerHTML = '<p>No zone data available</p>';
    }

    // 5. Best Tide Window Section
    const bestTideSection = document.getElementById('weeklyBestTideSection');
    if (data.best_tide_stage) {
        bestTideSection.innerHTML = `
            <div class="stat-value">${data.best_tide_stage.tide}</div>
            <div class="stat-count">${data.best_tide_stage.catches} catches during this tide stage</div>
        `;
    } else {
        bestTideSection.innerHTML = '<p>No tide data available</p>';
    }

    // 6. Best Time of Day Section
    const bestTimeSection = document.getElementById('weeklyBestTimeSection');
    if (data.best_hours && data.best_hours.length > 0) {
        const topTimes = data.best_hours.slice(0, 3);
        bestTimeSection.innerHTML = topTimes.map(time => `
            <span class="time-tag">${time.time_of_day} (Avg Score: ${time.avg_score})</span>
        `).join('');
    } else {
        bestTimeSection.innerHTML = '<p>No time data available</p>';
    }
}

// Show no data message
function showNoDataMessage() {
    document.getElementById('weeklyNoData').style.display = 'block';

    // Clear all sections
    document.getElementById('weeklyTotalCatches').textContent = '0';
    document.getElementById('weeklyBestSpeciesSection').innerHTML = '<p>No data</p>';
    document.getElementById('weeklyBestBaitSection').innerHTML = '<p>No data</p>';
    document.getElementById('weeklyBestZonesSection').innerHTML = '<p>No data</p>';
    document.getElementById('weeklyBestTideSection').innerHTML = '<p>No data</p>';
    document.getElementById('weeklyBestTimeSection').innerHTML = '<p>No data</p>';
}

// Initialize weekly summary when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Weekly Summary JS initialized');

    // Listen for tab changes
    const weeklyTab = document.querySelector('[data-tab="weeklysummary"]');
    if (weeklyTab) {
        weeklyTab.addEventListener('click', function() {
            // Load data when tab is clicked
            loadWeeklySummary();
        });
    }
});
