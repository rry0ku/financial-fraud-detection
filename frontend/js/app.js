/**
 * FRAUD SHIELD SURVEILLANCE & THREAT DEFENSE CONTROLLER v2.5
 */

// Global State
let currentCurrency = 'USD';
const CURRENCY_RATES = {
    USD: { symbol: '$', rate: 1.0 },
    INR: { symbol: '₹', rate: 83.2 },
    EUR: { symbol: '€', rate: 0.92 },
    GBP: { symbol: '£', rate: 0.79 }
};

let decisionChart = null;
let riskDistChart = null;
let shapChart = null;
let cyInstance = null;
let liveStreamSocket = null;
let isStreaming = false;
let currentTransactionId = null;
let streamTxCount = 0;
let streamStartTime = null;
let allAuditTransactions = [];
let selectedRedTeamCampaign = 'MICRO_SMURFING';
let threatMap = null;

// ==========================================
// 1. INITIALIZATION & TAB CONTROLS
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchAnalytics();
    fetchAuditLog();
    initShapChart();
    initThreatMap();

    const form = document.getElementById('txnForm');
    if (form) {
        form.addEventListener('submit', handleSinglePrediction);
    }

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterAuditLogTable);
    }

    const filterDecision = document.getElementById('filterDecision');
    if (filterDecision) {
        filterDecision.addEventListener('change', filterAuditLogTable);
    }

    if (window.lucide) {
        lucide.createIcons();
    }
});

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.nav-tab-pill').forEach(btn => {
        btn.classList.remove('active');
    });

    const activeContent = document.getElementById(`tab-${tabId}`);
    const activeBtn = document.getElementById(`tabBtn-${tabId}`);

    if (activeContent) activeContent.classList.remove('hidden');
    if (activeBtn) activeBtn.classList.add('active');

    if (tabId === 'threatmap') {
        if (threatMap) threatMap.resize();
    } else if (tabId === 'graph') {
        loadGraphData();
        setTimeout(() => {
            if (cyInstance) {
                cyInstance.resize();
                cyInstance.fit();
            }
        }, 100);
    } else if (tabId === 'rules') {
        loadPolicyRules();
    } else if (tabId === 'hitl') {
        loadHitlQueue();
    } else if (tabId === 'drift') {
        loadDriftReport();
    }

    if (window.lucide) lucide.createIcons();
}

// ==========================================
// 2. TOAST NOTIFICATIONS
// ==========================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'cyber-toast';

    let iconHtml = '<i data-lucide="info" class="w-4 h-4 text-indigo-400"></i>';
    if (type === 'success') {
        iconHtml = '<i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-400"></i>';
    } else if (type === 'error') {
        iconHtml = '<i data-lucide="shield-alert" class="w-4 h-4 text-rose-400"></i>';
    } else if (type === 'warning') {
        iconHtml = '<i data-lucide="alert-triangle" class="w-4 h-4 text-amber-400"></i>';
    }

    toast.innerHTML = `${iconHtml}<span>${message}</span>`;
    container.appendChild(toast);

    if (window.lucide) lucide.createIcons();

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 250);
    }, 2800);
}

// ==========================================
// 3. CURRENCY SWITCHER
// ==========================================
function onCurrencyChange(curr) {
    currentCurrency = curr;
    const symbol = CURRENCY_RATES[curr].symbol;
    document.querySelectorAll('.currencySymbolDisplay').forEach(el => el.textContent = symbol);
    fetchAnalytics();
    renderAuditTable(allAuditTransactions);
    showToast(`Currency set to ${curr} (${symbol})`, 'info');
}

