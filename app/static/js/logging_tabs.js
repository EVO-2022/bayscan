// Logging Tabs Handler - Fish, Bait, Predator
// Manages sub-tabs in Fishing Log section, zone map modal, and log forms

// Store current log IDs for deletion
let currentBaitLogId = null;
let currentPredatorLogId = null;

// ===== Zone Map Modal =====
function initZoneMapModal() {
    const modalBtn = document.getElementById('zoneMapModalBtn');
    const modal = document.getElementById('zoneMapModal');
    const closeBtn = modal?.querySelector('.zone-map-modal-close');

    if (!modalBtn || !modal) return;

    // Open modal
    modalBtn.addEventListener('click', () => {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scroll
    });

    // Close modal
    const closeModal = () => {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scroll
    };

    closeBtn?.addEventListener('click', closeModal);

    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Close on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });
}

// ===== Logging Sub-Tabs =====
function initLoggingSubTabs() {
    const tabs = document.querySelectorAll('.logging-subtab');
    const fishContent = document.getElementById('fishLogContent');
    const baitContent = document.getElementById('baitLogContent');
    const predatorContent = document.getElementById('predatorLogContent');

    if (!tabs.length || !fishContent || !baitContent || !predatorContent) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/hide content
            fishContent.style.display = targetTab === 'fish' ? 'block' : 'none';
            baitContent.style.display = targetTab === 'bait' ? 'block' : 'none';
            predatorContent.style.display = targetTab === 'predators' ? 'block' : 'none';

            // Load data for the active tab
            if (targetTab === 'bait') {
                loadBaitLogs();
            } else if (targetTab === 'predators') {
                loadPredatorLogs();
            }
        });
    });
}

// ===== Auto-fill Current Time =====
function setCurrentTime(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const now = new Date();
    // Format as ISO datetime-local (YYYY-MM-DDTHH:MM)
    const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
    input.value = localDateTime;
}

