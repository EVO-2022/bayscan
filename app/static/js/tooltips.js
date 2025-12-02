/**
 * Tooltip System for BayScan
 * Provides micro-tooltips with ? icons for key concepts
 */

// Tooltip definitions
const TOOLTIPS = {
    tide: "Tide is how high or low the water is, which changes where fish move.",
    current: "Current is how fast water is moving past the dock, which pushes bait and fish.",
    clarity: "Clarity is how clear or muddy the water is, which affects how well fish can see baits.",
    confidence: "Confidence shows how stable conditions are and how much you can trust today's forecast.",
    zoneMap: "The zone map breaks the dock into zones 1–5 so you know where to cast.",
    baitActivity: "Bait activity shows when and where you can catch live bait for fishing.",
    tideState: "Tide state shows if water is rising (incoming), falling (outgoing), or slack (not moving).",
    windSpeed: "Wind speed affects water chop and can make bait and fish more active.",
    waterTemp: "Water temperature affects fish metabolism and feeding behavior.",
    moonPhase: "Moon phase influences tide strength and fish feeding patterns.",
    pressure: "Barometric pressure changes can trigger or slow fish feeding.",
    bestZones: "Best zones are where fish and bait are most likely to be active right now.",
    rigOfMoment: "Recommended rig setup based on current conditions and target species.",
    fishBehavior: "How fish are positioned and behaving based on today's conditions."
};

/**
 * Create tooltip HTML element
 */
function createTooltip(key, text) {
    const wrapper = document.createElement('span');
    wrapper.className = 'tooltip-wrapper';
    wrapper.style.position = 'relative';
    wrapper.style.display = 'inline-block';

    const trigger = document.createElement('span');
    trigger.className = 'tooltip-trigger';
    trigger.textContent = '?';
    trigger.setAttribute('data-tooltip-key', key);
    trigger.setAttribute('aria-label', text);
    trigger.setAttribute('role', 'button');
    trigger.setAttribute('tabindex', '0');

    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.setAttribute('role', 'tooltip');

    wrapper.appendChild(trigger);
    wrapper.appendChild(tooltip);

    return wrapper;
}

/**
 * Add tooltip to an element
 */
function addTooltip(element, tooltipKey) {
    if (!element || !TOOLTIPS[tooltipKey]) {
        console.warn(`Tooltip not found for key: ${tooltipKey}`);
        return;
    }

    const tooltipEl = createTooltip(tooltipKey, TOOLTIPS[tooltipKey]);
    element.appendChild(tooltipEl);
}

/**
 * Add tooltip after text (for headers, labels, etc.)
 */
function addTooltipAfterText(selector, tooltipKey) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
        // Check if tooltip already exists
        if (element.querySelector('.tooltip-wrapper')) {
            return;
        }
        addTooltip(element, tooltipKey);
    });
}

/**
 * Show tooltip
 */
function showTooltip(trigger) {
    const wrapper = trigger.closest('.tooltip-wrapper');
    if (!wrapper) return;

    const tooltip = wrapper.querySelector('.tooltip');
    if (!tooltip) return;

    // Hide all other tooltips
    document.querySelectorAll('.tooltip.show').forEach(t => {
        if (t !== tooltip) {
            t.classList.remove('show');
        }
    });

    // Position and show tooltip
    tooltip.classList.add('show');

    // Adjust position if tooltip goes off screen
    const rect = tooltip.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
        tooltip.style.left = 'auto';
        tooltip.style.right = '0';
    }
    if (rect.bottom > window.innerHeight) {
        tooltip.style.top = 'auto';
        tooltip.style.bottom = '100%';
        tooltip.style.marginBottom = '4px';
    }
}

/**
 * Hide tooltip
 */
function hideTooltip(trigger) {
    const wrapper = trigger.closest('.tooltip-wrapper');
    if (!wrapper) return;

    const tooltip = wrapper.querySelector('.tooltip');
    if (tooltip) {
        tooltip.classList.remove('show');
    }
}

/**
 * Initialize tooltips
 */
function initTooltips() {
    console.log('Initializing tooltips...');

    // Add tooltips to key elements
    const tooltipMappings = [
        { selector: 'h4:contains("Tide")', key: 'tide' },
        { selector: 'h4:contains("Current")', key: 'current' },
        { selector: 'h4:contains("Clarity")', key: 'clarity' },
        { selector: 'h4:contains("Confidence")', key: 'confidence' },
        { selector: '.zone-map-caption', key: 'zoneMap' },
    ];

    // Since :contains() doesn't work in querySelectorAll, we'll use a different approach
    // Add tooltips to specific known elements

    // Tide
    const tideElements = document.querySelectorAll('h4');
    tideElements.forEach(el => {
        const text = el.textContent.trim();
        if (text.includes('Tide') && !text.includes('Current') && !el.querySelector('.tooltip-wrapper')) {
            addTooltip(el, 'tide');
        } else if (text.includes('Current Strength')) {
            addTooltip(el, 'current');
        } else if (text.includes('Water Clarity') || text.includes('Clarity')) {
            addTooltip(el, 'clarity');
        } else if (text.includes('Confidence')) {
            addTooltip(el, 'confidence');
        }
    });

    // Zone map captions
    const zoneCaptions = document.querySelectorAll('.zone-map-caption');
    zoneCaptions.forEach(el => {
        if (!el.querySelector('.tooltip-wrapper')) {
            addTooltip(el, 'zoneMap');
        }
    });

    // Set up event listeners
    setupTooltipListeners();

    console.log('Tooltips initialized');
}

/**
 * Set up tooltip event listeners
 */
function setupTooltipListeners() {
    // Hover events for desktop
    document.addEventListener('mouseover', (e) => {
        if (e.target.classList.contains('tooltip-trigger')) {
            showTooltip(e.target);
        }
    });

    document.addEventListener('mouseout', (e) => {
        if (e.target.classList.contains('tooltip-trigger')) {
            setTimeout(() => hideTooltip(e.target), 100);
        }
    });

    // Click/tap events for mobile
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('tooltip-trigger')) {
            e.stopPropagation();
            const wrapper = e.target.closest('.tooltip-wrapper');
            const tooltip = wrapper?.querySelector('.tooltip');

            if (tooltip) {
                const isShown = tooltip.classList.contains('show');
                // Hide all tooltips first
                document.querySelectorAll('.tooltip.show').forEach(t => t.classList.remove('show'));
                // Toggle this tooltip
                if (!isShown) {
                    showTooltip(e.target);
                }
            }
        } else if (!e.target.closest('.tooltip')) {
            // Click outside - hide all tooltips
            document.querySelectorAll('.tooltip.show').forEach(t => t.classList.remove('show'));
        }
    });

    // Keyboard support
    document.addEventListener('keydown', (e) => {
        if (e.target.classList.contains('tooltip-trigger')) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const tooltip = e.target.closest('.tooltip-wrapper')?.querySelector('.tooltip');
                if (tooltip) {
                    tooltip.classList.toggle('show');
                }
            } else if (e.key === 'Escape') {
                hideTooltip(e.target);
            }
        }
    });
}

/**
 * Add tooltip programmatically to any element
 */
function addCustomTooltip(element, tooltipText) {
    if (!element) return;

    const key = `custom_${Date.now()}`;
    TOOLTIPS[key] = tooltipText;
    addTooltip(element, key);
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTooltips);
} else {
    initTooltips();
}

// Export for use in other modules
window.BayScanTooltips = {
    init: initTooltips,
    add: addCustomTooltip,
    TOOLTIPS: TOOLTIPS
};
