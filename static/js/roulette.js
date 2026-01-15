/* Roulette Game Logic */

let ws = null;
let currentRound = null;
let timerInterval = null;
let roundEndTime = null;
let currentWheelRotation = 0;
let myUsername = "";

let myBets = { GRAY: 0, RED: 0, BLUE: 0, GOLD: 0 };
let totalBets = { GRAY: 0, RED: 0, BLUE: 0, GOLD: 0 };
let playerBets = { GRAY: {}, RED: {}, BLUE: {}, GOLD: {} };
let winHistory = [];

function initRoulette(username) {
    myUsername = username;
    drawWheel();
    connectWebSocket();

    // Format initial balance display
    const balanceEl = document.getElementById('balance');
    const initialBalance = parseFloat(balanceEl.textContent) || 0;
    balanceEl.textContent = formatMoney(initialBalance);

    // Restore last bet from localStorage
    const savedBet = localStorage.getItem('roulette_bet');
    if (savedBet) {
        const savedAmount = parseFloat(savedBet.replace(/,/g, '')) || 0;
        document.getElementById('bet-amount-input').value = savedAmount > 0 ? formatMoney(savedAmount) : '';
    }

    // Save bet amount when it changes and ensure integer with formatting
    document.getElementById('bet-amount-input').addEventListener('change', function() {
        const input = document.getElementById('bet-amount-input');
        const val = parseFloat(input.value.replace(/,/g, '')) || 0;
        input.value = val > 0 ? formatMoney(val) : '';
        localStorage.setItem('roulette_bet', val);
    });
}

function updateWinnerDisplay(color) {
    const display = document.getElementById('winner-display');
    const name = document.getElementById('winner-name');

    display.className = 'color-display ' + color.toLowerCase();
    name.textContent = color;
}

function addToHistory(color) {
    winHistory.unshift(color);
    if (winHistory.length > 10) {
        winHistory.pop();
    }

    const historyItems = document.getElementById('history-items');
    historyItems.innerHTML = '';

    winHistory.forEach(function(histColor) {
        const item = document.createElement('div');
        item.className = 'history-item ' + histColor.toLowerCase();
        item.textContent = histColor.charAt(0);
        historyItems.appendChild(item);
    });
}

function getCurrentBalance() {
    const balanceText = document.getElementById('balance').textContent.replace(/,/g, '');
    return parseFloat(balanceText) || 0;
}

function getBetAmount() {
    const betText = document.getElementById('bet-amount-input').value.replace(/,/g, '');
    return parseFloat(betText) || 0;
}

function setBetAmountRoulette(amount) {
    const input = document.getElementById('bet-amount-input');
    input.value = amount > 0 ? formatMoney(amount) : '';
}

function addToBetRoulette(amount) {
    const current = getBetAmount();
    setBetAmountRoulette(current + amount);
}

function multiplyBetRoulette(multiplier) {
    const current = getBetAmount();
    setBetAmountRoulette(Math.floor(current * multiplier));
}

function allInRoulette() {
    setBetAmountRoulette(getCurrentBalance());
}

function updateCurrentBetDisplay(color) {
    const element = document.getElementById('current-bet-' + color);
    const amount = myBets[color];
    if (amount > 0) {
        element.textContent = 'Your bet: $' + formatMoney(amount);
        element.classList.add('has-bet');
    } else {
        element.textContent = 'Your bet: -';
        element.classList.remove('has-bet');
    }
}

function updateTotalBetsDisplay(color) {
    const element = document.getElementById('total-bets-' + color);
    element.textContent = 'Total: $' + formatMoney(totalBets[color]);
}

function resetBetDisplays() {
    myBets = { GRAY: 0, RED: 0, BLUE: 0, GOLD: 0 };
    totalBets = { GRAY: 0, RED: 0, BLUE: 0, GOLD: 0 };
    ['GRAY', 'RED', 'BLUE', 'GOLD'].forEach(function(color) {
        updateCurrentBetDisplay(color);
        updateTotalBetsDisplay(color);
    });
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = protocol + '//' + window.location.host + '/ws/roulette/';

    ws = new WebSocket(wsUrl);

    ws.onopen = function(e) {
        console.log('WebSocket connected');
        ws.send(JSON.stringify({
            type: 'get_state'
        }));
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };

    ws.onclose = function(event) {
        console.log('WebSocket closed, reconnecting in 2s...');
        setTimeout(connectWebSocket, 2000);
    };
}

function handleWebSocketMessage(data) {
    console.log('Received:', data);

    switch(data.type) {
        case 'round_state':
            syncRoundState(data);
            break;

        case 'round_starting':
            startNewRound(data.round_number, data.time_remaining, data.history, data.bets);
            break;

        case 'bet_placed':
            addBetToLiveFeed(data);
            break;

        case 'round_spinning':
            enterSpinningPhase(data.winning_slot, data.winning_color);
            break;

        case 'round_result':
            displayResult(data);
            break;

        case 'balance_update':
            updateBalance(data.balance);
            break;

        case 'error':
            alert('Error: ' + data.message);
            break;
    }
}