// ===== Fish Log Form - NEW HYPERLOCAL SPEC =====
function initFishForm() {
    const form = document.getElementById('catchForm');
    const messageDiv = document.getElementById('catchFormMessage');

    if (!form) return;

    // Auto-fill current time
    setCurrentTime('catchTime');

    // Conditional field: Days Since Last Checked (for traps)
    const rigField = document.getElementById('presentation');
    const daysSinceField = document.getElementById('fishDaysSinceField');
    const daysSinceInput = document.getElementById('fishDaysSince');

    if (rigField && daysSinceField && daysSinceInput) {
        rigField.addEventListener('change', () => {
            const rigValue = rigField.value.toLowerCase();
            const isTrap = rigValue.includes('trap') || rigValue.includes('pot');

            if (isTrap) {
                daysSinceField.style.display = 'block';
                daysSinceInput.required = true;
            } else {
                daysSinceField.style.display = 'none';
                daysSinceInput.required = false;
                daysSinceInput.value = ''; // Clear value when hidden
            }
        });
    }

    // Part C: Bidirectional Bait/Rig Auto-fill
    const baitField = document.getElementById('baitUsed');

    // Bait → Rig mapping
    const baitToRig = {
        'live fish': 'free-lined',
        'live shrimp': 'cork',
        'cut bait': 'carolina',
        'frozen shrimp': 'carolina',
        'frozen fish': 'carolina',
        'sandflea': 'bottom rig',
        'lure': 'jig',
        'cast net': 'cast net',
        'trap': 'trap'
    };

    // Rig → Bait mapping
    const rigToBait = {
        'jig': 'lure',
        'cork': 'live shrimp',
        'carolina': 'cut bait',
        'free-lined': 'live fish',
        'topwater': 'lure',
        'bottom rig': 'cut bait',
        'cast net': 'cast net',
        'trap': 'trap'
    };

    if (baitField && rigField) {
        // Auto-fill Rig when Bait changes
        baitField.addEventListener('change', () => {
            const baitValue = baitField.value.toLowerCase();
            const currentRig = rigField.value;

            // Only auto-fill if Rig is empty or default
            if (!currentRig && baitToRig[baitValue]) {
                rigField.value = baitToRig[baitValue];

                // Trigger rig change event to update conditional fields
                rigField.dispatchEvent(new Event('change'));
            }
        });

        // Auto-fill Bait when Rig changes
        rigField.addEventListener('change', () => {
            const rigValue = rigField.value.toLowerCase();
            const currentBait = baitField.value;

            // Only auto-fill if Bait is empty or default
            if (!currentBait && rigToBait[rigValue]) {
                baitField.value = rigToBait[rigValue];
            }
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const data = {
            species: formData.get('species'),
            zone_id: formData.get('zone_id'),
            distance_from_dock: formData.get('distance_from_dock') || null,
            depth_estimate: formData.get('depth_estimate') || null,
            structure_type: formData.get('structure_type') || null,
            size_bucket: formData.get('size_bucket') || null,
            size_length_in: formData.get('size_length_in') ? parseInt(formData.get('size_length_in')) : null,
            quantity: formData.get('quantity') ? parseInt(formData.get('quantity')) : 1,
            bait_used: formData.get('bait_used') || null,
            presentation: formData.get('presentation') || null,
            kept: formData.get('kept') === 'true',
            notes: formData.get('notes') || null,
            days_since_last_checked: formData.get('days_since_last_checked') ? parseInt(formData.get('days_since_last_checked')) : null,
            timestamp: formData.get('timestamp') || new Date().toISOString()
        };

        try {
            const response = await fetch('/api/catches', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                showMessage(messageDiv, 'Catch logged successfully!', 'success');
                form.reset();
                setCurrentTime('catchTime'); // Reset time to current
                // Reload fish logs if there's a function for it
                if (typeof loadRecentCatches === 'function') {
                    loadRecentCatches();
                }
            } else {
                const error = await response.json();
                showMessage(messageDiv, error.detail || 'Failed to log catch', 'error');
            }
        } catch (error) {
            console.error('Fish log error:', error);
            showMessage(messageDiv, 'Network error. Please try again.', 'error');
        }
    });
}

// ===== Bait Log Form - NEW HYPERLOCAL SPEC =====
function initBaitForm() {
    const form = document.getElementById('baitForm');
    const messageDiv = document.getElementById('baitFormMessage');

    if (!form) return;

    // Auto-fill current time
    setCurrentTime('baitTime');

    // Conditional field: Days Since Last Checked (for traps)
    const methodField = document.getElementById('baitMethod');
    const daysSinceField = document.getElementById('baitDaysSinceField');
    const daysSinceInput = document.getElementById('baitDaysSince');

    if (methodField && daysSinceField && daysSinceInput) {
        methodField.addEventListener('change', () => {
            const methodValue = methodField.value.toLowerCase();
            const isTrap = methodValue.includes('trap') || methodValue.includes('pot');

            if (isTrap) {
                daysSinceField.style.display = 'block';
                daysSinceInput.required = true;
            } else {
                daysSinceField.style.display = 'none';
                daysSinceInput.required = false;
                daysSinceInput.value = ''; // Clear value when hidden
            }
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const data = {
            bait_species: formData.get('bait_species'),
            method: formData.get('method'),  // REQUIRED - NEW
            zone_id: formData.get('zone_id'),  // REQUIRED
            quantity_estimate: formData.get('quantity_estimate') || null,  // NEW
            structure_type: formData.get('structure_type') || null,  // NEW
            notes: formData.get('notes') || null,
            days_since_last_checked: formData.get('days_since_last_checked') ? parseInt(formData.get('days_since_last_checked')) : null,
            timestamp: formData.get('timestamp') || new Date().toISOString()  // Use form timestamp
        };

        try {
            const response = await fetch('/api/bait-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                showMessage(messageDiv, 'Bait logged successfully!', 'success');
                form.reset();
                setCurrentTime('baitTime'); // Reset time to current
                loadBaitLogs(); // Reload list
            } else {
                const error = await response.json();
                showMessage(messageDiv, error.detail || 'Failed to log bait', 'error');
            }
        } catch (error) {
            console.error('Bait log error:', error);
            showMessage(messageDiv, 'Network error. Please try again.', 'error');
        }
    });
}

// ===== Predator Log Form =====
function initPredatorForm() {
    const form = document.getElementById('predatorForm');
    const messageDiv = document.getElementById('predatorFormMessage');

    if (!form) return;

    // Auto-fill current time
    setCurrentTime('predatorTime');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const data = {
            type: 'predator',
            predator: formData.get('predator'),
            zone: formData.get('zone'),
            time: formData.get('time') || new Date().toISOString(),
            behavior: formData.get('behavior'),
            tide: formData.get('tide') || null,
            notes: formData.get('notes') || null,
        };

        try {
            const response = await fetch('/api/predator-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                showMessage(messageDiv, 'Predator sighting logged successfully!', 'success');
                form.reset();
                setCurrentTime('predatorTime'); // Reset time to current
                loadPredatorLogs(); // Reload list
            } else {
                const error = await response.json();
                showMessage(messageDiv, error.detail || 'Failed to log predator', 'error');
            }
        } catch (error) {
            console.error('Predator log error:', error);
            showMessage(messageDiv, 'Network error. Please try again.', 'error');
        }
    });
}

