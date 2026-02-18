/**
 * Alpine.js app for tariff selection page (index)
 * Handles basic and advanced elephant purchases
 */

import { getCookie, getHueName } from './utils.js';
import { ordersAPI } from './api.js';

/**
 * Create tariff selection Alpine.js app
 * @returns {Object} Alpine.js app data
 */
export function tariffApp() {
    return {
        selectedHue: 0, // Красный по умолчанию
        loading: false,
        message: '',
        messageType: '',

        async buyBasic() {
            await this.createOrder('basic');
        },

        async buyAdvanced() {
            await this.createOrder('advanced');
        },

        async createOrder(tariff) {
            this.loading = true;
            this.message = '';

            try {
                const desiredColor = tariff === 'advanced' ? `HUE:${this.selectedHue}` : null;
                const data = await ordersAPI.create(tariff, desiredColor);

                // Redirect to YooKassa payment page
                window.location.href = data.payment_url;
            } catch (error) {
                console.error('Order creation error:', error);
                this.showMessage('error', error.message || 'Произошла ошибка');
                this.loading = false;
            }
        },

        showMessage(type, text) {
            this.messageType = type;
            this.message = text;
        },

        getHueName(hue) {
            return getHueName(hue);
        },

        getCookie(name) {
            return getCookie(name);
        }
    };
}
