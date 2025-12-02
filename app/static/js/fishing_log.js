/**
 * Fishing Log JavaScript
 * Handles form submission, table updates, and stats display
 */

// Track if data has been loaded to avoid duplicate loads
let dataLoaded = false;

// Size category buttons (supports both .size-btn and .size-btn-compact)
function setupSizeButtons() {
    const sizeButtons = document.querySelectorAll('.size-btn, .size-btn-compact');
    const sizeBucketInput = document.getElementById('sizeBucket');

    if (!sizeBucketInput) {
        console.error('sizeBucket input not found');
        return;
    }

    console.log(`Found ${sizeButtons.length} size buttons`);

    sizeButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Size button clicked:', this.dataset.size);

            // Remove active class from all buttons
            sizeButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            // Set the hidden input value
            const size = this.dataset.size;
            sizeBucketInput.value = size;
            console.log('Size bucket value set to:', sizeBucketInput.value);
        });
    });
}

// Kept/Released toggle (supports both .toggle-btn and .toggle-btn-compact)
function setupKeptToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-btn, .toggle-btn-compact');
    const keptInput = document.getElementById('keptInput');

    if (!keptInput) {
        console.error('keptInput not found');
        return;
    }

    console.log(`Found ${toggleButtons.length} toggle buttons`);

    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Toggle button clicked:', this.dataset.kept);

            // Remove active class from all buttons
            toggleButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            // Set the hidden input value
            const kept = this.dataset.kept === 'true';
            keptInput.value = kept;
            console.log('Kept value set to:', keptInput.value);
        });
    });
}

// Predator Seen toggle (NEW - HYPERLOCAL SPEC)
function setupPredatorToggle() {
    const predatorButtons = document.querySelectorAll('#catchForm .toggle-btn-compact');
    const predatorInput = document.getElementById('predatorSeen');

    if (!predatorInput) {
        console.error('predatorSeen input not found');
        return;
    }

    console.log(`Found ${predatorButtons.length} predator toggle buttons`);

    predatorButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const value = this.dataset.value;
            console.log('Predator button clicked:', value);

            // Remove active class from all buttons in this group
            predatorButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            // Set the hidden input value
            predatorInput.value = value;
            console.log('Predator seen value set to:', predatorInput.value);
        });
    });
}

// Cast net and trap sync between bait type and method
function setupCastNetSync() {
    const baitTypeSelect = document.getElementById('baitType');
    const methodSelect = document.getElementById('method');

    if (!baitTypeSelect || !methodSelect) {
        console.error('Bait type or method select not found');
        return;
    }

    console.log('Cast net and trap sync initialized');

    // When bait type changes to cast net or trap, set method to match
    baitTypeSelect.addEventListener('change', function() {
        console.log('Bait type changed to:', this.value);
        if (this.value === 'cast net') {
            methodSelect.value = 'cast net';
            console.log('Auto-set method to: cast net');
        } else if (this.value === 'trap') {
            methodSelect.value = 'trap';
            console.log('Auto-set method to: trap');
        }
    });

    // When method changes to cast net or trap, set bait type to match
    methodSelect.addEventListener('change', function() {
        console.log('Method changed to:', this.value);
        if (this.value === 'cast net') {
            baitTypeSelect.value = 'cast net';
            console.log('Auto-set bait type to: cast net');
        } else if (this.value === 'trap') {
            baitTypeSelect.value = 'trap';
            console.log('Auto-set bait type to: trap');
        }
    });
}