function syncRoundState(data) {
    currentRound = data.round_number;
    document.getElementById('round-number').textContent = data.round_number;

    if (data.history && data.history.length > 0) {
        loadHistoryFromServer(data.history);
    }

    clearLiveBets();
    resetBetDisplays();

    if (data.bets && data.bets.length > 0) {
        loadBetsFromServer(data.bets);
    }

    if (data.status === 'SPINNING') {
        disableBetting();
        document.getElementById('timer').textContent = 'SPIN!';
        document.getElementById('result-display').textContent = '';
        document.getElementById('result-display').className = 'result-display';
    } else if (data.status === 'BETTING') {
        enableBetting();
        document.getElementById('result-display').textContent = '';
        document.getElementById('result-display').className = 'result-display';
        startTimer(data.time_remaining);
    }
}

function startNewRound(roundNumber, timeRemaining, history, bets) {
    currentRound = roundNumber;
    document.getElementById('round-number').textContent = roundNumber;

    if (history && history.length > 0) {
        loadHistoryFromServer(history);
    }

    clearLiveBets();
    resetBetDisplays();
    document.getElementById('result-display').textContent = '';
    document.getElementById('result-display').className = 'result-display';
    enableBetting();

    if (bets && bets.length > 0) {
        loadBetsFromServer(bets);
    }

    startTimer(timeRemaining);
}

function loadHistoryFromServer(history) {
    if (winHistory.length === 0 && history.length > 0) {
        winHistory = history.slice(0, 10);
        updateWinnerDisplay(winHistory[0]);

        const historyItems = document.getElementById('history-items');
        historyItems.innerHTML = '';

        winHistory.forEach(function(color) {
            const item = document.createElement('div');
            item.className = 'history-item ' + color.toLowerCase();
            item.textContent = color.charAt(0);
            historyItems.appendChild(item);
        });
    }
}

function loadBetsFromServer(bets) {
    bets.forEach(function(bet) {
        const color = bet.color;
        const username = bet.username;
        const amount = bet.amount;
        const isOwnBet = username === myUsername;

        totalBets[color] += amount;
        updateTotalBetsDisplay(color);

        if (isOwnBet) {
            myBets[color] += amount;
            updateCurrentBetDisplay(color);
        }

        if (!playerBets[color][username]) {
            playerBets[color][username] = 0;
        }
        playerBets[color][username] += amount;
    });

    ['GRAY', 'RED', 'BLUE', 'GOLD'].forEach(function(color) {
        if (Object.keys(playerBets[color]).length > 0) {
            rebuildBetsList(color);
        }
    });
}

function enterSpinningPhase(winningSlot, winningColor) {
    disableBetting();

    if (timerInterval) {
        clearInterval(timerInterval);
    }
    document.getElementById('timer').textContent = 'SPIN!';

    document.getElementById('winner-display').className = 'color-display none';
    document.getElementById('winner-name').textContent = '?';

    spinWheelToSlot(winningSlot);
}

function spinWheelToSlot(winningSlot) {
    const wheel = document.getElementById('wheel');
    const degreesPerSlot = 360 / 54;
    const slotCenterAngle = winningSlot * degreesPerSlot + (degreesPerSlot / 2);

    let targetOffset = 270 - slotCenterAngle;
    if (targetOffset < 0) targetOffset += 360;

    const minSpins = 5;
    const minFinalRotation = currentWheelRotation + minSpins * 360;
    const k = Math.ceil((minFinalRotation - targetOffset) / 360);
    const finalRotation = targetOffset + k * 360;

    const animation = wheel.animate([
        { transform: 'translateZ(0) rotate(' + currentWheelRotation + 'deg)' },
        { transform: 'translateZ(0) rotate(' + finalRotation + 'deg)' }
    ], {
        duration: 3000,
        easing: 'cubic-bezier(0.17, 0.67, 0.12, 0.99)',
        fill: 'forwards'
    });

    animation.onfinish = function() {
        wheel.style.transform = 'translateZ(0) rotate(' + finalRotation + 'deg)';
        animation.cancel();
    };

    currentWheelRotation = finalRotation;
}

function displayResult(data) {
    const resultDiv = document.getElementById('result-display');
    const colorName = data.winning_color;
    const yourPayout = data.your_payout;

    updateBalance(data.your_balance);
    updateWinnerDisplay(colorName);
    addToHistory(colorName);

    if (yourPayout > 0) {
        resultDiv.textContent = colorName + ' WINS! You won $' + formatMoney(yourPayout) + '!';
        resultDiv.className = 'result-display winner';
    } else {
        resultDiv.textContent = colorName + ' wins.';
        resultDiv.className = 'result-display loser';
    }
}

function placeBet(color) {
    const amount = getBetAmount();

    if (!amount || amount <= 0) {
        alert('Please enter a bet amount first');
        return;
    }

    if (amount > getCurrentBalance()) {
        alert('Insufficient balance');
        return;
    }

    localStorage.setItem('roulette_bet', amount);

    ws.send(JSON.stringify({
        type: 'place_bet',
        color: color,
        amount: amount
    }));
}

