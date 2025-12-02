/**
 * Skeleton Loading States for BayScan
 * Provides shimmer placeholders while data loads
 */

/**
 * Create skeleton element
 */
function createSkeleton(type, customClass = '') {
    const skeleton = document.createElement('div');
    skeleton.className = `skeleton skeleton-${type} ${customClass}`;
    return skeleton;
}

/**
 * Create skeleton for species/bait card
 */
function createCardSkeleton() {
    const card = document.createElement('div');
    card.className = 'skeleton skeleton-card';
    card.style.padding = '15px';

    const header = createSkeleton('title');
    header.style.width = '70%';

    const text1 = createSkeleton('text');
    text1.style.width = '90%';

    const text2 = createSkeleton('text');
    text2.style.width = '60%';

    card.appendChild(header);
    card.appendChild(text1);
    card.appendChild(text2);

    return card;
}

/**
 * Create skeleton for hourly outlook strip
 */
function createHourlySkeletons(count = 12) {
    const container = document.createElement('div');
    container.className = 'hourly-skeleton-container';
    container.style.display = 'flex';
    container.style.gap = '8px';
    container.style.overflowX = 'auto';
    container.style.padding = '10px 0';

    for (let i = 0; i < count; i++) {
        const hourBlock = createSkeleton('hour-block');
        container.appendChild(hourBlock);
    }

    return container;
}

/**
 * Create skeleton for conditions summary
 */
function createConditionsSkeleton() {
    const container = document.createElement('div');
    container.className = 'skeleton-conditions';
    container.style.padding = '15px';

    const title = createSkeleton('title');
    title.style.width = '50%';
    title.style.marginBottom = '15px';

    const text1 = createSkeleton('text');
    text1.style.width = '100%';
    text1.style.marginBottom = '8px';

    const text2 = createSkeleton('text');
    text2.style.width = '85%';

    container.appendChild(title);
    container.appendChild(text1);
    container.appendChild(text2);

    return container;
}

/**
 * Create skeleton for species grid
 */
function createSpeciesGridSkeleton(cardCount = 6) {
    const grid = document.createElement('div');
    grid.className = 'species-grid skeleton-grid';

    for (let i = 0; i < cardCount; i++) {
        const card = createCardSkeleton();
        grid.appendChild(card);
    }

    return grid;
}

/**
 * Create skeleton for weekly summary
 */
function createWeeklySummarySkeleton() {
    const container = document.createElement('div');
    container.className = 'skeleton-weekly-summary';
    container.style.padding = '20px';

    // Title
    const title = createSkeleton('title');
    title.style.width = '40%';
    title.style.marginBottom = '20px';

    // Create 5 section skeletons
    const sections = [];
    for (let i = 0; i < 5; i++) {
        const section = document.createElement('div');
        section.style.marginBottom = '20px';
        section.style.padding = '15px';
        section.style.background = 'var(--bg-tertiary)';
        section.style.borderRadius = '8px';

        const sectionTitle = createSkeleton('title');
        sectionTitle.style.width = '60%';
        sectionTitle.style.marginBottom = '10px';

        const sectionText = createSkeleton('text');
        sectionText.style.width = '80%';

        section.appendChild(sectionTitle);
        section.appendChild(sectionText);
        sections.push(section);
    }

    container.appendChild(title);
    sections.forEach(s => container.appendChild(s));

    return container;
}

/**
 * Show skeleton loading state for an element
 */
function showSkeleton(targetElement, skeletonType = 'card') {
    if (!targetElement) return null;

    let skeleton;
    switch (skeletonType) {
        case 'hourly':
            skeleton = createHourlySkeletons();
            break;
        case 'conditions':
            skeleton = createConditionsSkeleton();
            break;
        case 'species-grid':
            skeleton = createSpeciesGridSkeleton();
            break;
        case 'weekly-summary':
            skeleton = createWeeklySummarySkeleton();
            break;
        case 'card':
        default:
            skeleton = createCardSkeleton();
            break;
    }

    // Store original content
    const originalContent = targetElement.innerHTML;
    targetElement.setAttribute('data-original-content', originalContent);

    // Replace with skeleton
    targetElement.innerHTML = '';
    targetElement.appendChild(skeleton);

    return skeleton;
}

/**
 * Hide skeleton and restore/show content
 */
function hideSkeleton(targetElement, newContent = null) {
    if (!targetElement) return;

    // Get original or new content
    const content = newContent || targetElement.getAttribute('data-original-content') || '';

    // Fade out skeleton
    const skeleton = targetElement.querySelector('.skeleton, .skeleton-grid, .hourly-skeleton-container, .skeleton-conditions, .skeleton-weekly-summary');
    if (skeleton) {
        skeleton.style.opacity = '0';
        skeleton.style.transition = 'opacity 0.3s ease';

        setTimeout(() => {
            if (newContent) {
                targetElement.innerHTML = '';
                if (typeof newContent === 'string') {
                    targetElement.innerHTML = newContent;
                } else if (newContent instanceof HTMLElement) {
                    targetElement.appendChild(newContent);
                }
            } else {
                targetElement.innerHTML = content;
            }

            // Fade in content
            targetElement.style.opacity = '0';
            setTimeout(() => {
                targetElement.style.transition = 'opacity 0.3s ease';
                targetElement.style.opacity = '1';
            }, 10);
        }, 300);
    }
}

/**
 * Initialize skeleton loaders for main page elements
 */
function initSkeletonLoaders() {
    console.log('Initializing skeleton loaders...');

    // Show skeletons on page load for key sections
    const sectionsToSkeleton = [
        { selector: '#speciesList', type: 'species-grid' },
        { selector: '#baitList', type: 'species-grid' },
        { selector: '.hourly-outlook-content', type: 'hourly' },
    ];

    sectionsToSkeleton.forEach(({ selector, type }) => {
        const element = document.querySelector(selector);
        if (element && element.children.length === 0) {
            showSkeleton(element, type);
        }
    });

    console.log('Skeleton loaders ready');
}

/**
 * Wrapper for fetch with skeleton loading
 */
async function fetchWithSkeleton(targetElement, skeletonType, fetchFunction) {
    showSkeleton(targetElement, skeletonType);

    try {
        const result = await fetchFunction();
        hideSkeleton(targetElement, result);
        return result;
    } catch (error) {
        hideSkeleton(targetElement);
        throw error;
    }
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSkeletonLoaders);
} else {
    initSkeletonLoaders();
}

// Export for use in other modules
window.BayScanSkeleton = {
    show: showSkeleton,
    hide: hideSkeleton,
    createCard: createCardSkeleton,
    createHourly: createHourlySkeletons,
    createConditions: createConditionsSkeleton,
    createSpeciesGrid: createSpeciesGridSkeleton,
    createWeeklySummary: createWeeklySummarySkeleton,
    fetchWith: fetchWithSkeleton
};
