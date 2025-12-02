/**
 * Timezone utilities for BayScan frontend
 * Ensures all times display in Central Time (America/Chicago)
 */

/**
 * Format a datetime string (ISO format) to Central time
 * @param {string} isoString - ISO format datetime string with timezone
 * @param {object} options - Formatting options
 * @returns {string} Formatted time string
 */
function formatCentralTime(isoString, options = {}) {
    if (!isoString) return '';

    const date = new Date(isoString);
    const defaultOptions = {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
        timeZone: 'America/Chicago'
    };

    const formatOptions = { ...defaultOptions, ...options };
    return date.toLocaleTimeString('en-US', formatOptions);
}

/**
 * Format a datetime string to Central time with timezone abbreviation
 * @param {string} isoString - ISO format datetime string
 * @param {boolean} showTimezone - Whether to show CST/CDT abbreviation
 * @returns {string} Formatted time like "3:45 PM CST"
 */
function formatCentralTimeWithZone(isoString, showTimezone = true) {
    if (!isoString) return '';

    const date = new Date(isoString);
    const timeStr = date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
        timeZone: 'America/Chicago'
    });

    if (!showTimezone) {
        return timeStr;
    }

    // Get timezone abbreviation (CST or CDT)
    const tzStr = date.toLocaleTimeString('en-US', {
        timeZone: 'America/Chicago',
        timeZoneName: 'short'
    });

    // Extract timezone abbreviation from string like "3:45:00 PM CST"
    const tzMatch = tzStr.match(/\s([A-Z]{3})$/);
    const tzAbbr = tzMatch ? tzMatch[1] : 'CST';

    return `${timeStr} ${tzAbbr}`;
}

/**
 * Format a datetime string to Central date
 * @param {string} isoString - ISO format datetime string
 * @param {object} options - Formatting options
 * @returns {string} Formatted date string
 */
function formatCentralDate(isoString, options = {}) {
    if (!isoString) return '';

    const date = new Date(isoString);
    const defaultOptions = {
        month: 'short',
        day: 'numeric',
        timeZone: 'America/Chicago'
    };

    const formatOptions = { ...defaultOptions, ...options };
    return date.toLocaleDateString('en-US', formatOptions);
}

/**
 * Format a datetime string to Central date and time
 * @param {string} isoString - ISO format datetime string
 * @param {boolean} showTimezone - Whether to show timezone abbreviation
 * @returns {string} Formatted string like "Nov 23, 3:45 PM CST"
 */
function formatCentralDateTime(isoString, showTimezone = true) {
    if (!isoString) return '';

    const dateStr = formatCentralDate(isoString);
    const timeStr = formatCentralTimeWithZone(isoString, showTimezone);

    return `${dateStr}, ${timeStr}`;
}

/**
 * Get current time in Central timezone
 * @returns {Date} Current date/time
 */
function getCentralNow() {
    return new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Chicago' }));
}

// Backward compatibility: Update the existing formatTime function
// This will be used throughout the existing codebase
function formatTime(dateOrString) {
    // Handle both Date objects and ISO strings
    if (typeof dateOrString === 'string') {
        return formatCentralTimeWithZone(dateOrString, false);
    } else if (dateOrString instanceof Date) {
        return dateOrString.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
            timeZone: 'America/Chicago'
        });
    }
    return '';
}