function formatCurrency(amountUSD) {
    const config = CURRENCY_RATES[currentCurrency] || CURRENCY_RATES.USD;
    const converted = amountUSD * config.rate;
    return `${config.symbol}${converted.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// ==========================================
// 4. TRANSACTION SIMULATOR & PRESETS
// ==========================================
function loadPreset(presetKey) {
    if (presetKey === 'coffee') {
        document.getElementById('formType').value = 'PAYMENT';
        document.getElementById('formAmount').value = '4.50';
        document.getElementById('formOldOrig').value = '450.00';
        document.getElementById('formNewOrig').value = '445.50';
        document.getElementById('formOldDest').value = '2500.00';
        document.getElementById('formNewDest').value = '2504.50';
        document.getElementById('formHour').value = '10';
        document.getElementById('formOrigId').value = 'C11928471';
        document.getElementById('formDestId').value = 'M99281742';
        document.getElementById('formCity').value = 'New York, US';
        document.getElementById('formIp').value = '192.168.1.101';
        showToast('Loaded Card-Present POS Payment scenario', 'info');
    } else if (presetKey === 'salary') {
        document.getElementById('formType').value = 'CASH_IN';
        document.getElementById('formAmount').value = '3200.00';
        document.getElementById('formOldOrig').value = '1200.00';
        document.getElementById('formNewOrig').value = '4400.00';
        document.getElementById('formOldDest').value = '0.00';
        document.getElementById('formNewDest').value = '0.00';
        document.getElementById('formHour').value = '14';
        document.getElementById('formOrigId').value = 'C44819201';
        document.getElementById('formDestId').value = 'C00918231';
        document.getElementById('formCity').value = 'London, UK';
        document.getElementById('formIp').value = '81.2.69.142';
        showToast('Loaded Direct Deposit Salary scenario', 'info');
    } else if (presetKey === 'travel') {
        document.getElementById('formType').value = 'TRANSFER';
        document.getElementById('formAmount').value = '18000.00';
        document.getElementById('formOldOrig').value = '25000.00';
        document.getElementById('formNewOrig').value = '7000.00';
        document.getElementById('formOldDest').value = '500.00';
        document.getElementById('formNewDest').value = '18500.00';
        document.getElementById('formHour').value = '16';
        document.getElementById('formOrigId').value = 'C11928471';
        document.getElementById('formDestId').value = 'C77291044';
        document.getElementById('formCity').value = 'Tokyo, JP';
        document.getElementById('formIp').value = '133.242.18.9';
        showToast('Loaded Impossible Travel Velocity anomaly', 'warning');
    } else if (presetKey === 'drain') {
        document.getElementById('formType').value = 'TRANSFER';
        document.getElementById('formAmount').value = '95000.00';
        document.getElementById('formOldOrig').value = '95000.00';
        document.getElementById('formNewOrig').value = '0.00';
        document.getElementById('formOldDest').value = '0.00';
        document.getElementById('formNewDest').value = '0.00';
        document.getElementById('formHour').value = '3';
        document.getElementById('formOrigId').value = 'C88219472';
        document.getElementById('formDestId').value = 'C19028471';
        document.getElementById('formCity').value = 'Mumbai, IN';
        document.getElementById('formIp').value = '103.21.124.5';
        showToast('Loaded Nocturnal Account Drain scenario', 'error');
    }
}

async function handleSinglePrediction(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>Scoring AI Vectors & Rules...</span>`;

    const payload = {
        step: parseInt(document.getElementById('formHour').value) || 12,
        type: document.getElementById('formType').value,
        amount: parseFloat(document.getElementById('formAmount').value),
        name_orig: document.getElementById('formOrigId').value,
        oldbalance_orig: parseFloat(document.getElementById('formOldOrig').value),
        newbalance_orig: parseFloat(document.getElementById('formNewOrig').value),
        name_dest: document.getElementById('formDestId').value,
        oldbalance_dest: parseFloat(document.getElementById('formOldDest').value),
        newbalance_dest: parseFloat(document.getElementById('formNewDest').value),
        location_city: document.getElementById('formCity').value,
        ip_address: document.getElementById('formIp').value
    };

    try {
        const res = await fetch('/api/v1/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Prediction API error');
        const data = await res.json();

        currentTransactionId = data.transaction_id;
        displayEvaluationResult(data);
        fetchAnalytics();
        fetchAuditLog();

        // Project on threat map
        if (threatMap) {
            threatMap.addTransactionArc(payload.location_city, 'Frankfurt, DE', data.risk_score, data.decision === 'BLOCK');
        }

        if (data.decision === 'BLOCK') {
            showToast(`Threat Intercepted: Transaction ${data.transaction_id} BLOCKED`, 'error');
        } else if (data.decision === 'FLAG') {
            showToast(`Step-Up Verification Required: ${data.transaction_id}`, 'warning');
        } else {
            showToast(`Transaction ${data.transaction_id} Approved`, 'success');
        }

    } catch (err) {
        showToast(`Evaluation error: ${err.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i data-lucide="zap" class="w-4 h-4"></i><span>Evaluate AI Risk & Score Transaction</span>`;
        if (window.lucide) lucide.createIcons();
    }
}

function displayEvaluationResult(data) {
    const resultBox = document.getElementById('resultBox');
    resultBox.classList.remove('hidden');

    document.getElementById('resultTxnId').textContent = data.transaction_id;
    document.getElementById('riskPercentageText').textContent = data.risk_percentage;

    const riskScore = data.risk_score;
    const bar = document.getElementById('riskBarFill');
    bar.style.width = `${Math.min(100, Math.max(4, riskScore * 100))}%`;

    const badge = document.getElementById('decisionBadge');
    badge.textContent = data.decision;

    if (data.decision === 'BLOCK') {
        badge.className = 'verdict-pill verdict-block';
        bar.className = 'h-full rounded-full transition-all duration-500 bg-rose-500';
    } else if (data.decision === 'FLAG') {
        badge.className = 'verdict-pill verdict-flag';
        bar.className = 'h-full rounded-full transition-all duration-500 bg-amber-400';
    } else {
        badge.className = 'verdict-pill verdict-approve';
        bar.className = 'h-full rounded-full transition-all duration-500 bg-emerald-500';
    }

    // Render Telemetry Badges
    const reasonsContainer = document.getElementById('reasonsList');
    reasonsContainer.innerHTML = '';
    
    if (data.impossible_travel_flag) {
        const rEl = document.createElement('span');
        rEl.className = 'px-2.5 py-0.5 rounded text-[10.5px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 font-mono';
        rEl.textContent = `🚨 Impossible Travel (${data.geo_velocity_kmh} km/h)`;
        reasonsContainer.appendChild(rEl);
    }

    if (data.mule_cycle_detected) {
        const rEl = document.createElement('span');
        rEl.className = 'px-2.5 py-0.5 rounded text-[10.5px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 font-mono';
        rEl.textContent = `🕸️ Circular Money Mule Loop`;
        reasonsContainer.appendChild(rEl);
    }

    (data.flag_reasons || []).forEach(r => {
        const rEl = document.createElement('span');
        rEl.className = 'px-2.5 py-0.5 rounded text-[10.5px] font-medium bg-[#06070a] text-slate-300 border border-[#1a1f2c] font-mono';
        rEl.textContent = r;
        reasonsContainer.appendChild(rEl);
    });

    updateShapChart(data.shap_values || []);
}

// ==========================================
// 5. GLOBAL CYBER THREAT ATTACK MAP ENGINE
// ==========================================
class GlobalThreatMap {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.arcs = [];
        this.dpr = window.devicePixelRatio || 1;
        this.nodes = {
            'New York, US': { x: 0.28, y: 0.36, label: 'New York' },
            'London, UK': { x: 0.48, y: 0.28, label: 'London' },
            'Frankfurt, DE': { x: 0.52, y: 0.30, label: 'Frankfurt' },
            'Zurich, CH': { x: 0.50, y: 0.34, label: 'Zurich' },
            'Dubai, AE': { x: 0.58, y: 0.42, label: 'Dubai' },
            'Tokyo, JP': { x: 0.85, y: 0.38, label: 'Tokyo' },
            'Mumbai, IN': { x: 0.67, y: 0.48, label: 'Mumbai' },
            'Singapore, SG': { x: 0.76, y: 0.58, label: 'Singapore' },
            'Sydney, AU': { x: 0.88, y: 0.78, label: 'Sydney' },
            'São Paulo, BR': { x: 0.35, y: 0.70, label: 'São Paulo' }
        };

        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.animate = this.animate.bind(this);
        requestAnimationFrame(this.animate);
    }

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.width = rect.width;
        this.height = rect.height;
        this.dpr = window.devicePixelRatio || 1;
        this.canvas.width = this.width * this.dpr;
        this.canvas.height = this.height * this.dpr;
        this.canvas.style.width = `${this.width}px`;
        this.canvas.style.height = `${this.height}px`;
        this.ctx.scale(this.dpr, this.dpr);
    }

    _findNode(locStr) {
        if (!locStr) return this.nodes['New York, US'];
        const lower = String(locStr).toLowerCase();
        for (const [key, node] of Object.entries(this.nodes)) {
            if (lower.includes(node.label.toLowerCase()) || lower.includes(key.toLowerCase())) {
                return node;
            }
        }
        return this.nodes['New York, US'];
    }

    addTransactionArc(origin, dest, riskScore, isBlocked) {
        const origNode = this._findNode(origin);
        let destNode = this._findNode(dest);
        
        // Ensure origin and destination differ
        if (origNode.label === destNode.label) {
            const keys = Object.keys(this.nodes);
            const altKey = keys.find(k => this.nodes[k].label !== origNode.label) || 'Frankfurt, DE';
            destNode = this.nodes[altKey];
        }

        this.arcs.push({
            startX: origNode.x * this.width,
            startY: origNode.y * this.height,
            endX: destNode.x * this.width,
            endY: destNode.y * this.height,
            progress: 0.0,
            color: isBlocked ? '#f43f5e' : (riskScore > 0.3 ? '#fbbf24' : '#10b981'),
            isBlocked: isBlocked,
            originLabel: origNode.label,
            destLabel: destNode.label
        });

        if (this.arcs.length > 25) this.arcs.shift();

        // Prepend to live threat intercept feed
        const feed = document.getElementById('mapInterceptFeed');
        if (feed && (isBlocked || riskScore > 0.35)) {
            const item = document.createElement('div');
            item.className = `p-2.5 rounded bg-[#080a0f] border ${isBlocked ? 'border-rose-500/40' : 'border-amber-500/40'} font-mono text-[10.5px]`;
            item.innerHTML = `
                <span class="${isBlocked ? 'text-rose-400' : 'text-amber-400'} font-bold block">${isBlocked ? '🚨 INTERCEPTED ATTACK' : '⚠️ STEP-UP VERIFICATION'}</span>
                <span class="text-slate-300 block mt-0.5">${origNode.label.toUpperCase()} &rarr; ${destNode.label.toUpperCase()}</span>
                <span class="text-[9.5px] text-slate-500 block">Risk Score: ${(riskScore * 100).toFixed(1)}%</span>
            `;
            feed.insertBefore(item, feed.firstChild);
            if (feed.children.length > 8) feed.removeChild(feed.lastChild);
        }
    }

    animate() {
        if (!this.ctx || !this.canvas) return;
        const w = this.width;
        const h = this.height;

        this.ctx.save();
        this.ctx.fillStyle = '#040609';
        this.ctx.fillRect(0, 0, w, h);

        // Draw tactical radar grid lines
        this.ctx.strokeStyle = '#0e131d';
        this.ctx.lineWidth = 1;
        for (let x = 0; x < w; x += 40) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, h);
            this.ctx.stroke();
        }
        for (let y = 0; y < h; y += 40) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(w, y);
            this.ctx.stroke();
        }

        // Draw Global Financial Hubs
        for (const [key, node] of Object.entries(this.nodes)) {
            const nx = node.x * w;
            const ny = node.y * h;

            this.ctx.fillStyle = 'rgba(99, 102, 241, 0.15)';
            this.ctx.beginPath();
            this.ctx.arc(nx, ny, 8, 0, Math.PI * 2);
            this.ctx.fill();

            this.ctx.fillStyle = '#818cf8';
            this.ctx.beginPath();
            this.ctx.arc(nx, ny, 3.5, 0, Math.PI * 2);
            this.ctx.fill();

            this.ctx.fillStyle = '#94a3b8';
            this.ctx.font = '9.5px JetBrains Mono';
            this.ctx.fillText(node.label, nx + 7, ny + 3);
        }

        // Draw Flying Laser Arcs
        for (let i = this.arcs.length - 1; i >= 0; i--) {
            const arc = this.arcs[i];
            arc.progress += 0.022;

            const midX = (arc.startX + arc.endX) / 2;
            const midY = Math.min(arc.startY, arc.endY) - 45;

            this.ctx.strokeStyle = arc.color;
            this.ctx.lineWidth = arc.isBlocked ? 2.5 : 1.5;
            this.ctx.beginPath();
            this.ctx.moveTo(arc.startX, arc.startY);
            this.ctx.quadraticCurveTo(midX, midY, arc.endX, arc.endY);
            this.ctx.stroke();

            // Head Particle
            const t = Math.min(1.0, arc.progress);
            const px = (1 - t) * (1 - t) * arc.startX + 2 * (1 - t) * t * midX + t * t * arc.endX;
            const py = (1 - t) * (1 - t) * arc.startY + 2 * (1 - t) * t * midY + t * t * arc.endY;

            this.ctx.fillStyle = '#ffffff';
            this.ctx.beginPath();
            this.ctx.arc(px, py, arc.isBlocked ? 3.5 : 2.5, 0, Math.PI * 2);
            this.ctx.fill();

            if (arc.progress >= 1.0) {
                this.arcs.splice(i, 1);
            }
        }

        this.ctx.restore();
        requestAnimationFrame(this.animate);
    }
}

