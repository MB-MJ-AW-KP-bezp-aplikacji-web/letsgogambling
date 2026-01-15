/* Shared utility functions for casino games */

/**
 * Get a cookie value by name
 * @param {string} name - Cookie name
 * @returns {string|undefined} Cookie value
 */
function getCookie(name) {
    return document.cookie.split('; ')
        .find(row => row.startsWith(name + '='))
        ?.split('=')[1];
}

/**
 * Format a number with commas (e.g., 16986566 -> "16,986,566")
 * @param {number} amount - Number to format
 * @returns {string} Formatted string
 */
function formatMoney(amount) {
    return Math.floor(amount).toLocaleString('en-US');
}

/**
 * Get current balance from element, handling comma-formatted numbers
 * @param {string} elementId - ID of the balance element
 * @returns {number} Balance value
 */
function getCurrentBalance(elementId) {
    const balanceText = document.getElementById(elementId).textContent.replace(/,/g, '');
    return parseFloat(balanceText) || 0;
}

/**
 * Parse a bet input value, handling comma-formatted numbers
 * @param {HTMLInputElement} inputEl - Input element
 * @returns {number} Bet value
 */
function getBetValue(inputEl) {
    const betText = inputEl.value.replace(/,/g, '');
    return parseFloat(betText) || 0;
}

/**
 * Set bet amount on an input element
 * @param {HTMLInputElement} inputEl - Input element
 * @param {number} amount - Amount to set
 * @param {boolean} [format=false] - Whether to format with commas
 */
function setBetAmount(inputEl, amount, format = false) {
    if (amount > 0) {
        inputEl.value = format ? formatMoney(amount) : Math.floor(amount);
    } else {
        inputEl.value = '';
    }
}

/**
 * Add amount to current bet
 * @param {HTMLInputElement} inputEl - Input element
 * @param {number} amount - Amount to add
 * @param {boolean} [format=false] - Whether to format with commas
 */
function addToBet(inputEl, amount, format = false) {
    const current = getBetValue(inputEl);
    setBetAmount(inputEl, current + amount, format);
}

/**
 * Multiply current bet by a factor
 * @param {HTMLInputElement} inputEl - Input element
 * @param {number} multiplier - Multiplier value
 * @param {boolean} [format=false] - Whether to format with commas
 */
function multiplyBet(inputEl, multiplier, format = false) {
    const current = getBetValue(inputEl);
    setBetAmount(inputEl, Math.floor(current * multiplier), format);
}

/**
 * Set bet to all-in (full balance)
 * @param {HTMLInputElement} inputEl - Input element
 * @param {string} balanceElementId - ID of balance element
 * @param {number} [divisor=1] - Divide balance by this (for multi-machine games)
 * @param {boolean} [format=false] - Whether to format with commas
 */
function allIn(inputEl, balanceElementId, divisor = 1, format = false) {
    const balance = getCurrentBalance(balanceElementId);
    setBetAmount(inputEl, Math.floor(balance / divisor), format);
}
