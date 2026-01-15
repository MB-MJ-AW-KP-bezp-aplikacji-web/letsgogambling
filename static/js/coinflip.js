/* Coinflip Game Logic */

const csrftoken = getCookie('csrftoken');

const balanceEl = document.getElementById("balance");
const betInput = document.getElementById("bet-amount");
const flipBtn = document.getElementById("flip-btn");
const resultCard = document.getElementById("result-card");
const resultEmoji = document.getElementById("result-emoji");
const resultText = document.getElementById("result-text");
const resultSubtext = document.getElementById("result-subtext");

let selectedChoice = null;

function initCoinflip() {
    // Bet control buttons via data attributes
    document.querySelectorAll('[data-bet-set]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            setBetAmountCoinflip(parseFloat(btn.dataset.betSet));
        });
    });
    document.querySelectorAll('[data-bet-add]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            addToBetCoinflip(parseFloat(btn.dataset.betAdd));
        });
    });
    document.querySelectorAll('[data-bet-multiply]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            multiplyBetCoinflip(parseFloat(btn.dataset.betMultiply));
        });
    });
    document.querySelectorAll('[data-bet-allin]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            allInCoinflip();
        });
    });

    // Restore last bet from localStorage
    const savedBet = localStorage.getItem('coinflip_bet');
    if (savedBet) {
        betInput.value = savedBet;
    }

    // Save bet amount when it changes and ensure integer
    betInput.addEventListener('change', function() {
        const val = parseFloat(betInput.value) || 0;
        betInput.value = val > 0 ? Math.floor(val) : '';
        localStorage.setItem('coinflip_bet', betInput.value);
    });

    // Fetch initial balance
    fetch("/api/balance/")
        .then(function(res) { return res.json(); })
        .then(function(data) {
            balanceEl.textContent = formatMoney(data.balance);
        });

    // Coin option selection
    document.querySelectorAll('.coin-option').forEach(function(option) {
        option.addEventListener('click', function() {
            document.querySelectorAll('.coin-option').forEach(function(o) {
                o.classList.remove('selected');
            });
            option.classList.add('selected');
            selectedChoice = parseInt(option.dataset.choice);
            updateFlipButton();
        });
    });

    // Update button state when bet changes
    betInput.addEventListener('input', updateFlipButton);

    // Initial button state
    updateFlipButton();

    // Flip button
    flipBtn.addEventListener("click", handleFlip);
}

function getCurrentBalanceCoinflip() {
    const balanceText = balanceEl.textContent.replace(/,/g, '');
    return parseFloat(balanceText) || 0;
}

function setBetAmountCoinflip(amount) {
    betInput.value = amount > 0 ? Math.floor(amount) : '';
    localStorage.setItem('coinflip_bet', betInput.value);
}

function addToBetCoinflip(amount) {
    const current = parseFloat(betInput.value) || 0;
    setBetAmountCoinflip(current + amount);
}

function multiplyBetCoinflip(multiplier) {
    const current = parseFloat(betInput.value) || 0;
    setBetAmountCoinflip(Math.floor(current * multiplier));
}

function allInCoinflip() {
    setBetAmountCoinflip(getCurrentBalanceCoinflip());
}

function updateFlipButton() {
    const bet = Number(betInput.value);
    const isValid = Number.isFinite(bet) && bet >= 1 && selectedChoice !== null;
    flipBtn.disabled = !isValid;
}

function handleFlip() {
    const bet = Number(betInput.value);
    localStorage.setItem('coinflip_bet', betInput.value);

    if (bet > getCurrentBalanceCoinflip()) {
        showResult('broke', null);
        return;
    }

    flipBtn.disabled = true;

    fetch("/api/coinflip/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({ bet: bet, choice: selectedChoice })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        flipBtn.disabled = false;

        if (data.error) {
            showResult('error', data.error);
            return;
        }

        balanceEl.textContent = formatMoney(data.balance);

        if (data.result === 1) {
            showResult('win', formatMoney(data.win));
        } else if (data.result === 0) {
            showResult('lose', null);
        } else {
            showResult('broke', null);
        }
    })
    .catch(function(err) {
        flipBtn.disabled = false;
        showResult('error', "Server error");
    });
}

function showResult(type, value) {
    resultCard.classList.add('show');
    resultCard.className = 'result-card show card-casino rounded-2xl p-6 text-center';

    switch(type) {
        case 'win':
            resultCard.classList.add('border-2', 'border-green-500');
            resultEmoji.textContent = '\uD83C\uDF89';
            resultText.textContent = 'WINNER!';
            resultText.className = 'font-casino text-2xl text-neon-green text-glow-green';
            resultSubtext.textContent = '+$' + value;
            resultSubtext.className = 'mt-2 text-gray-400';
            break;
        case 'lose':
            resultCard.classList.add('border-2', 'border-red-500');
            resultEmoji.textContent = '\uD83D\uDC80';
            resultText.textContent = 'YOU LOSE';
            resultText.className = 'font-casino text-2xl text-red-400';
            resultSubtext.textContent = 'Better luck next time';
            resultSubtext.className = 'mt-2 text-gray-500';
            break;
        case 'broke':
            resultCard.classList.add('border-2', 'border-yellow-500');
            resultEmoji.textContent = '\uD83D\uDCB8';
            resultText.textContent = 'TOO BROKE';
            resultText.className = 'font-casino text-2xl text-yellow-400';
            resultSubtext.textContent = 'Get more money first';
            resultSubtext.className = 'mt-2 text-gray-500';
            break;
        case 'error':
            resultCard.classList.add('border-2', 'border-red-500');
            resultEmoji.textContent = '\u26A0\uFE0F';
            resultText.textContent = 'ERROR';
            resultText.className = 'font-casino text-2xl text-red-400';
            resultSubtext.textContent = value;
            resultSubtext.className = 'mt-2 text-gray-500';
            break;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initCoinflip);