function initThreatMap() {
    threatMap = new GlobalThreatMap('threatMapCanvas');
}

// ==========================================
// 6. RED TEAM ADVERSARIAL ATTACK SIMULATOR
// ==========================================
function selectRedTeamCampaign(type) {
    selectedRedTeamCampaign = type;
    document.querySelectorAll('[id^="rtCard-"]').forEach(el => {
        el.className = 'scenario-card p-4';
    });
    const active = document.getElementById(`rtCard-${type}`);
    if (active) {
        active.className = 'scenario-card p-4 border-indigo-500/50 bg-[#0e1118]';
    }
}

async function launchRedTeamAttack() {
    const btn = document.getElementById('launchRtBtn');
    const intensity = parseInt(document.getElementById('rtIntensity').value) || 50;
    const terminal = document.getElementById('rtTerminalLogs');

    btn.disabled = true;
    btn.innerHTML = `<span>Firing Adversarial Attack Swarm...</span>`;
    terminal.innerHTML = `<p class="text-indigo-400">[*] Launching offensive simulation campaign [${selectedRedTeamCampaign}] with ${intensity} payloads...</p>`;

    try {
        const res = await fetch('/api/v1/redteam/launch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                campaign_type: selectedRedTeamCampaign,
                intensity: intensity
            })
        });

        if (!res.ok) throw new Error('Simulation failed');
        const data = await res.json();

        // Render animated terminal logs
        terminal.innerHTML = '';
        data.battle_logs.forEach(log => {
            const p = document.createElement('p');
            if (log.includes('INTERCEPTED')) p.className = 'text-rose-400 font-bold';
            else if (log.includes('MFA CHALLENGE')) p.className = 'text-amber-400';
            else if (log.includes('EVADED')) p.className = 'text-slate-400';
            else if (log.includes('[+]')) p.className = 'text-emerald-400 font-bold';
            else p.className = 'text-sky-300';
            p.textContent = log;
            terminal.appendChild(p);
        });
        terminal.scrollTop = terminal.scrollHeight;

        // Update score
        document.getElementById('rtDefenseScore').textContent = `${data.interception_rate_pct}%`;
        document.getElementById('rtAttr-ml').textContent = `${data.defense_attribution['XGBoost ML Ensemble']} Hits`;
        document.getElementById('rtAttr-geo').textContent = `${data.defense_attribution['Impossible Travel Engine']} Hits`;
        document.getElementById('rtAttr-graph').textContent = `${data.defense_attribution['Money Mule Graph Detector']} Hits`;
        document.getElementById('rtAttr-rules').textContent = `${data.defense_attribution['Policy Rules Engine']} Hits`;

        showToast(`Red Team Campaign Concluded: ${data.interception_rate_pct}% Intercepted`, 'success');
        fetchAnalytics();

    } catch (err) {
        terminal.innerHTML += `<p class="text-rose-400 font-bold">[!] Error: ${err.message}</p>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="play" class="w-4 h-4"></i><span>Launch Adversarial Campaign</span>`;
        if (window.lucide) lucide.createIcons();
    }
}

