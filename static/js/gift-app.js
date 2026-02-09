/**
 * Alpine.js app for public gift page
 * Handles claiming gifts
 */

import { getCookie } from './utils.js';
import { giftsAPI } from './api.js';

/**
 * Create gift page Alpine.js app
 * @returns {Object} Alpine.js app data
 */
export function giftPage() {
    return {
        claiming: false,

        async claimGift() {
            if (!confirm('Вы уверены, что хотите принять этот подарок?')) {
                return;
            }

            this.claiming = true;

            try {
                const uuid = window.location.pathname.split('/')[2];
                const data = await giftsAPI.claim(uuid);

                alert('🎉 ' + data.message);
                window.location.href = '/dashboard/';
            } catch (error) {
                console.error('Error:', error);
                alert('Произошла ошибка при принятии подарка');
            } finally {
                this.claiming = false;
            }
        },

        getCookie(name) {
            return getCookie(name);
        }
    };
}
