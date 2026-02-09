/**
 * API client for Kupi Slona
 * Centralized API calls with CSRF token handling
 */

import { getCookie } from './utils.js';

/**
 * Base fetch wrapper with CSRF token
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>}
 */
async function apiFetch(url, options = {}) {
    const csrfToken = getCookie('csrftoken');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (csrfToken && options.method && options.method !== 'GET') {
        headers['X-CSRFToken'] = csrfToken;
    }

    return fetch(url, {
        ...options,
        headers
    });
}

/**
 * Orders API
 */
export const ordersAPI = {
    /**
     * Create a new order
     * @param {string} tariffName - Tariff name ('basic' or 'advanced')
     * @param {string|null} desiredColor - Color (null for basic, HUE:XXX or #RRGGBB for advanced)
     * @returns {Promise<Object>} Order data
     */
    async create(tariffName, desiredColor = null) {
        const response = await apiFetch('/api/orders', {
            method: 'POST',
            body: JSON.stringify({
                tariff_name: tariffName,
                desired_color: desiredColor
            })
        });
        return response.json();
    },

    /**
     * Get list of user's orders
     * @returns {Promise<Array>} List of orders
     */
    async list() {
        const response = await apiFetch('/api/orders');
        return response.json();
    },

    /**
     * Get order by ID
     * @param {number} orderId - Order ID
     * @returns {Promise<Object>} Order data
     */
    async get(orderId) {
        const response = await apiFetch(`/api/orders/${orderId}`);
        return response.json();
    }
};

/**
 * Elephants API
 */
export const elephantsAPI = {
    /**
     * Get list of user's elephants
     * @returns {Promise<Array>} List of elephants
     */
    async list() {
        const response = await apiFetch('/api/elephants');
        return response.json();
    },

    /**
     * Get elephant by ID
     * @param {number} elephantId - Elephant ID
     * @returns {Promise<Object>} Elephant data
     */
    async get(elephantId) {
        const response = await apiFetch(`/api/elephants/${elephantId}`);
        return response.json();
    },

    /**
     * Get download URL for elephant
     * @param {number} elephantId - Elephant ID
     * @returns {string} Download URL
     */
    getDownloadUrl(elephantId) {
        return `/api/elephants/${elephantId}/download`;
    }
};

/**
 * Gifts API
 */
export const giftsAPI = {
    /**
     * Create a gift link
     * @param {Object} giftData - Gift data
     * @param {number} giftData.elephant_id - Elephant ID to gift
     * @param {string} giftData.sender_name - Sender name (optional)
     * @param {string} giftData.recipient_name - Recipient name (optional)
     * @param {string} giftData.message - Gift message (optional)
     * @returns {Promise<Object>} Gift link data
     */
    async create(giftData) {
        const response = await apiFetch('/api/gifts/', {
            method: 'POST',
            body: JSON.stringify(giftData)
        });
        return response.json();
    },

    /**
     * Get list of sent gifts
     * @returns {Promise<Array>} List of sent gifts
     */
    async listSent() {
        const response = await apiFetch('/api/gifts/sent');
        return response.json();
    },

    /**
     * Get public gift info by UUID
     * @param {string} uuid - Gift UUID
     * @returns {Promise<Object>} Public gift data
     */
    async getPublic(uuid) {
        const response = await apiFetch(`/api/gifts/public/${uuid}`);
        return response.json();
    },

    /**
     * Claim a gift
     * @param {string} uuid - Gift UUID
     * @returns {Promise<Object>} Claim response
     */
    async claim(uuid) {
        const response = await apiFetch(`/api/gifts/public/${uuid}/claim`, {
            method: 'POST'
        });
        return response.json();
    }
};
