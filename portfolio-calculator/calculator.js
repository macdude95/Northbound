// Portfolio Rebalancer Calculator

// Global state
let targetAllocations = {}; // ticker -> percentage
let currentHoldings = {}; // ticker -> dollar amount

// Initialize the calculator
document.addEventListener('DOMContentLoaded', function() {
    // Add initial input fields
    addManualInput();
    addHoldingInput();

    // Make inputs update calculations in real-time
    document.addEventListener('input', function(e) {
        if (e.target.matches('input[type="number"]')) {
            // Update global state when inputs change
            updateGlobalState();
        }
    });
});

function addManualInput() {
    const container = document.getElementById('manualInputs');
    const inputGroup = createAllocationInput();
    container.appendChild(inputGroup);
    updateGlobalState();
}

function addHoldingInput() {
    const container = document.getElementById('holdingsInputs');
    const inputGroup = createHoldingInput();
    container.appendChild(inputGroup);
    updateGlobalState();
}

function createAllocationInput(ticker = '', percentage = '') {
    const div = document.createElement('div');
    div.className = 'input-group';

    div.innerHTML = `
        <label>Ticker:</label>
        <input type="text" placeholder="SQQQ" value="${ticker}" onchange="updateGlobalState()">
        <label>%:</label>
        <input type="number" step="0.01" min="0" max="100" placeholder="0.00" value="${percentage}" onchange="updateGlobalState()">
        <button onclick="removeInput(this)">❌</button>
    `;

    return div;
}

function createHoldingInput(ticker = '', amount = '') {
    const div = document.createElement('div');
    div.className = 'input-group';

    div.innerHTML = `
        <label>$</label>
        <input type="number" step="0.01" min="0" placeholder="0.00" value="${amount}" onchange="updateGlobalState()">
        <label>in:</label>
        <input type="text" placeholder="SQQQ" value="${ticker}" onchange="updateGlobalState()">
        <button onclick="removeInput(this)">❌</button>
    `;

    return div;
}

function removeInput(button) {
    button.parentElement.remove();
    updateGlobalState();
}

function updateGlobalState() {
    // Update target allocations from manual inputs
    targetAllocations = {};
    const allocationGroups = document.querySelectorAll('#manualInputs .input-group');
    allocationGroups.forEach(group => {
        const inputs = group.querySelectorAll('input');
        const ticker = inputs[0].value.trim().toUpperCase();
        const percentage = parseFloat(inputs[1].value) || 0;

        if (ticker && percentage > 0) {
            targetAllocations[ticker] = percentage;
        }
    });

    // Update current holdings
    currentHoldings = {};
    const holdingGroups = document.querySelectorAll('#holdingsInputs .input-group');
    holdingGroups.forEach(group => {
        const inputs = group.querySelectorAll('input');
        const amount = parseFloat(inputs[0].value) || 0;
        const ticker = inputs[1].value.trim().toUpperCase();

        if (ticker && amount > 0) {
            currentHoldings[ticker] = amount;
        }
    });
}

function parseEmailBlock() {
    const emailText = document.getElementById('emailInput').value.trim();
    const statusDiv = document.getElementById('parseStatus');

    // Clear previous status
    statusDiv.className = 'parse-status';
    statusDiv.style.display = 'none';

    if (!emailText) {
        showParseStatus('Please paste allocation data from email first.', 'error');
        return;
    }

    // Parse lines like "SQQQ: 81.34%" or "SQQQ: 81.34"
    const lines = emailText.split('\n');
    const parsedAllocations = {};

    lines.forEach(line => {
        line = line.trim();
        if (!line) return;

        // Match patterns like "SQQQ: 81.34%" or "SQQQ: 81.34"
        const match = line.match(/^([A-Z]+):\s*([\d.]+)%?$/i);
        if (match) {
            const ticker = match[1].toUpperCase();
            const percentage = parseFloat(match[2]);
            if (percentage > 0 && percentage <= 100) {
                parsedAllocations[ticker] = percentage;
            }
        }
    });

    if (Object.keys(parsedAllocations).length === 0) {
        showParseStatus('No valid allocations found. Expected format: "TICKER: PERCENTAGE%"', 'error');
        return;
    }

    // Update manual inputs to reflect parsed data
    const container = document.getElementById('manualInputs');
    container.innerHTML = ''; // Clear existing

    Object.entries(parsedAllocations).forEach(([ticker, percentage]) => {
        const inputGroup = createAllocationInput(ticker, percentage.toFixed(2));
        container.appendChild(inputGroup);
    });

    // Update global state
    targetAllocations = parsedAllocations;

    // Show success message
    showParseStatus(`✅ Parsed ${Object.keys(parsedAllocations).length} allocations from email!`, 'success');
}