// Form submission
function setupFormSubmit() {
    const form = document.getElementById('catchForm');
    const messageDiv = document.getElementById('catchFormMessage');

    if (!form) {
        console.error('catchForm not found');
        return;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Gather form data
        const formData = new FormData(form);
        const data = {
            species: formData.get('species'),
            dock_side: formData.get('dock_side') || null,
            size_length_in: formData.get('size_length_in') ? parseInt(formData.get('size_length_in')) : null,
            size_bucket: formData.get('size_bucket') || null,
            quantity: formData.get('quantity') ? parseInt(formData.get('quantity')) : 1,
            bait_type: formData.get('bait_type') || null,
            method: formData.get('method') || null,
            kept: formData.get('kept') === 'true',
            notes: formData.get('notes') || null
        };

        // Validate required fields
        if (!data.species) {
            showMessage('Please select a species', 'error');
            return;
        }
        if (!data.size_bucket) {
            showMessage('Please select a size category', 'error');
            return;
        }
        if (!data.bait_type) {
            showMessage('Please select a bait type', 'error');
            return;
        }

        try {
            // Show submitting state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Logging...';

            // Submit to API
            const response = await fetch('/api/catches', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error('Failed to log catch');
            }

            const result = await response.json();

            // Show success message
            showMessage(`✓ Catch logged: ${result.species}`, 'success');

            // Clear form (but keep some fields)
            const lastSpecies = data.species;
            const lastDockSide = data.dock_side;
            const lastBaitType = data.bait_type;
            const lastMethod = data.method;

            form.reset();

            // Restore persistent fields
            document.getElementById('catchSpecies').value = lastSpecies;
            if (lastDockSide) {
                document.getElementById('dockSide').value = lastDockSide;
            }
            if (lastBaitType) {
                document.getElementById('baitType').value = lastBaitType;
            }
            if (lastMethod) {
                document.getElementById('method').value = lastMethod;
            }
            // Reset quantity to 1
            document.getElementById('quantity').value = '1';

            // Clear size buttons
            document.querySelectorAll('.size-btn, .size-btn-compact').forEach(b => b.classList.remove('active'));

            // Reload catches table
            loadRecentCatches();
            loadStats();

            // Reset button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;

        } catch (error) {
            console.error('Error logging catch:', error);
            showMessage('Error logging catch. Please try again.', 'error');

            // Reset button
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Log Catch';
        }
    });
}