function addBetToLiveFeed(data) {
    const color = data.color;
    const list = document.getElementById('bets-list-' + color);
    const username = data.username;
    const isOwnBet = username === myUsername;

    const emptyMsg = list.querySelector('.tile-bets-empty');
    if (emptyMsg) {
        emptyMsg.remove();
    }

    totalBets[color] += data.amount;
    updateTotalBetsDisplay(color);

    if (isOwnBet) {
        myBets[color] += data.amount;
        updateCurrentBetDisplay(color);
    }

    if (!playerBets[color][username]) {
        playerBets[color][username] = 0;
    }
    playerBets[color][username] += data.amount;

    rebuildBetsList(color);
}

function rebuildBetsList(color) {
    const list = document.getElementById('bets-list-' + color);

    const sortedPlayers = Object.entries(playerBets[color])
        .sort(function(a, b) { return b[1] - a[1]; });

    list.innerHTML = '';

    if (sortedPlayers.length === 0) {
        list.innerHTML = '<div class="tile-bets-empty">No bets yet</div>';
        return;
    }

    sortedPlayers.forEach(function(entry) {
        const username = entry[0];
        const amount = entry[1];
        const isOwnBet = username === myUsername;
        const betItem = document.createElement('div');
        betItem.className = 'tile-bet-item' + (isOwnBet ? ' own-bet' : '');
        betItem.setAttribute('data-username', username);
        betItem.innerHTML = '<strong>' + username + '</strong>: $' + formatMoney(amount);
        list.appendChild(betItem);
    });
}

function clearLiveBets() {
    ['GRAY', 'RED', 'BLUE', 'GOLD'].forEach(function(color) {
        const list = document.getElementById('bets-list-' + color);
        list.innerHTML = '<div class="tile-bets-empty">No bets yet</div>';
        playerBets[color] = {};
    });
}

function updateBalance(newBalance) {
    document.getElementById('balance').textContent = formatMoney(newBalance);
}

function enableBetting() {
    document.querySelectorAll('.color-bet-tile').forEach(function(tile) {
        tile.classList.remove('disabled');
    });
    document.querySelectorAll('.bet-button').forEach(function(btn) {
        btn.disabled = false;
    });
}

function disableBetting() {
    document.querySelectorAll('.color-bet-tile').forEach(function(tile) {
        tile.classList.add('disabled');
    });
    document.querySelectorAll('.bet-button').forEach(function(btn) {
        btn.disabled = true;
    });
}

function startTimer(seconds) {
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    roundEndTime = Date.now() + (seconds * 1000);

    function updateTimer() {
        const remaining = Math.max(0, (roundEndTime - Date.now()) / 1000);
        document.getElementById('timer').textContent = remaining.toFixed(2) + 's';

        if (remaining <= 0) {
            clearInterval(timerInterval);
            document.getElementById('timer').textContent = '0.00s';
        }
    }

    updateTimer();
    timerInterval = setInterval(updateTimer, 10);
}

function drawWheel() {
    const canvas = document.getElementById('wheel-canvas');
    const ctx = canvas.getContext('2d');
    const centerX = 200;
    const centerY = 200;
    const outerRadius = 190;
    const innerRadius = 120;

    const colors = {
        'GOLD': '#ffd700',
        'BLUE': '#3b82f6',
        'GRAY': '#6b7280',
        'RED': '#ef4444'
    };

    const wheel = [
        'GOLD', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
        'BLUE', 'GRAY', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
        'BLUE', 'GRAY', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
        'BLUE', 'GRAY', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
        'BLUE', 'GRAY', 'BLUE', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY', 'RED', 'GRAY',
        'BLUE'
    ];

    const anglePerSegment = (2 * Math.PI) / 54;
    wheel.forEach(function(colorName, i) {
        const startAngle = i * anglePerSegment;
        const endAngle = startAngle + anglePerSegment;

        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
        ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
        ctx.closePath();
        ctx.fillStyle = colors[colorName];
        ctx.fill();
        ctx.strokeStyle = '#111827';
        ctx.lineWidth = 1;
        ctx.stroke();
    });

    ctx.beginPath();
    ctx.arc(centerX, centerY, innerRadius, 0, 2 * Math.PI);
    ctx.fillStyle = '#111827';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(centerX, centerY, 45, 0, 2 * Math.PI);
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 45);
    gradient.addColorStop(0, '#374151');
    gradient.addColorStop(1, '#1f2937');
    ctx.fillStyle = gradient;
    ctx.fill();
    ctx.strokeStyle = '#4b5563';
    ctx.lineWidth = 3;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(centerX, centerY, 20, 0, 2 * Math.PI);
    ctx.fillStyle = '#9333ea';
    ctx.fill();
    ctx.strokeStyle = '#a855f7';
    ctx.lineWidth = 2;
    ctx.stroke();
}