// ==========================================
// 7. VISUAL POLICY RULES ENGINE
// ==========================================
async function loadPolicyRules() {
    try {
        const res = await fetch('/api/v1/rules');
        if (!res.ok) return;
        const rules = await res.json();

        const tbody = document.getElementById('rulesTableBody');
        tbody.innerHTML = '';

        if (!rules.length) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-500 font-sans">No policy rules registered.</td></tr>`;
            return;
        }

        rules.forEach(r => {
            const tr = document.createElement('tr');
            const actionClass = r.action === 'FORCE_BLOCK' ? 'verdict-pill verdict-block' : (r.action === 'REQUIRE_MFA' ? 'verdict-pill verdict-flag' : 'verdict-pill verdict-approve');

            tr.innerHTML = `
                <td>
                    <label class="switch">
                        <input type="checkbox" ${r.is_active ? 'checked' : ''} onchange="togglePolicyRule(${r.id})">
                        <span class="slider"></span>
                    </label>
                </td>
                <td class="font-mono text-indigo-400 font-bold">${r.rule_code}</td>
                <td>
                    <span class="text-white font-bold block">${r.name}</span>
                    <span class="text-[10px] text-slate-400 block">${r.description || 'No description'}</span>
                </td>
                <td class="font-mono text-amber-300 font-bold">${r.field} ${r.operator} ${r.value}</td>
                <td><span class="${actionClass}">${r.action}</span></td>
                <td class="font-mono text-slate-300">${r.priority}</td>
                <td><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#0e1118] text-white border border-[#262d3e] font-mono">${r.trigger_count} Hits</span></td>
                <td class="text-right">
                    <button onclick="deletePolicyRule(${r.id})" class="text-rose-400 hover:text-rose-300 p-1"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        if (window.lucide) lucide.createIcons();

    } catch (err) {
        console.error('Rules load error:', err);
    }
}

async function togglePolicyRule(ruleId) {
    try {
        const res = await fetch(`/api/v1/rules/${ruleId}/toggle`, { method: 'PUT' });
        if (res.ok) {
            showToast('Rule status updated', 'success');
            loadPolicyRules();
        }
    } catch (err) {
        showToast(`Toggle failed: ${err.message}`, 'error');
    }
}

async function deletePolicyRule(ruleId) {
    if (!confirm('Are you sure you want to delete this policy rule?')) return;
    try {
        const res = await fetch(`/api/v1/rules/${ruleId}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Policy rule deleted', 'info');
            loadPolicyRules();
        }
    } catch (err) {
        showToast(`Delete failed: ${err.message}`, 'error');
    }
}

function openNewRuleModal() {
    const m = document.getElementById('ruleModal');
    m.classList.remove('hidden');
    m.classList.add('flex');
}

function closeNewRuleModal() {
    const m = document.getElementById('ruleModal');
    m.classList.add('hidden');
    m.classList.remove('flex');
}