// ===== Load Bait Logs =====
async function loadBaitLogs() {
    const listDiv = document.getElementById('baitLogsList');
    if (!listDiv) return;

    listDiv.innerHTML = '<p class="loading-text">Loading bait logs...</p>';

    try {
        const response = await fetch('/api/bait-logs?limit=20');
        if (!response.ok) throw new Error('Failed to load bait logs');

        const logs = await response.json();

        if (logs.length === 0) {
            listDiv.innerHTML = '<p class="loading-text">No bait logs yet. Start logging!</p>';
            return;
        }

        listDiv.innerHTML = logs.map((log, index) => createBaitLogCard(log, index)).join('');

        // Add click event listeners
        document.querySelectorAll('.bait-log-card').forEach((card, index) => {
            card.addEventListener('click', () => openBaitDetailModal(logs[index]));
        });
    } catch (error) {
        console.error('Load bait logs error:', error);
        listDiv.innerHTML = '<p class="loading-text" style="color: var(--tier-hot);">Failed to load bait logs</p>';
    }
}

// ===== Load Predator Logs =====
async function loadPredatorLogs() {
    const listDiv = document.getElementById('predatorLogsList');
    if (!listDiv) return;

    listDiv.innerHTML = '<p class="loading-text">Loading predator logs...</p>';

    try {
        const response = await fetch('/api/predator-logs?limit=20');
        if (!response.ok) throw new Error('Failed to load predator logs');

        const logs = await response.json();

        if (logs.length === 0) {
            listDiv.innerHTML = '<p class="loading-text">No predator logs yet. Start logging!</p>';
            return;
        }

        listDiv.innerHTML = logs.map((log, index) => createPredatorLogCard(log, index)).join('');

        // Add click event listeners
        document.querySelectorAll('.predator-log-card').forEach((card, index) => {
            card.addEventListener('click', () => openPredatorDetailModal(logs[index]));
        });
    } catch (error) {
        console.error('Load predator logs error:', error);
        listDiv.innerHTML = '<p class="loading-text" style="color: var(--tier-hot);">Failed to load predator logs</p>';
    }
}

// ===== Create Bait Log Card =====
function createBaitLogCard(log, index) {
    const date = new Date(log.time);
    const timeStr = date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        timeZone: 'America/Chicago'
    });
    const species = formatBaitSpecies(log.bait_species);
    const zone = log.zone || 'Unknown';
    const qty = log.quantity || 'Unknown';
    const method = log.how_caught || 'Unknown';

    return `
        <div class="bait-log-card" data-index="${index}">
            <div class="log-card-line1">${timeStr} – ${zone}</div>
            <div class="log-card-line2">${qty} ${species} – ${method}</div>
        </div>
    `;
}

