/**
 * Alpine.js app for dashboard page
 * Manages elephants, orders, and gifts
 */

import { getCookie, getHueName, copyToClipboard } from './utils.js';
import { elephantsAPI, ordersAPI, giftsAPI } from './api.js';

/**
 * Create dashboard Alpine.js app
 * @param {Object} config - Configuration
 * @param {string} config.username - Current user's username
 * @returns {Object} Alpine.js app data
 */
export function dashboard(config = {}) {
    return {
        loading: true,
        elephants: [],
        orders: [],
        sentGifts: [],
        showGiftModal: false,
        selectedElephant: null,
        giftForm: {
            sender_name: config.username || '',
            recipient_name: '',
            message: ''
        },
        giftLoading: false,
        giftLink: null,

        // Purchase form
        showPurchase: false,
        selectedHue: 0, // Красный по умолчанию
        purchaseLoading: false,
        purchaseMessage: '',
        purchaseMessageType: '',

        async loadData() {
            this.loading = true;
            try {
                await Promise.all([
                    this.loadElephants(),
                    this.loadOrders(),
                    this.loadSentGifts()
                ]);
            } finally {
                this.loading = false;
            }
        },

        async loadElephants() {
            try {
                this.elephants = await elephantsAPI.list();
            } catch (error) {
                console.error('Failed to load elephants:', error);
            }
        },

        async loadOrders() {
            try {
                this.orders = await ordersAPI.list();
            } catch (error) {
                console.error('Failed to load orders:', error);
            }
        },

        async loadSentGifts() {
            try {
                this.sentGifts = await giftsAPI.listSent();
            } catch (error) {
                console.error('Failed to load sent gifts:', error);
            }
        },

        downloadElephant(elephantId) {
            window.open(elephantsAPI.getDownloadUrl(elephantId), '_blank');
        },

        openGiftModal(elephant) {
            this.selectedElephant = elephant;
            this.showGiftModal = true;
            this.giftLink = null;
            this.giftForm = {
                sender_name: config.username || '',
                recipient_name: '',
                message: ''
            };
        },

        closeGiftModal() {
            this.showGiftModal = false;
            this.selectedElephant = null;
            this.giftLink = null;
        },

        async createGift() {
            this.giftLoading = true;
            try {
                const data = await giftsAPI.create({
                    elephant_id: this.selectedElephant.id,
                    sender_name: this.giftForm.sender_name,
                    recipient_name: this.giftForm.recipient_name,
                    message: this.giftForm.message
                });

                this.giftLink = window.location.origin + data.public_url;
                await this.loadSentGifts();
                await this.loadElephants();
            } catch (error) {
                console.error('Error:', error);
                alert('Произошла ошибка при создании подарка');
            } finally {
                this.giftLoading = false;
            }
        },

        async copyGiftLink(uuid) {
            const link = `${window.location.origin}/gift/${uuid}/`;
            try {
                await copyToClipboard(link);
                alert('Ссылка скопирована!');
            } catch (error) {
                console.error('Failed to copy:', error);
                alert('Не удалось скопировать ссылку');
            }
        },

        async copyGiftLinkFromModal() {
            try {
                await copyToClipboard(this.giftLink);
                alert('Ссылка скопирована!');
            } catch (error) {
                console.error('Failed to copy:', error);
                alert('Не удалось скопировать ссылку');
            }
        },

        async buyBasic() {
            await this.createOrder('basic');
        },

        async buyAdvanced() {
            await this.createOrder('advanced');
        },

        async createOrder(tariff) {
            this.purchaseLoading = true;
            this.purchaseMessage = '';

            try {
                const desiredColor = tariff === 'advanced' ? `HUE:${this.selectedHue}` : null;
                const data = await ordersAPI.create(tariff, desiredColor);

                this.purchaseMessage = 'Заказ успешно создан! Генерация слона началась...';
                this.purchaseMessageType = 'success';

                // Hide purchase form
                this.showPurchase = false;

                // Reload data to show new order
                await this.loadOrders();

                // Clear message after 3 seconds
                setTimeout(() => {
                    this.purchaseMessage = '';
                    // Reload elephants to show new elephant when ready
                    this.loadElephants();
                }, 3000);
            } catch (error) {
                console.error('Error:', error);
                this.purchaseMessage = error.message || 'Произошла ошибка при создании заказа';
                this.purchaseMessageType = 'error';
            } finally {
                this.purchaseLoading = false;
            }
        },

        getHueName(hue) {
            return getHueName(hue);
        },

        getCookie(name) {
            return getCookie(name);
        }
    };
}