// Show message helper
function showMessage(message, type) {
    const messageDiv = document.getElementById('catchFormMessage');
    messageDiv.textContent = message;
    messageDiv.className = `form-message ${type}`;
    messageDiv.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// Species filter
function setupSpeciesFilter() {
    const filterSelect = document.getElementById('speciesFilter');
    if (!filterSelect) return;

    filterSelect.addEventListener('change', function() {
        loadRecentCatches(this.value);
    });
}

// Store catches data globally for modal access
let recentCatchesData = [];
let currentCatchId = null;  // Store current catch ID for deletion

// Load recent catches
async function loadRecentCatches(speciesFilter = '') {
    const listDiv = document.getElementById('catchesList');
    if (!listDiv) return;

    try {
        let url = '/api/catches?limit=20';
        if (speciesFilter) {
            url += `&species=${encodeURIComponent(speciesFilter)}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load catches');

        const catches = await response.json();

        if (catches.length === 0) {
            listDiv.innerHTML = '<p class="loading-text">No catches logged yet</p>';
            return;
        }

        // Store catches data for modal access
        recentCatchesData = catches;

        listDiv.innerHTML = catches.map((c, index) => createCatchCard(c, index)).join('');

        // Add click event listeners
        document.querySelectorAll('.catch-log-card').forEach((card, index) => {
            card.addEventListener('click', () => openCatchModal(catches[index]));
        });

    } catch (error) {
        console.error('Error loading catches:', error);
        listDiv.innerHTML = '<p class="loading-text" style="color: var(--tier-hot);">Error loading catches</p>';
    }
}

// Create two-line catch card
function createCatchCard(c, index) {
    const date = new Date(c.timestamp);
    const timeStr = date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        timeZone: 'America/Chicago'
    });
    const qty = c.quantity || 1;
    const species = c.species_display || c.species;
    const sizeClass = c.size_bucket || 'Unknown';
    const zone = c.zone_id || 'Unknown';

    return `
        <div class="catch-log-card" data-index="${index}">
            <div class="log-card-line1">${timeStr} – ${zone}</div>
            <div class="log-card-line2">${qty} ${species} – ${sizeClass}</div>
        </div>
    `;
}

// Open catch detail modal
function openCatchModal(catchData) {
    const modal = document.getElementById('catchDetailModal');
    if (!modal) return;

    // Store catch ID for deletion
    currentCatchId = catchData.id;

    // Populate modal with catch details
    const date = new Date(catchData.timestamp);
    const dateStr = date.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        timeZone: 'America/Chicago'
    });

    document.getElementById('modalCatchSpecies').textContent = catchData.species_display || catchData.species;
    document.getElementById('modalCatchSize').textContent = catchData.size_bucket || 'Unknown';
    document.getElementById('modalCatchDateTime').textContent = dateStr;
    document.getElementById('modalCatchZone').textContent = catchData.zone_id || 'Unknown';
    document.getElementById('modalCatchQuantity').textContent = catchData.quantity || 1;
    document.getElementById('modalCatchLength').textContent = catchData.size_length_in ? catchData.size_length_in + '"' : 'Not recorded';
    document.getElementById('modalCatchBait').textContent = catchData.bait_used || 'Not recorded';
    document.getElementById('modalCatchRig').textContent = catchData.presentation || 'Not recorded';
    document.getElementById('modalCatchKept').textContent = catchData.kept ? 'Kept' : 'Released';
    document.getElementById('modalCatchNotes').textContent = catchData.notes || 'No notes';

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Delete catch
async function deleteCatch() {
    if (!currentCatchId) return;

    if (!confirm('Are you sure you want to delete this catch?')) {
        return;
    }

    try {
        const response = await fetch(`/api/catches/${currentCatchId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            closeCatchModal();
            loadRecentCatches();
            loadStats();
        } else {
            alert('Failed to delete catch');
        }
    } catch (error) {
        console.error('Error deleting catch:', error);
        alert('Error deleting catch');
    }
}

// Close catch detail modal
function closeCatchModal() {
    const modal = document.getElementById('catchDetailModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Load stats
async function loadStats() {
    const statsContent = document.getElementById('statsContent');
    if (!statsContent) return;

    try {
        const response = await fetch('/api/catches/stats?days=30');
        if (!response.ok) throw new Error('Failed to load stats');

        const stats = await response.json();

        if (stats.total_catches === 0) {
            statsContent.innerHTML = '<p>No catches in the last 30 days</p>';
            return;
        }

        let html = `
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${stats.total_catches}</div>
                    <div class="stat-label">Total Catches</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.kept_count}</div>
                    <div class="stat-label">Kept</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.released_count}</div>
                    <div class="stat-label">Released</div>
                </div>
            </div>
        `;

        if (stats.by_species && stats.by_species.length > 0) {
            html += '<h4 style="margin-top: 15px;">Top Species</h4><ul class="species-stats">';
            stats.by_species.slice(0, 5).forEach(s => {
                html += `<li>${s.species_display || s.species}: ${s.count}</li>`;
            });
            html += '</ul>';
        }

        statsContent.innerHTML = html;

    } catch (error) {
        console.error('Error loading stats:', error);
        statsContent.innerHTML = '<p style="color: #dc3545;">Error loading stats</p>';
    }
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing fishing log...');

    // Set up event handlers immediately
    setupSizeButtons();
    setupKeptToggle();
    setupPredatorToggle(); // NEW - HYPERLOCAL SPEC
    setupCastNetSync();
    setupFormSubmit();
    setupSpeciesFilter();

    // Set up catch detail modal click-outside-to-close
    const catchModal = document.getElementById('catchDetailModal');
    if (catchModal) {
        catchModal.addEventListener('click', function(e) {
            if (e.target === catchModal) {
                closeCatchModal();
            }
        });
    }

    // Set up delete catch button
    const deleteCatchBtn = document.getElementById('deleteCatchBtn');
    if (deleteCatchBtn) {
        deleteCatchBtn.addEventListener('click', deleteCatch);
    }

    // Load data when fishing log tab is clicked
    const logTabButton = document.querySelector('[data-tab="fishinglog"]');
    if (logTabButton) {
        logTabButton.addEventListener('click', function() {
            if (!dataLoaded) {
                dataLoaded = true;
                loadRecentCatches();
                loadStats();
            }
        });
    }

    console.log('Fishing log initialization complete');
});