function showParseStatus(message, type) {
    const statusDiv = document.getElementById('parseStatus');
    statusDiv.textContent = message;
    statusDiv.className = `parse-status ${type}`;
    statusDiv.style.display = 'block';

    // Success messages stay visible (no auto-hide)
    // Error messages stay visible until user fixes and tries again
}

function calculateRebalancing() {
    updateGlobalState();

    // Validate inputs
    if (Object.keys(targetAllocations).length === 0) {
        alert('Please enter target allocations first.');
        return;
    }

    if (Object.keys(currentHoldings).length === 0) {
        alert('Please enter current holdings first.');
        return;
    }

    // Calculate total portfolio value
    const totalValue = Object.values(currentHoldings).reduce((sum, val) => sum + val, 0);

    if (totalValue <= 0) {
        alert('Total portfolio value must be greater than zero.');
        return;
    }

    // Calculate target values for each holding
    const targetValues = {};
    Object.entries(targetAllocations).forEach(([ticker, percentage]) => {
        targetValues[ticker] = totalValue * (percentage / 100);
    });

    // Calculate required trades
    const trades = {};
    let totalBuy = 0;
    let totalSell = 0;

    Object.keys(targetAllocations).forEach(ticker => {
        const currentValue = currentHoldings[ticker] || 0;
        const targetValue = targetValues[ticker] || 0;
        const difference = targetValue - currentValue;

        if (Math.abs(difference) >= 0.01) { // Only show meaningful trades
            trades[ticker] = difference;
            if (difference > 0) {
                totalBuy += difference;
            } else {
                totalSell += Math.abs(difference);
            }
        }
    });

    // Calculate final balances
    const finalBalances = {};
    Object.entries(targetAllocations).forEach(([ticker, percentage]) => {
        finalBalances[ticker] = targetValues[ticker];
    });

    // Display results
    displayResults(trades, finalBalances, totalValue);
}

function displayResults(trades, finalBalances, totalValue) {
    const resultsDiv = document.getElementById('results');
    const tradesDiv = document.getElementById('trades');
    const balancesDiv = document.getElementById('finalBalances');

    // Clear previous results
    tradesDiv.innerHTML = '<h3>📈 Required Trades</h3>';
    balancesDiv.innerHTML = '<h3>💰 Final Balances</h3>';

    // Display trades
    if (Object.keys(trades).length === 0) {
        tradesDiv.innerHTML += '<p class="success">✅ Portfolio is already balanced!</p>';
    } else {
        Object.entries(trades).forEach(([ticker, amount]) => {
            const tradeType = amount > 0 ? 'buy' : 'sell';
            const action = amount > 0 ? 'Buy' : 'Sell';
            const formattedAmount = Math.abs(amount).toLocaleString('en-US', {
                style: 'currency',
                currency: 'USD'
            });

            const tradeItem = document.createElement('div');
            tradeItem.className = `trade-item ${tradeType}`;
            tradeItem.innerHTML = `
                <strong>${action} ${ticker}</strong>
                <span class="amount ${amount > 0 ? 'positive' : 'negative'}">${formattedAmount}</span>
            `;
            tradesDiv.appendChild(tradeItem);
        });
    }

    // Display final balances
    Object.entries(finalBalances).forEach(([ticker, amount]) => {
        const percentage = targetAllocations[ticker];
        const formattedAmount = amount.toLocaleString('en-US', {
            style: 'currency',
            currency: 'USD'
        });

        const balanceItem = document.createElement('div');
        balanceItem.className = 'balance-item';
        balanceItem.innerHTML = `
            <strong>${ticker}</strong>
            <span class="percentage">${formattedAmount} (${percentage.toFixed(2)}%)</span>
        `;
        balancesDiv.appendChild(balanceItem);
    });

    // Add total
    const totalItem = document.createElement('div');
    totalItem.className = 'balance-item total-balance';
    totalItem.innerHTML = `
        <strong>Total Portfolio</strong>
        <span class="amount">${totalValue.toLocaleString('en-US', {style: 'currency', currency: 'USD'})}</span>
    `;
    balancesDiv.appendChild(totalItem);

    // Show results section
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

// Utility function to format currency
function formatCurrency(amount) {
    return amount.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD'
    });
}

// Utility function to format percentage
function formatPercentage(value) {
    return value.toFixed(2) + '%';
}