async function handleCreatePolicyRule(e) {
    e.preventDefault();
    const payload = {
        rule_code: document.getElementById('ruleInCode').value.trim(),
        name: document.getElementById('ruleInName').value.trim(),
        description: document.getElementById('ruleInDesc').value.trim(),
        field: document.getElementById('ruleInField').value,
        operator: document.getElementById('ruleInOp').value,
        value: document.getElementById('ruleInVal').value.trim(),
        action: document.getElementById('ruleInAction').value,
        priority: parseInt(document.getElementById('ruleInPriority').value) || 10,
        risk_boost: document.getElementById('ruleInAction').value === 'FORCE_BLOCK' ? 0.4 : 0.2,
        is_active: true
    };

    try {
        const res = await fetch('/api/v1/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Rule creation failed');
        showToast(`Rule ${payload.rule_code} registered`, 'success');
        closeNewRuleModal();
        loadPolicyRules();
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// ==========================================
// 8. BATCH INGESTION & STRESS BENCHMARK
// ==========================================
async function handleCsvFileSelected(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    showToast(`Uploading and analyzing ${file.name}...`, 'info');

    try {
        const res = await fetch('/api/v1/batch/upload-csv', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('CSV Processing Error');
        const data = await res.json();

        document.getElementById('batchResultsContainer').classList.remove('hidden');
        document.getElementById('benchTps').textContent = `${data.throughput_tps} TPS`;
        document.getElementById('benchP50').textContent = `${(data.processing_time_ms / data.total_ingested).toFixed(2)}ms`;
        document.getElementById('benchP95').textContent = `Total: ${data.total_ingested}`;
        document.getElementById('benchDecisions').textContent = `Pass: ${data.total_approved} | Flag: ${data.total_flagged} | Block: ${data.total_blocked}`;

        showToast(`Processed ${data.total_ingested} records @ ${data.throughput_tps} TPS`, 'success');
        fetchAnalytics();
        fetchAuditLog();

    } catch (err) {
        showToast(`CSV Upload Error: ${err.message}`, 'error');
    }
}

async function runSyntheticStressBenchmark() {
    const btn = document.getElementById('runBenchBtn');
    const batchSize = parseInt(document.getElementById('benchBatchSize').value) || 1000;
    const fraudRate = parseFloat(document.getElementById('benchFraudRate').value) || 0.20;

    btn.disabled = true;
    btn.innerHTML = `<span>Simulating High-Scale Stream (${batchSize} Txns)...</span>`;

    try {
        const res = await fetch('/api/v1/batch/stress-benchmark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                batch_size: batchSize,
                fraud_injection_rate: fraudRate
            })
        });

        if (!res.ok) throw new Error('Benchmark Failed');
        const data = await res.json();

        document.getElementById('batchResultsContainer').classList.remove('hidden');
        document.getElementById('benchTps').textContent = `${data.throughput_tps} TPS`;
        document.getElementById('benchP50').textContent = `${data.latency_percentiles_ms.p50}ms`;
        document.getElementById('benchP95').textContent = `${data.latency_percentiles_ms.p95}ms`;
        document.getElementById('benchDecisions').textContent = `Pass: ${data.verdict_distribution.approved} | Flag: ${data.verdict_distribution.flagged} | Block: ${data.verdict_distribution.blocked}`;

        showToast(`Benchmark Completed: ${data.throughput_tps} TPS (${batchSize} Txns)`, 'success');
        fetchAnalytics();

    } catch (err) {
        showToast(`Benchmark Error: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="zap" class="w-4 h-4"></i><span>Execute High-Scale Stress Test</span>`;
        if (window.lucide) lucide.createIcons();
    }
}

// ==========================================
// 9. SHAP WATERFALL VISUALIZATION
// ==========================================
function initShapChart() {
    const canvas = document.getElementById('shapChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    shapChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'SHAP Feature Impact (%)',
                data: [],
                backgroundColor: [],
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Risk Impact: ${ctx.raw > 0 ? '+' : ''}${ctx.raw}%`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: '#161a24' },
                    ticks: { color: '#94a3b8', font: { size: 9.5, family: 'JetBrains Mono' } }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#f8fafc', font: { size: 10, family: 'Inter' } }
                }
            }
        }
    });
}

function updateShapChart(shapValues) {
    if (!shapChart || !shapValues.length) return;

    const labels = shapValues.map(s => s.feature);
    const impacts = shapValues.map(s => s.impact_percentage);
    const colors = impacts.map(val => val > 0 ? 'rgba(244, 63, 94, 0.85)' : 'rgba(16, 185, 129, 0.85)');

    shapChart.data.labels = labels;
    shapChart.data.datasets[0].data = impacts;
    shapChart.data.datasets[0].backgroundColor = colors;
    shapChart.update();
}

// ==========================================
// 10. CYTOSCAPE MONEY MULE GRAPH NETWORK
// ==========================================
let rawGraphElements = { nodes: [], edges: [] };

async function loadGraphData() {
    try {
        const res = await fetch('/api/v1/graph');
        if (!res.ok) return;
        const data = await res.json();

        rawGraphElements = data;
        initCytoscape(data);
    } catch (err) {
        console.error('Graph fetch error:', err);
    }
}

function initCytoscape(graphData) {
    const container = document.getElementById('cyGraph');
    if (!container) return;

    if (cyInstance) {
        try {
            cyInstance.destroy();
        } catch (e) {}
        cyInstance = null;
    }

    cyInstance = cytoscape({
        container: container,
        elements: [...graphData.nodes, ...graphData.edges],
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'color': '#f8fafc',
                    'font-size': '9.5px',
                    'font-family': 'JetBrains Mono',
                    'text-valign': 'bottom',
                    'text-margin-y': '4px',
                    'background-color': (ele) => {
                        if (ele.data('is_mule')) return '#fbbf24';
                        if (ele.data('is_fraud') || ele.data('risk') > 0.75) return '#f43f5e';
                        return '#10b981';
                    },
                    'width': (ele) => Math.max(18, Math.min(48, ele.data('pagerank') * 8 + 18)),
                    'height': (ele) => Math.max(18, Math.min(48, ele.data('pagerank') * 8 + 18)),
                    'border-width': 2,
                    'border-color': '#161a24',
                    'transition-property': 'background-color, opacity, border-width',
                    'transition-duration': '0.2s'
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 3,
                    'border-color': '#ffffff',
                    'border-opacity': 0.9
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': (ele) => ele.data('is_cycle') ? 3 : 1.5,
                    'line-color': (ele) => ele.data('is_cycle') ? '#f43f5e' : '#222838',
                    'target-arrow-color': (ele) => ele.data('is_cycle') ? '#f43f5e' : '#475569',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 0.75,
                    'transition-property': 'line-color, opacity',
                    'transition-duration': '0.2s'
                }
            },
            {
                selector: '.faded',
                style: { 'opacity': 0.15 }
            },
            {
                selector: '.highlighted',
                style: { 'opacity': 1.0, 'border-color': '#6366f1', 'border-width': 3 }
            }
        ],
        layout: {
            name: 'concentric',
            minNodeSpacing: 44,
            padding: 24,
            animate: false
        }
    });

    cyInstance.on('tap', 'node', function (evt) {
        const node = evt.target;
        const neighborhood = node.neighborhood().add(node);

        cyInstance.elements().addClass('faded');
        neighborhood.removeClass('faded');
        node.addClass('highlighted');

        const inspector = document.getElementById('nodeInspectorContent');
        const isMule = node.data('is_mule');
        const inDeg = node.data('in_degree');
        const outDeg = node.data('out_degree');
        const risk = (node.data('risk') * 100).toFixed(1);

        inspector.innerHTML = `
            <div class="space-y-2 font-mono text-[11px] bg-[#030407] p-3 rounded-lg border border-[#161a24]">
                <div class="flex items-center justify-between border-b border-[#161a24] pb-1.5">
                    <span class="text-indigo-400 font-bold text-xs">${node.data('label')}</span>
                    <span class="px-1.5 py-0.2 text-[9px] rounded font-bold ${isMule ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'}">${isMule ? 'SUSPECT MULE' : 'STANDARD'}</span>
                </div>
                <div class="space-y-1 text-slate-300 text-[10.5px]">
                    <p>Calculated Node Risk: <strong class="${node.data('risk') > 0.5 ? 'text-rose-400 font-bold' : 'text-emerald-400'}">${risk}%</strong></p>
                    <p>In-Degree (Inflows): <strong class="text-white">${inDeg}</strong></p>
                    <p>Out-Degree (Outflows): <strong class="text-white">${outDeg}</strong></p>
                    <p>PageRank Centrality: <strong class="text-white">${node.data('pagerank')}</strong></p>
                    <p>Flow Imbalance Ratio: <strong class="text-white">${inDeg > 0 ? (outDeg / inDeg).toFixed(2) : outDeg}</strong></p>
                </div>
            </div>
        `;
    });

    cyInstance.on('tap', 'edge', function (evt) {
        const edge = evt.target;
        const inspector = document.getElementById('nodeInspectorContent');
        const isCycle = edge.data('is_cycle');
        const amt = edge.data('amount');
        const risk = (edge.data('risk') * 100).toFixed(1);

        inspector.innerHTML = `
            <div class="space-y-2 font-mono text-[11px] bg-[#030407] p-3 rounded-lg border border-[#161a24]">
                <div class="flex items-center justify-between border-b border-[#161a24] pb-1.5">
                    <span class="text-white font-bold text-xs">Route Flow</span>
                    <span class="px-1.5 py-0.2 text-[9px] rounded font-bold ${isCycle ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-800 text-slate-300'}">${isCycle ? '⚠️ CYCLE LAYER' : 'NORMAL'}</span>
                </div>
                <div class="space-y-1 text-slate-300 text-[10.5px]">
                    <p>Route: <strong class="text-white">${edge.data('source')} &rarr; ${edge.data('target')}</strong></p>
                    <p>Transfer Value: <strong class="text-white">${formatCurrency(amt)}</strong></p>
                    <p>Transaction Risk: <strong class="${edge.data('risk') > 0.5 ? 'text-rose-400 font-bold' : 'text-emerald-400'}">${risk}%</strong></p>
                    <p>Transaction ID: <strong class="text-indigo-300">${edge.data('txn_id')}</strong></p>
                </div>
            </div>
        `;
    });

    cyInstance.on('tap', function (evt) {
        if (evt.target === cyInstance) {
            cyInstance.elements().removeClass('faded highlighted');
        }
    });

    setTimeout(() => {
        if (cyInstance) {
            cyInstance.resize();
            cyInstance.fit();
        }
    }, 80);
}

function zoomGraphIn() {
    if (cyInstance) cyInstance.zoom(cyInstance.zoom() * 1.25);
}

function zoomGraphOut() {
    if (cyInstance) cyInstance.zoom(cyInstance.zoom() * 0.8);
}

function fitGraph() {
    if (cyInstance) {
        cyInstance.resize();
        cyInstance.fit();
    }
}

function searchGraphNode(query) {
    if (!cyInstance) return;
    const q = (query || '').trim().toLowerCase();
    if (!q) {
        cyInstance.elements().removeClass('faded highlighted');
        return;
    }

    const matchedNodes = cyInstance.nodes().filter(n => n.data('label').toLowerCase().includes(q));
    if (matchedNodes.length > 0) {
        cyInstance.elements().addClass('faded');
        matchedNodes.removeClass('faded').addClass('highlighted');
        cyInstance.animate({
            center: { eles: matchedNodes.first() },
            zoom: 1.5,
            duration: 300
        });
    }
}

function filterGraphNodes(filterType) {
    if (!cyInstance || !rawGraphElements.nodes) return;

    document.querySelectorAll('[id^="filterGraph-"]').forEach(btn => {
        btn.className = 'px-2.5 py-1 rounded text-slate-400 hover:text-white';
    });
    const activeBtn = document.getElementById(`filterGraph-${filterType}`);
    if (activeBtn) {
        activeBtn.className = 'px-2.5 py-1 rounded bg-[#0e1118] text-white';
    }

    if (filterType === 'all') {
        initCytoscape(rawGraphElements);
    } else if (filterType === 'mules') {
        const muleNodes = rawGraphElements.nodes.filter(n => n.data.is_mule);
        const muleNodeIds = new Set(muleNodes.map(n => n.data.id));
        const muleEdges = rawGraphElements.edges.filter(e => muleNodeIds.has(e.data.source) || muleNodeIds.has(e.data.target));
        initCytoscape({ nodes: muleNodes, edges: muleEdges });
    } else if (filterType === 'high_risk') {
        const highRiskNodes = rawGraphElements.nodes.filter(n => n.data.risk > 0.6 || n.data.is_fraud);
        const hrNodeIds = new Set(highRiskNodes.map(n => n.data.id));
        const hrEdges = rawGraphElements.edges.filter(e => hrNodeIds.has(e.data.source) || hrNodeIds.has(e.data.target));
        initCytoscape({ nodes: highRiskNodes, edges: hrEdges });
    }
}

// ==========================================
// 11. HUMAN-IN-THE-LOOP (HITL) QUEUE
// ==========================================
async function loadHitlQueue() {
    try {
        const res = await fetch('/api/v1/hitl/queue');
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('hitlBadge').textContent = data.pending_count;

        const tbody = document.getElementById('hitlTableBody');
        tbody.innerHTML = '';

        if (!data.pending_items.length) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-slate-500 font-sans">No transactions currently pending triage.</td></tr>`;
            return;
        }

        data.pending_items.forEach(t => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="font-mono text-indigo-400 font-bold">${t.transaction_id}</td>
                <td>
                    <span class="text-white font-bold">${formatCurrency(t.amount)}</span>
                    <span class="text-[10px] text-slate-400 block">${t.type}</span>
                </td>
                <td class="font-mono text-slate-400">${t.name_orig} &rarr; ${t.name_dest}</td>
                <td class="font-bold font-mono text-amber-400">${t.risk_percentage}</td>
                <td class="text-[10.5px] text-slate-300 font-sans">${t.flag_reasons.slice(0, 2).join('; ') || 'Threshold breach'}</td>
                <td class="text-right space-x-1.5 font-sans">
                    <button onclick="submitHitlDecision('${t.transaction_id}', 'CONFIRMED_FRAUD')" class="bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 px-2.5 py-1 rounded text-[11px] border border-rose-500/30 transition font-medium">Confirm Block</button>
                    <button onclick="submitHitlDecision('${t.transaction_id}', 'FALSE_POSITIVE')" class="bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 px-2.5 py-1 rounded text-[11px] border border-emerald-500/30 transition font-medium">Approve</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error('HITL error:', err);
    }
}

async function submitHitlDecision(txnId, verdict) {
    try {
        const res = await fetch('/api/v1/hitl/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_id: txnId, verdict: verdict })
        });
        if (res.ok) {
            showToast(`Transaction ${txnId} marked as ${verdict}`, 'success');
            loadHitlQueue();
            fetchAnalytics();
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// ==========================================
// 12. CONTINUOUS CONCEPT DRIFT MONITOR
// ==========================================
async function loadDriftReport() {
    try {
        const res = await fetch('/api/v1/drift');
        if (!res.ok) return;
        const data = await res.json();

        const amtFeature = data.features_drift.find(f => f.feature === 'Transaction Amount') || {};
        const ratioFeature = data.features_drift.find(f => f.feature === 'Transfer Ratio') || {};

        document.getElementById('driftAmtPsi').textContent = `PSI: ${amtFeature.psi || 0.015}`;
        document.getElementById('driftRatioPsi').textContent = `PSI: ${ratioFeature.psi || 0.022}`;
        document.getElementById('driftOverallStatus').textContent = `${data.overall_drift_status}`;
        document.getElementById('driftRecommendationText').textContent = data.recommendation;

    } catch (err) {
        console.error('Drift fetch error:', err);
    }
}

// ==========================================
// 13. WEBSOCKET LIVE STREAMING
// ==========================================
function toggleLiveStream() {
    if (isStreaming) {
        stopLiveStream();
    } else {
        startLiveStream();
    }
}

function startLiveStream() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live-stream`;

    liveStreamSocket = new WebSocket(wsUrl);

    liveStreamSocket.onopen = () => {
        isStreaming = true;
        streamTxCount = 0;
        streamStartTime = Date.now();

        document.getElementById('streamIndicator').className = 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse';
        document.getElementById('streamLabel').textContent = 'Radar Stream: ACTIVE';
        document.getElementById('tpsBadge').classList.remove('hidden');
        showToast('WebSocket Live Stream Connected', 'success');
    };

    liveStreamSocket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.event === 'NEW_TRANSACTION') {
            streamTxCount++;
            updateTpsMeter();
            prependLiveTransactionToAuditLog(msg.transaction);
            fetchAnalytics();

            if (threatMap) {
                threatMap.addTransactionArc(
                    msg.transaction.location_city || 'New York, US',
                    'Frankfurt, DE',
                    msg.transaction.risk_score || 0.1,
                    msg.transaction.decision === 'BLOCK'
                );
            }
        }
    };

    liveStreamSocket.onclose = () => {
        stopLiveStream();
    };
}

function stopLiveStream() {
    isStreaming = false;
    if (liveStreamSocket) {
        liveStreamSocket.close();
        liveStreamSocket = null;
    }
    document.getElementById('streamIndicator').className = 'w-2 h-2 rounded-full bg-slate-500';
    document.getElementById('streamLabel').textContent = 'Radar Stream: OFF';
    document.getElementById('tpsBadge').classList.add('hidden');
    showToast('Live Stream Disconnected', 'info');
}

function updateTpsMeter() {
    const elapsedSec = (Date.now() - streamStartTime) / 1000.0;
    if (elapsedSec > 0) {
        const tps = (streamTxCount / elapsedSec).toFixed(1);
        document.getElementById('tpsBadge').textContent = `${tps} TPS`;
    }
}

function prependLiveTransactionToAuditLog(txn) {
    const tbody = document.getElementById('txnTableBody');
    const tr = document.createElement('tr');

    const decisionBadgeClass = txn.decision === 'BLOCK'
        ? 'verdict-pill verdict-block'
        : (txn.decision === 'FLAG' ? 'verdict-pill verdict-flag' : 'verdict-pill verdict-approve');

    tr.innerHTML = `
        <td class="text-slate-400 font-mono text-[10.5px]">Just Now</td>
        <td class="font-bold text-indigo-400 font-mono">${txn.transaction_id}</td>
        <td><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-black text-slate-300 border border-[#1a1f2c] font-mono">${txn.type}</span></td>
        <td class="font-bold text-white font-mono">${formatCurrency(txn.amount)}</td>
        <td class="text-slate-400 font-mono">${txn.name_orig} &rarr; ${txn.name_dest}</td>
        <td class="text-slate-300 font-mono">${txn.location_city || 'New York'}</td>
        <td class="font-bold font-mono text-white">${txn.risk_percentage}</td>
        <td><span class="${decisionBadgeClass}">${txn.decision}</span></td>
        <td class="text-right">
            <button onclick="openSarModal('${txn.transaction_id}')" class="text-xs text-indigo-400 hover:text-indigo-300 font-sans font-semibold">SAR</button>
        </td>
    `;

    tbody.insertBefore(tr, tbody.firstChild);

    if (tbody.children.length > 50) {
        tbody.removeChild(tbody.lastChild);
    }
}

// ==========================================
// 14. REGULATORY SAR REPORT MODAL
// ==========================================
function openSarModalForCurrent() {
    if (currentTransactionId) {
        openSarModal(currentTransactionId);
    }
}

async function openSarModal(txnId) {
    const modal = document.getElementById('sarModal');
    const content = document.getElementById('sarModalContent');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    content.textContent = 'Generating certified FinCEN Regulatory SAR Report...';

    try {
        const res = await fetch('/api/v1/sar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_id: txnId })
        });
        const data = await res.json();
        content.textContent = data.report_text;
    } catch (err) {
        content.textContent = `SAR generation failed: ${err.message}`;
    }
}

function closeSarModal() {
    const modal = document.getElementById('sarModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function copySarText() {
    const text = document.getElementById('sarModalContent').textContent;
    navigator.clipboard.writeText(text);
    showToast('Regulatory SAR Report copied to clipboard!', 'success');
}

// ==========================================
// 15. AUDIT LOG & ANALYTICS CHARTS
// ==========================================
async function fetchAnalytics() {
    try {
        const res = await fetch('/api/v1/analytics');
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('kpiTotal').textContent = (data.total_transactions || 0).toLocaleString();
        document.getElementById('kpiApproved').textContent = (data.total_approved || 0).toLocaleString();
        document.getElementById('kpiFlagged').textContent = (data.total_flagged || 0).toLocaleString();
        document.getElementById('kpiBlocked').textContent = (data.total_blocked || 0).toLocaleString();
        document.getElementById('kpiFraudRate').textContent = `${data.fraud_rate_percentage || 0.0}% Rate`;

        updateCharts(data);
    } catch (err) {
        console.error('Analytics error:', err);
    }
}

async function fetchAuditLog() {
    try {
        const res = await fetch('/api/v1/transactions?limit=30');
        if (!res.ok) return;
        const data = await res.json();

        allAuditTransactions = data.transactions || data.items || [];
        renderAuditTable(allAuditTransactions);

    } catch (err) {
        console.error('Audit log fetch error:', err);
    }
}

function filterAuditLogTable() {
    const query = (document.getElementById('searchInput')?.value || '').trim().toLowerCase();
    const decision = document.getElementById('filterDecision')?.value || 'ALL';

    const filtered = allAuditTransactions.filter(t => {
        const matchesQuery = !query || 
            (t.transaction_id && t.transaction_id.toLowerCase().includes(query)) ||
            (t.name_orig && t.name_orig.toLowerCase().includes(query)) ||
            (t.name_dest && t.name_dest.toLowerCase().includes(query)) ||
            (t.location_city && t.location_city.toLowerCase().includes(query));

        const matchesDecision = decision === 'ALL' || t.decision === decision;

        return matchesQuery && matchesDecision;
    });

    renderAuditTable(filtered);
}

function renderAuditTable(items) {
    const tbody = document.getElementById('txnTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!items || !items.length) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center py-8 text-slate-500 font-sans">No matching transactions found.</td></tr>`;
        return;
    }

    items.forEach(t => {
        const tr = document.createElement('tr');

        const decisionBadgeClass = t.decision === 'BLOCK'
            ? 'verdict-pill verdict-block'
            : (t.decision === 'FLAG' ? 'verdict-pill verdict-flag' : 'verdict-pill verdict-approve');

        const timeStr = t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : 'N/A';

        tr.innerHTML = `
            <td class="text-slate-400 font-mono text-[10.5px]">${timeStr}</td>
            <td class="font-bold text-indigo-400 font-mono">${t.transaction_id}</td>
            <td><span class="px-2 py-0.5 rounded text-[10px] font-bold bg-black text-slate-300 border border-[#1a1f2c] font-mono">${t.type}</span></td>
            <td class="font-bold text-white font-mono">${formatCurrency(t.amount)}</td>
            <td class="text-slate-400 font-mono">${t.name_orig} &rarr; ${t.name_dest}</td>
            <td class="text-slate-300 font-mono">${t.location_city || 'New York'}</td>
            <td class="font-bold font-mono text-white">${t.risk_percentage}</td>
            <td><span class="${decisionBadgeClass}">${t.decision}</span></td>
            <td class="text-right">
                <button onclick="openSarModal('${t.transaction_id}')" class="text-xs text-indigo-400 hover:text-indigo-300 font-sans font-semibold">SAR</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function initCharts() {
    const dCtx = document.getElementById('decisionChart').getContext('2d');
    decisionChart = new Chart(dCtx, {
        type: 'doughnut',
        data: {
            labels: ['Approved', 'Flagged', 'Blocked'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#10b981', '#fbbf24', '#f43f5e'],
                borderColor: '#080a0f',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 10, font: { size: 11, family: 'Inter' } } }
            }
        }
    });

    const rCtx = document.getElementById('riskDistributionChart').getContext('2d');
    riskDistChart = new Chart(rCtx, {
        type: 'bar',
        data: {
            labels: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'],
            datasets: [{
                label: 'Transactions',
                data: [0, 0, 0, 0, 0],
                backgroundColor: '#6366f1',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: '#1a1f2c' }, ticks: { color: '#94a3b8', font: { size: 9.5, family: 'JetBrains Mono' } } },
                y: { grid: { color: '#1a1f2c' }, ticks: { color: '#94a3b8', font: { size: 9.5, family: 'JetBrains Mono' } } }
            }
        }
    });
}

function updateCharts(data) {
    if (decisionChart) {
        decisionChart.data.datasets[0].data = [
            data.total_approved || 0,
            data.total_flagged || 0,
            data.total_blocked || 0
        ];
        decisionChart.update();
    }

    if (riskDistChart && data.risk_distribution) {
        riskDistChart.data.datasets[0].data = Object.values(data.risk_distribution);
        riskDistChart.update();
    }
}

// ==========================================
// 16. SYSTEM ENVIRONMENT RESET
// ==========================================
function promptResetSystem() {
    const m = document.getElementById('resetConfirmModal');
    if (m) {
        m.classList.remove('hidden');
        m.classList.add('flex');
        if (window.lucide) lucide.createIcons();
    }
}

function closeResetModal() {
    const m = document.getElementById('resetConfirmModal');
    if (m) {
        m.classList.add('hidden');
        m.classList.remove('flex');
    }
}

async function executeSystemReset(reseed = true) {
    closeResetModal();
    showToast(reseed ? 'Resetting and seeding demo environment...' : 'Purging all environment data...', 'info');

    // If live stream is running, stop it
    if (isStreaming) {
        stopLiveStream();
    }

    try {
        const res = await fetch('/api/v1/system/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reseed_demo_data: reseed })
        });

        if (!res.ok) throw new Error('Reset request failed');
        const data = await res.json();

        // 1. Reset Simulator UI
        document.getElementById('resultBox')?.classList.add('hidden');
        currentTransactionId = null;

        // 2. Reset Red Team Terminal & Attribution
        const rtTerminal = document.getElementById('rtTerminalLogs');
        if (rtTerminal) {
            rtTerminal.innerHTML = `<span class="text-slate-500 italic">Select an offensive campaign and click "Launch Adversarial Campaign" to stress-test defense pipelines...</span>`;
        }
        const scoreEl = document.getElementById('rtDefenseScore');
        if (scoreEl) scoreEl.textContent = '--%';
        const aMl = document.getElementById('rtAttr-ml');
        if (aMl) aMl.textContent = '--';
        const aGeo = document.getElementById('rtAttr-geo');
        if (aGeo) aGeo.textContent = '--';
        const aGraph = document.getElementById('rtAttr-graph');
        if (aGraph) aGraph.textContent = '--';
        const aRules = document.getElementById('rtAttr-rules');
        if (aRules) aRules.textContent = '--';

        // 3. Reset Batch Ingestion Container
        document.getElementById('batchResultsContainer')?.classList.add('hidden');

        // 4. Reset Threat Map
        if (threatMap) {
            threatMap.arcs = [];
            const feed = document.getElementById('mapInterceptFeed');
            if (feed) feed.innerHTML = '';
        }

        // 5. Reload Fresh Data Across All Tabs
        await fetchAnalytics();
        await fetchAuditLog();
        await loadPolicyRules();
        await loadHitlQueue();
        await loadDriftReport();
        loadGraphData();

        showToast(data.message, 'success');

    } catch (err) {
        showToast(`Reset error: ${err.message}`, 'error');
    }
}

