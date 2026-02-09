/**
 * Utility functions for Kupi Slona frontend
 * Extracted from inline scripts to reduce duplication
 */

/**
 * Get a cookie value by name (used for CSRF tokens)
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value or null if not found
 */
export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Get human-readable name for a hue value
 * @param {number|null} hue - Hue value (0-360)
 * @returns {string} Human-readable color name
 */
export function getHueName(hue) {
    const names = {
        0: 'Красный',
        30: 'Оранжевый',
        60: 'Желтый',
        120: 'Зеленый',
        180: 'Голубой',
        240: 'Синий',
        300: 'Фиолетовый',
        330: 'Розовый'
    };
    return names[hue] || 'Не выбран';
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<void>}
 */
export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
        } catch (e) {
            console.error('Failed to copy text:', e);
        }
        document.body.removeChild(textArea);
    }
}
