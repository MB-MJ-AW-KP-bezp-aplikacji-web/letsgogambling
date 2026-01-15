/* Slots Game Logic */

const csrftoken = getCookie('csrftoken');

const balanceEl = document.getElementById("balance");
const messageEl = document.getElementById("message");
const machinesContainer = document.getElementById("machines-container");
const spinBtn = document.getElementById("spin-btn");
const betInput = document.getElementById("bet-amount");
const totalBetEl = document.getElementById("total-bet");
let isSpinning = false;
let machineCount = 1;

function createMachineHTML(index) {
    return '\
        <div class="machine-wrapper">\
            <div class="slot-machine" id="slot-machine-' + index + '">\
                <table class="border-separate border-spacing-1">\
                    <tbody>\
                        <tr>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                        </tr>\
                        <tr>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                        </tr>\
                        <tr>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                            <td class="slot-cell rounded-lg">\u2753</td>\
                        </tr>\
                    </tbody>\
                </table>\
            </div>\
            <div class="machine-result" id="result-' + index + '"></div>\
        </div>\
    ';
}

function renderMachines() {
    machinesContainer.innerHTML = '';
    for (let i = 0; i < machineCount; i++) {
        machinesContainer.innerHTML += createMachineHTML(i);
    }
    updateTotalBet();
}

function updateTotalBet() {
    const bet = Number(betInput.value) || 0;
    totalBetEl.textContent = '$' + formatMoney(bet * machineCount);
}

function initSlots() {
    // Machine count selector
    document.querySelectorAll('.machine-count-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (isSpinning) return;
            document.querySelectorAll('.machine-count-btn').forEach(function(b) {
                b.classList.remove('selected');
            });
            btn.classList.add('selected');
            machineCount = parseInt(btn.dataset.count);
            renderMachines();
        });
    });

    // Bet control buttons via data attributes
    document.querySelectorAll('[data-bet-set]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            setBetAmountSlots(parseFloat(btn.dataset.betSet));
        });
    });
    document.querySelectorAll('[data-bet-add]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            addToBetSlots(parseFloat(btn.dataset.betAdd));
        });
    });
    document.querySelectorAll('[data-bet-multiply]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            multiplyBetSlots(parseFloat(btn.dataset.betMultiply));
        });
    });
    document.querySelectorAll('[data-bet-allin]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            allInSlots();
        });
    });

    // Restore last bet from localStorage
    const savedBet = localStorage.getItem('slots_bet');
    if (savedBet) {
        betInput.value = savedBet;
    }

    // Save bet amount when it changes and ensure integer
    betInput.addEventListener('change', function() {
        const val = parseFloat(betInput.value) || 0;
        betInput.value = val > 0 ? Math.floor(val) : '';
        localStorage.setItem('slots_bet', betInput.value);
        updateTotalBet();
    });

    betInput.addEventListener('input', updateTotalBet);

    // Fetch initial balance
    fetch("/api/balance/")
        .then(function(res) { return res.json(); })
        .then(function(data) {
            balanceEl.textContent = formatMoney(data.balance);
        });

    // Initialize machines
    renderMachines();

    // Spin button handler
    spinBtn.addEventListener("click", handleSpin);
}

function getCurrentBalanceSlots() {
    const balanceText = balanceEl.textContent.replace(/,/g, '');
    return parseFloat(balanceText) || 0;
}

function setBetAmountSlots(amount) {
    betInput.value = amount > 0 ? Math.floor(amount) : '';
    localStorage.setItem('slots_bet', betInput.value);
    updateTotalBet();
}

function addToBetSlots(amount) {
    const current = parseFloat(betInput.value) || 0;
    setBetAmountSlots(current + amount);
}

function multiplyBetSlots(multiplier) {
    const current = parseFloat(betInput.value) || 0;
    setBetAmountSlots(Math.floor(current * multiplier));
}

function allInSlots() {
    setBetAmountSlots(Math.floor(getCurrentBalanceSlots() / machineCount));
}

async function handleSpin() {
    if (isSpinning) return;

    const bet = Number(betInput.value);
    localStorage.setItem('slots_bet', betInput.value);
    const totalBet = bet * machineCount;

    if (!Number.isFinite(bet) || bet < 1) {
        messageEl.textContent = "Invalid bet amount.";
        messageEl.className = "text-center text-xl font-casino mb-4 h-8 text-red-400";
        return;
    }

    if (totalBet > getCurrentBalanceSlots()) {
        messageEl.textContent = "TOO BROKE!";
        messageEl.className = "text-center text-xl font-casino mb-4 h-8 text-red-400";
        return;
    }

    isSpinning = true;
    spinBtn.disabled = true;
    messageEl.textContent = "";

    // Start spinning all machines
    for (let i = 0; i < machineCount; i++) {
        const machine = document.getElementById('slot-machine-' + i);
        machine.classList.add("spinning");
        machine.classList.remove("winner", "loser");
        document.getElementById('result-' + i).textContent = "";
        document.getElementById('result-' + i).className = "machine-result";
    }

    try {
        const response = await fetch("/api/spin/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
            body: JSON.stringify({ bet: bet, count: machineCount })
        });
        const data = await response.json();

        setTimeout(function() {
            if (data.error) {
                for (let i = 0; i < machineCount; i++) {
                    const machine = document.getElementById('slot-machine-' + i);
                    machine.classList.remove("spinning");
                }
                messageEl.textContent = data.error;
                messageEl.className = "text-center text-xl font-casino mb-4 h-8 text-red-400";
                isSpinning = false;
                spinBtn.disabled = false;
                return;
            }

            data.results.forEach(function(result, i) {
                const machine = document.getElementById('slot-machine-' + i);
                const resultEl = document.getElementById('result-' + i);
                machine.classList.remove("spinning");

                const rows = machine.querySelectorAll("tr");
                result.machine.forEach(function(row, ri) {
                    row.forEach(function(sym, ci) {
                        const cell = rows[ri].children[ci];
                        cell.textContent = sym;
                        if (result.strikes[ri][ci]) {
                            cell.classList.add("strike");
                        } else {
                            cell.classList.remove("strike");
                        }
                    });
                });

                if (result.win > 0) {
                    machine.classList.add("winner");
                    resultEl.textContent = '+$' + formatMoney(result.win);
                    resultEl.className = "machine-result win";
                } else {
                    machine.classList.add("loser");
                    resultEl.textContent = "NO WIN";
                    resultEl.className = "machine-result lose";
                }
            });

            balanceEl.textContent = formatMoney(data.balance);

            if (data.total_win > 0) {
                messageEl.textContent = 'TOTAL WIN: +$' + formatMoney(data.total_win);
                messageEl.className = "text-center text-xl font-casino mb-4 h-8 text-neon-green text-glow-green";
            } else {
                messageEl.textContent = "NO WINS";
                messageEl.className = "text-center text-xl font-casino mb-4 h-8 text-gray-500";
            }

            isSpinning = false;
            spinBtn.disabled = false;
        }, 500);

    } catch (err) {
        for (let i = 0; i < machineCount; i++) {
            document.getElementById('slot-machine-' + i).classList.remove("spinning");
        }
        isSpinning = false;
        spinBtn.disabled = false;
        messageEl.textContent = "Server Error";
        messageEl.className = "text-center text-xl font-casino mb-4 h-8 text-red-400";
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initSlots);