// ===== Create Predator Log Card =====
function createPredatorLogCard(log, index) {
    const date = new Date(log.time);
    const timeStr = date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        timeZone: 'America/Chicago'
    });
    const predator = log.predator.charAt(0).toUpperCase() + log.predator.slice(1);
    const zone = log.zone || 'Unknown';
    const behavior = log.behavior || 'Unknown';
    // Predators don't have quantity, so we'll just show "1" or omit it
    const qty = 1;

    return `
        <div class="predator-log-card" data-index="${index}">
            <div class="log-card-line1">${timeStr} – ${zone}</div>
            <div class="log-card-line2">${qty} ${predator} – ${behavior}</div>
        </div>
    `;
}

// ===== Open Bait Detail Modal =====
function openBaitDetailModal(logData) {
    const modal = document.getElementById('baitDetailModal');
    if (!modal) return;

    // Store log ID for deletion
    currentBaitLogId = logData.id;

    const date = new Date(logData.time);
    const dateStr = date.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        timeZone: 'America/Chicago'
    });

    const species = formatBaitSpecies(logData.bait_species);
    const method = logData.how_caught || 'Unknown method';
    const headerText = `${species} – ${method}`;

    document.getElementById('modalBaitLogSpecies').textContent = headerText;
    document.getElementById('modalBaitDateTime').textContent = dateStr;
    document.getElementById('modalBaitZone').textContent = logData.zone || 'Not recorded';
    document.getElementById('modalBaitQuantity').textContent = logData.quantity || 'Not recorded';
    document.getElementById('modalBaitMethod').textContent = logData.how_caught || 'Not recorded';
    document.getElementById('modalBaitStructure').textContent = logData.structure_type || 'Not recorded';
    document.getElementById('modalBaitLogNotes').textContent = logData.notes || 'No notes';

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// ===== Delete Bait Log =====
async function deleteBaitLog() {
    if (!currentBaitLogId) return;

    if (!confirm('Are you sure you want to delete this bait log?')) {
        return;
    }

    try {
        const response = await fetch(`/api/bait-logs/${currentBaitLogId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            closeBaitDetailModal();
            loadBaitLogs();
        } else {
            alert('Failed to delete bait log');
        }
    } catch (error) {
        console.error('Error deleting bait log:', error);
        alert('Error deleting bait log');
    }
}

// ===== Close Bait Detail Modal =====
function closeBaitDetailModal() {
    const modal = document.getElementById('baitDetailModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// ===== Open Predator Detail Modal =====
function openPredatorDetailModal(logData) {
    const modal = document.getElementById('predatorDetailModal');
    if (!modal) return;

    // Store log ID for deletion
    currentPredatorLogId = logData.id;

    const date = new Date(logData.time);
    const dateStr = date.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        timeZone: 'America/Chicago'
    });

    const predator = logData.predator.charAt(0).toUpperCase() + logData.predator.slice(1);
    const behavior = logData.behavior || 'Unknown behavior';
    const headerText = `${predator} – ${behavior}`;

    document.getElementById('modalPredatorType').textContent = headerText;
    document.getElementById('modalPredatorDateTime').textContent = dateStr;
    document.getElementById('modalPredatorZone').textContent = logData.zone || 'Not recorded';
    document.getElementById('modalPredatorBehavior').textContent = logData.behavior || 'Not recorded';
    document.getElementById('modalPredatorTide').textContent = logData.tide || 'Not recorded';
    document.getElementById('modalPredatorNotes').textContent = logData.notes || 'No notes';

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// ===== Delete Predator Log =====
async function deletePredatorLog() {
    if (!currentPredatorLogId) return;

    if (!confirm('Are you sure you want to delete this predator log?')) {
        return;
    }

    try {
        const response = await fetch(`/api/predator-logs/${currentPredatorLogId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            closePredatorDetailModal();
            loadPredatorLogs();
        } else {
            alert('Failed to delete predator log');
        }
    } catch (error) {
        console.error('Error deleting predator log:', error);
        alert('Error deleting predator log');
    }
}

// ===== Close Predator Detail Modal =====
function closePredatorDetailModal() {
    const modal = document.getElementById('predatorDetailModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// ===== Format Bait Species Name =====
function formatBaitSpecies(key) {
    const names = {
        live_shrimp: 'Live Shrimp',
        live_bait_fish: 'Live Bait Fish',
        mud_minnows: 'Mud Minnows',
        pinfish: 'Pinfish',
        menhaden: 'Menhaden',
        fiddler_crabs: 'Fiddler Crabs',
    };
    return names[key] || key;
}

// ===== Check if Predator Activity is Recent (4 hours) =====
function isRecentPredatorActivity(logTime) {
    const now = new Date();
    const logDate = new Date(logTime);
    const diffHours = (now - logDate) / (1000 * 60 * 60);
    return diffHours <= 4;
}

// ===== Show Form Message =====
function showMessage(messageDiv, text, type) {
    if (!messageDiv) return;

    messageDiv.textContent = text;
    messageDiv.className = `form-message ${type}`;
    messageDiv.style.display = 'block';

    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 4000);
}

// ===== Get Recent Predator Activity by Zone =====
async function getRecentPredatorActivity() {
    try {
        const response = await fetch('/api/predator-logs?limit=50');
        if (!response.ok) return {};

        const logs = await response.json();

        // Group by zone, only keep recent activity (within 4 hours)
        const activityByZone = {};
        logs.forEach(log => {
            if (log.is_recent) {
                if (!activityByZone[log.zone]) {
                    activityByZone[log.zone] = {
                        predator: log.predator,
                        behavior: log.behavior,
                        time: log.time
                    };
                }
            }
        });

        return activityByZone;
    } catch (error) {
        console.error('Error fetching predator activity:', error);
        return {};
    }
}

// ===== Add Predator Tags to Zone Displays =====
async function addPredatorTagsToZones() {
    const activity = await getRecentPredatorActivity();

    // Find all zone badge elements
    const zoneBadges = document.querySelectorAll('.zone-badge');

    zoneBadges.forEach(badge => {
        const zoneText = badge.textContent.trim(); // e.g., "Zone 3"

        if (activity[zoneText]) {
            // Add predator tag after the badge
            const tag = document.createElement('div');
            tag.className = 'predator-activity-tag';
            tag.textContent = `Recent activity: ${activity[zoneText].predator} – ${activity[zoneText].behavior}`;

            // Insert after the badge
            if (badge.nextSibling) {
                badge.parentNode.insertBefore(tag, badge.nextSibling);
            } else {
                badge.parentNode.appendChild(tag);
            }
        }
    });
}

// ===== Export for use in other modules =====
window.addPredatorTagsToZones = addPredatorTagsToZones;
window.getRecentPredatorActivity = getRecentPredatorActivity;

// ===== Initialize All on DOM Load =====
document.addEventListener('DOMContentLoaded', () => {
    initZoneMapModal();
    initLoggingSubTabs();
    initFishForm();  // NEW - Initialize Fish Log form with datetime
    initBaitForm();
    initPredatorForm();

    // Set up bait detail modal click-outside-to-close
    const baitDetailModal = document.getElementById('baitDetailModal');
    if (baitDetailModal) {
        baitDetailModal.addEventListener('click', function(e) {
            if (e.target === baitDetailModal) {
                closeBaitDetailModal();
            }
        });
    }

    // Set up delete bait log button
    const deleteBaitLogBtn = document.getElementById('deleteBaitLogBtn');
    if (deleteBaitLogBtn) {
        deleteBaitLogBtn.addEventListener('click', deleteBaitLog);
    }

    // Set up predator detail modal click-outside-to-close
    const predatorDetailModal = document.getElementById('predatorDetailModal');
    if (predatorDetailModal) {
        predatorDetailModal.addEventListener('click', function(e) {
            if (e.target === predatorDetailModal) {
                closePredatorDetailModal();
            }
        });
    }

    // Set up delete predator log button
    const deletePredatorLogBtn = document.getElementById('deletePredatorLogBtn');
    if (deletePredatorLogBtn) {
        deletePredatorLogBtn.addEventListener('click', deletePredatorLog);
    }

    // Load initial bait logs (only if tab is active)
    // Fish logs are handled by existing fishing_log.js

    // Add predator tags to zones after a short delay (wait for zones to load)
    setTimeout(() => {
        addPredatorTagsToZones();
    }, 1500);
});

console.log('Logging tabs module loaded');
