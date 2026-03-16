document.addEventListener('DOMContentLoaded', () => {
    // ── State ──────────────────────────────────────────────────
    let currentTab = 'upload-data';
    let forecastChart = null;
    let lastForecastResult = null;

    // ── DOM Elements ──────────────────────────────────────────
    const navItems = document.querySelectorAll('.nav-item');
    const currentTabName = document.getElementById('current-tab-name');

    const forecastSection = document.getElementById('forecast-section');
    const metricsSection = document.getElementById('metrics-section');
    const scraperSection = document.getElementById('scraper-section');
    const dataSection = document.getElementById('data-section');
    const decisionSection = document.getElementById('decision-section');
    const sentimentSection = document.getElementById('sentiment-section');

    const allSections = [forecastSection, metricsSection, scraperSection, dataSection, decisionSection, sentimentSection];

    // Forecast
    const productSelect = document.getElementById('product-select');
    const modelSelect = document.getElementById('model-select');
    const periodsInput = document.getElementById('periods-input');
    const runForecastBtn = document.getElementById('run-forecast-btn');
    const forecastLoading = document.getElementById('forecast-loading');
    const chartCard = document.getElementById('chart-card');
    const bestBuySection = document.getElementById('best-buy-section');
    const bestBuyCards = document.getElementById('best-buy-cards');

    // Metrics
    const metricsEmpty = document.getElementById('metrics-empty');
    const metricsContent = document.getElementById('metrics-content');
    const metricsGrid = document.getElementById('metrics-grid');
    const metricsTableBody = document.getElementById('metrics-table-body');

    // Scraper
    const scraperForm = document.getElementById('scraper-form');
    const formTitle = document.getElementById('form-title');
    const formDesc = document.getElementById('form-desc');
    const dynamicInputs = document.getElementById('dynamic-inputs');
    const statusContainer = document.getElementById('status-container');
    const statusText = document.getElementById('status-text');
    const statusSpinner = document.querySelector('.spinner');

    // Database
    // Database
    const dataTableBody = document.getElementById('data-table-body');
    const refreshBtn = document.getElementById('refresh-db-btn');
    const downloadBtn = document.getElementById('download-csv-btn');

    // Decision & Alerts
    const decisionProductSelect = document.getElementById('decision-product-select');
    
    const runDecisionBtn = document.getElementById('run-decision-btn');
    const decisionLoading = document.getElementById('decision-loading');
    const decisionResults = document.getElementById('decision-results');
    const decisionWidget = document.getElementById('decision-widget');
    const decisionIcon = document.getElementById('decision-icon');
    const decisionTitle = document.getElementById('decision-title');
    const decisionReason = document.getElementById('decision-reason');
    const decisionPrice = document.getElementById('decision-price');
    const decisionRatio = document.getElementById('decision-ratio');
    
    const alertEmail = document.getElementById('alert-email');
    const subscribeBtn = document.getElementById('subscribe-alert-btn');
    const subscribeStatus = document.getElementById('subscribe-status');
    let sentimentChart = null;

    // Sentiment Analysis
    const sentimentProductSelect = document.getElementById('sentiment-product-select');
    const runSentimentBtn = document.getElementById('run-sentiment-btn');
    const sentimentLoading = document.getElementById('sentiment-loading');
    const sentimentResults = document.getElementById('sentiment-results');
    const sentimentTotalCount = document.getElementById('sentiment-total-count');
    const sentimentSamplesBody = document.getElementById('sentiment-samples-body');
    let standaloneSentimentChart = null;
    let categoryBarChart = null;

    // ── Tab Config (Flipkart scrapers) ────────────────────────
    const tabConfigs = {
        'flipkart-price': {
            title: 'Flipkart Price History Scraper',
            desc: 'Enter a PriceHistory.app URL for a Flipkart product to extract JSON pricing data.',
            endpoint: '/api/scrape/flipkart-price',
            inputs: `
                <label for="url-input">PriceHistory.app URL</label>
                <input type="url" id="url-input" placeholder="https://pricehistory.app/p/..." required>
                <a href="https://pricehistory.app/" target="_blank" style="color: var(--accent-primary); font-size: 0.8rem; text-decoration: none; display: inline-block; margin-top: 0.25rem;">
                    <i data-lucide="external-link" style="width: 12px; height: 12px; vertical-align: middle;"></i> Find Flipkart products on PriceHistory.app
                </a>
            `
        },
        'flipkart-reviews': {
            title: 'Flipkart Reviews Scraper',
            desc: 'Search for a product name on Flipkart to navigate and scrape its verified reviews.',
            endpoint: '/api/scrape/flipkart-reviews',
            inputs: `
                <label for="query-input">Search Query / Product Name</label>
                <input type="text" id="query-input" placeholder="e.g. apple iphone 15" required>
                <a href="https://www.flipkart.com/" target="_blank" style="color: var(--accent-primary); font-size: 0.8rem; text-decoration: none; display: inline-block; margin-top: 0.25rem;">
                    <i data-lucide="external-link" style="width: 12px; height: 12px; vertical-align: middle;"></i> Browse Flipkart.com for product names
                </a>
            `
        }
    };

    // ── Navigation ────────────────────────────────────────────
    function showSection(tabId) {
        allSections.forEach(s => s.classList.add('hidden'));
        
        if (tabId === 'forecast') {
            forecastSection.classList.remove('hidden');
            populateProductSelect();
        } else if (tabId === 'metrics') {
            metricsSection.classList.remove('hidden');
            renderMetrics();
        } else if (tabId === 'database') {
            dataSection.classList.remove('hidden');
            fetchData();
        } else if (tabId === 'decision') {
            decisionSection.classList.remove('hidden');
            populateProductSelect(decisionProductSelect);
        } else if (tabId === 'sentiment') {
            sentimentSection.classList.remove('hidden');
            populateProductSelect(sentimentProductSelect);
        } else if (tabConfigs[tabId]) {
            scraperSection.classList.remove('hidden');
            loadScraperTab(tabId);
        }
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            currentTabName.textContent = item.textContent.trim();
            currentTab = tabId;
            showSection(tabId);
        });
    });

    // ── Forecasting ──────────────────────────────────────────
    async function populateProductSelect(selectElement = productSelect) {
        try {
            const res = await fetch('/api/products');
            const data = await res.json();
            selectElement.innerHTML = '<option value="">— select product —</option>';
            if (data.success) {
                data.products.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p;
                    opt.textContent = p;
                    selectElement.appendChild(opt);
                });
            }
        } catch {}
    }

    // ── Forecasting ──────────────────────────────────────────
    runForecastBtn.addEventListener('click', async () => {
        const product_name = productSelect.value;
        const model = modelSelect.value;
        const periods = parseInt(periodsInput.value) || 30;

        if (!product_name) {
            alert('Please select a product first.');
            return;
        }

        runForecastBtn.disabled = true;
        forecastLoading.classList.remove('hidden');
        chartCard.classList.add('hidden');
        bestBuySection.classList.add('hidden');

        try {
            const res = await fetch('/api/forecast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_name, model, periods })
            });
            const result = await res.json();

            if (result.success) {
                lastForecastResult = result;
                renderChart(result);
                renderBestBuy(result);
                chartCard.classList.remove('hidden');
            } else {
                alert('Forecast failed: ' + (result.detail || 'Unknown error'));
            }
        } catch (err) {
            alert('Forecast error: ' + err.message);
        }

        forecastLoading.classList.add('hidden');
        runForecastBtn.disabled = false;
    });

    function renderChart(result) {
        const ctx = document.getElementById('forecast-chart').getContext('2d');
        if (forecastChart) forecastChart.destroy();

        const datasets = [];

        // Historical data
        if (result.historical) {
            datasets.push({
                label: 'Historical Price',
                data: result.historical.map(d => ({ x: d.date, y: d.price })),
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                fill: true,
                tension: 0.3,
                order: 3,
            });
        }

        let lastHistoricalData = null;
        if (result.historical && result.historical.length > 0) {
            const h = result.historical[result.historical.length - 1];
            lastHistoricalData = { x: h.date, y: h.price };
        }

        // Prophet
        if (result.prophet && result.prophet.success) {
            let pData = result.prophet.forecast.map(d => ({ x: d.date, y: d.predicted_price }));
            let pUpper = result.prophet.forecast.map(d => ({ x: d.date, y: d.upper_bound }));
            let pLower = result.prophet.forecast.map(d => ({ x: d.date, y: d.lower_bound }));
            
            if (lastHistoricalData) {
                pData.unshift({ x: lastHistoricalData.x, y: lastHistoricalData.y });
                pUpper.unshift({ x: lastHistoricalData.x, y: lastHistoricalData.y });
                pLower.unshift({ x: lastHistoricalData.x, y: lastHistoricalData.y });
            }

            datasets.push({
                label: 'Prophet Forecast',
                data: pData,
                borderColor: '#10b981',
                backgroundColor: 'transparent',
                borderWidth: 2.5,
                borderDash: [6, 3],
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0.3,
                order: 1,
            });
            datasets.push({
                label: 'Prophet Confidence',
                data: pUpper,
                borderColor: 'transparent',
                backgroundColor: 'rgba(16, 185, 129, 0.08)',
                pointRadius: 0,
                fill: '+1',
                tension: 0.3,
                order: 2,
            });
            datasets.push({
                label: '_prophet_lower',
                data: pLower,
                borderColor: 'transparent',
                backgroundColor: 'transparent',
                pointRadius: 0,
                tension: 0.3,
                order: 2,
            });
        }

        // Chronos
        if (result.chronos && result.chronos.success) {
            let cData = result.chronos.forecast.map(d => ({ x: d.date, y: d.predicted_price }));
            let cUpper = result.chronos.forecast.map(d => ({ x: d.date, y: d.upper_bound }));
            let cLower = result.chronos.forecast.map(d => ({ x: d.date, y: d.lower_bound }));
            
            if (lastHistoricalData) {
                cData.unshift({ x: lastHistoricalData.x, y: lastHistoricalData.y });
                cUpper.unshift({ x: lastHistoricalData.x, y: lastHistoricalData.y });
                cLower.unshift({ x: lastHistoricalData.x, y: lastHistoricalData.y });
            }

            datasets.push({
                label: 'Chronos Forecast',
                data: cData,
                borderColor: '#f59e0b',
                backgroundColor: 'transparent',
                borderWidth: 2.5,
                borderDash: [6, 3],
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0.3,
                order: 1,
            });
            datasets.push({
                label: 'Chronos Confidence',
                data: cUpper,
                borderColor: 'transparent',
                backgroundColor: 'rgba(245, 158, 11, 0.08)',
                pointRadius: 0,
                fill: '+1',
                tension: 0.3,
                order: 2,
            });
            datasets.push({
                label: '_chronos_lower',
                data: cLower,
                borderColor: 'transparent',
                backgroundColor: 'transparent',
                pointRadius: 0,
                tension: 0.3,
                order: 2,
            });
        }

        forecastChart = new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#e5e7eb',
                            font: { family: 'Inter', size: 12 },
                            filter: item => !item.text.startsWith('_'),
                            usePointStyle: true,
                            pointStyle: 'line',
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(20, 20, 29, 0.95)',
                        titleColor: '#f8f9fa',
                        bodyColor: '#a0a0b0',
                        borderColor: 'rgba(99, 102, 241, 0.3)',
                        borderWidth: 1,
                        padding: 12,
                        titleFont: { family: 'Inter', weight: '600' },
                        bodyFont: { family: 'Inter' },
                        callbacks: {
                            label: ctx => {
                                if (ctx.dataset.label.startsWith('_')) return null;
                                return `${ctx.dataset.label}: ₹${ctx.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: { unit: 'week', tooltipFormat: 'MMM dd, yyyy' },
                        ticks: { color: '#a0a0b0', font: { family: 'Inter', size: 11 } },
                        grid: { color: 'rgba(255,255,255,0.04)' },
                    },
                    y: {
                        ticks: {
                            color: '#a0a0b0',
                            font: { family: 'Inter', size: 11 },
                            callback: v => '₹' + v.toLocaleString(),
                        },
                        grid: { color: 'rgba(255,255,255,0.04)' },
                    }
                }
            }
        });
    }

    function renderBestBuy(result) {
        bestBuyCards.innerHTML = '';
        let cards = [];

        if (result.prophet && result.prophet.success && result.prophet.best_time_to_buy) {
            const b = result.prophet.best_time_to_buy;
            cards.push(buildBestBuyCard('Prophet', b, '#10b981'));
        }
        if (result.chronos && result.chronos.success && result.chronos.best_time_to_buy) {
            const b = result.chronos.best_time_to_buy;
            cards.push(buildBestBuyCard('Chronos', b, '#f59e0b'));
        }

        if (cards.length) {
            bestBuyCards.innerHTML = cards.join('');
            bestBuySection.classList.remove('hidden');
            lucide.createIcons();
        }
    }

    function buildBestBuyCard(model, info, color) {
        const dateStr = new Date(info.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
        return `
            <div class="best-buy-card" style="--accent: ${color}">
                <div class="best-buy-badge"><i data-lucide="tag" style="width:14px;height:14px;"></i> Best Time to Buy (${model})</div>
                <div class="best-buy-price">₹${info.predicted_price.toLocaleString()}</div>
                <div class="best-buy-date"><i data-lucide="calendar" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;"></i>${dateStr}</div>
                <div class="best-buy-range">Range: ₹${info.lower_bound.toLocaleString()} – ₹${info.upper_bound.toLocaleString()}</div>
            </div>
        `;
    }

    // ── Metrics ──────────────────────────────────────────────
    const metricDescriptions = {
        mape: 'Mean Absolute Percentage Error — lower is better',
        mae: 'Mean Absolute Error — lower is better',
        rmse: 'Root Mean Squared Error — lower is better',
        r2: 'R-squared — closer to 1 is better',
        smape: 'Symmetric MAPE — lower is better',
    };
    const metricLabels = { mape: 'MAPE (%)', mae: 'MAE', rmse: 'RMSE', r2: 'R²', smape: 'SMAPE (%)' };
    const metricIcons = { mape: 'percent', mae: 'ruler', rmse: 'sigma', r2: 'target', smape: 'scale' };

    function renderMetrics() {
        if (!lastForecastResult) return;

        const hasProphet = lastForecastResult.prophet && lastForecastResult.prophet.success;
        const hasChronos = lastForecastResult.chronos && lastForecastResult.chronos.success;

        if (!hasProphet && !hasChronos) return;

        metricsEmpty.classList.add('hidden');
        metricsContent.classList.remove('hidden');

        document.getElementById('th-prophet').classList.toggle('hidden', !hasProphet);
        document.getElementById('th-chronos').classList.toggle('hidden', !hasChronos);

        // Grid cards
        metricsGrid.innerHTML = '';
        const allMetricKeys = ['mape', 'mae', 'rmse', 'r2', 'smape'];

        allMetricKeys.forEach(key => {
            const pVal = hasProphet ? lastForecastResult.prophet.metrics[key] : null;
            const cVal = hasChronos ? lastForecastResult.chronos.metrics[key] : null;

            let bestModel = '';
            if (pVal !== null && cVal !== null) {
                if (key === 'r2') bestModel = pVal >= cVal ? 'Prophet' : 'Chronos';
                else bestModel = pVal <= cVal ? 'Prophet' : 'Chronos';
            }

            metricsGrid.innerHTML += `
                <div class="metric-card">
                    <div class="metric-label"><i data-lucide="${metricIcons[key]}" style="width:14px;height:14px;vertical-align:-2px;margin-right:4px;"></i>${metricLabels[key]}</div>
                    <div class="metric-values">
                        ${hasProphet ? `<div class="metric-val prophet-val"><span class="model-dot" style="background:#10b981;"></span>${pVal !== null ? pVal : '—'}</div>` : ''}
                        ${hasChronos ? `<div class="metric-val chronos-val"><span class="model-dot" style="background:#f59e0b;"></span>${cVal !== null ? cVal : '—'}</div>` : ''}
                    </div>
                    ${bestModel ? `<div class="metric-winner"><i data-lucide="trophy" style="width:12px;height:12px;vertical-align:-1px;margin-right:3px;color:#f59e0b;"></i>${bestModel} wins</div>` : ''}
                </div>
            `;
        });

        // Table
        metricsTableBody.innerHTML = '';
        allMetricKeys.forEach(key => {
            const pVal = hasProphet ? lastForecastResult.prophet.metrics[key] : null;
            const cVal = hasChronos ? lastForecastResult.chronos.metrics[key] : null;
            metricsTableBody.innerHTML += `
                <tr>
                    <td><strong>${metricLabels[key]}</strong></td>
                    ${hasProphet ? `<td class="metric-cell">${pVal !== null ? pVal : '—'}</td>` : ''}
                    ${hasChronos ? `<td class="metric-cell">${cVal !== null ? cVal : '—'}</td>` : ''}
                    <td class="text-muted">${metricDescriptions[key]}</td>
                </tr>
            `;
        });

        lucide.createIcons();
    }

    // ── Decision & Alerts ────────────────────────────────────
    
    runDecisionBtn.addEventListener('click', async () => {
        const product_name = decisionProductSelect.value;
        
        if (!product_name) {
            alert('Please select a product first.');
            return;
        }

        runDecisionBtn.disabled = true;
        decisionLoading.classList.remove('hidden');
        decisionResults.classList.add('hidden');

        try {
            const res = await fetch('/api/decision', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_name })
            });
            const result = await res.json();

            if (result.success) {
                // Update Widget
                decisionWidget.className = 'decision-widget';
                if (result.decision === 'Buy Now') {
                    decisionWidget.classList.add('buy');
                    decisionIcon.setAttribute('data-lucide', 'check-circle');
                } else {
                    decisionWidget.classList.add('wait');
                    decisionIcon.setAttribute('data-lucide', 'clock');
                }

                decisionTitle.textContent = result.decision;
                decisionReason.textContent = result.reason;
                decisionPrice.textContent = result.current_price ? '₹' + result.current_price.toLocaleString() : 'N/A';
                decisionRatio.textContent = Math.round(result.positive_ratio * 100) + '%';
                
                // Render Chart
                renderSentimentChart(result.sentiment_distribution);

                decisionResults.classList.remove('hidden');
                lucide.createIcons();
            } else {
                alert('Analysis failed: ' + (result.detail || 'Unknown error'));
            }
        } catch (err) {
            alert('Analysis error: ' + err.message);
        }

        decisionLoading.classList.add('hidden');
        runDecisionBtn.disabled = false;
    });

    function renderSentimentChart(dist) {
        const ctx = document.getElementById('sentiment-chart').getContext('2d');
        if (sentimentChart) sentimentChart.destroy();

        sentimentChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    data: [dist.Positive, dist.Neutral, dist.Negative],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',  // Green
                        'rgba(245, 158, 11, 0.8)',  // Amber/Yellow
                        'rgba(239, 68, 68, 0.8)'    // Red
                    ],
                    borderColor: 'var(--bg-card)',
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#e5e7eb', font: { family: 'Inter', size: 12 }, padding: 20 }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(20, 20, 29, 0.95)',
                        titleColor: '#f8f9fa',
                        bodyColor: '#a0a0b0',
                        borderColor: 'rgba(99, 102, 241, 0.3)',
                        borderWidth: 1,
                        padding: 12,
                        bodyFont: { family: 'Inter', size: 14, weight: '600' }
                    }
                }
            }
        });
    }

    subscribeBtn.addEventListener('click', async () => {
        const email = alertEmail.value;
        const product_name = decisionProductSelect.value;
        
        if (!email || !email.includes('@')) {
            alert('Please enter a valid email address.');
            return;
        }
        if (!product_name) {
            alert('Please select a product.');
            return;
        }

        subscribeBtn.disabled = true;
        subscribeStatus.classList.add('hidden');

        try {
            const res = await fetch('/api/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, product_name })
            });
            const result = await res.json();

            subscribeStatus.classList.remove('hidden');
            if (result.success) {
                subscribeStatus.className = 'status-msg status-success';
                subscribeStatus.textContent = result.message;
                alertEmail.value = '';
            } else {
                subscribeStatus.className = 'status-msg status-error';
                subscribeStatus.textContent = 'Failed to subscribe.';
            }
        } catch (err) {
            subscribeStatus.classList.remove('hidden');
            subscribeStatus.className = 'status-msg status-error';
            subscribeStatus.textContent = 'Network error.';
        }

        subscribeBtn.disabled = false;
    });

    // ── Sentiment Analyzer ────────────────────────────────────
    runSentimentBtn.addEventListener('click', async () => {
        const product_name = sentimentProductSelect.value;
        if (!product_name) return alert('Please select a product first.');

        runSentimentBtn.disabled = true;
        sentimentLoading.classList.remove('hidden');
        sentimentResults.classList.add('hidden');

        try {
            const res = await fetch('/api/sentiment/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_name })
            });
            const data = await res.json();

            if (data.success) {
                sentimentTotalCount.textContent = `(Analyzed ${data.total_analyzed} reviews)`;
                
                // Render Pie Chart
                renderStandaloneSentimentChart(data.sentiment_distribution);
                
                // Render Bar Chart
                renderCategoryChart(data.category_distribution);
                
                // Render Sample Table
                sentimentSamplesBody.innerHTML = '';
                data.sample_reviews.forEach(r => {
                    const tr = document.createElement('tr');
                    let color = 'var(--text-main)';
                    if(r.sentiment === 'Positive') color = 'var(--success-color)';
                    if(r.sentiment === 'Negative') color = 'var(--danger-color)';
                    if(r.sentiment === 'Neutral') color = 'var(--warning-color)';
                    
                    tr.innerHTML = `
                        <td style="color: ${color}; font-weight: 600;">${r.sentiment}</td>
                        <td><span class="badge" style="background: rgba(99, 102, 241, 0.1); color: var(--accent-primary); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem;">${r.category}</span></td>
                        <td style="font-size: 0.9rem; max-width: 400px; white-space: normal; line-height: 1.4;">${r.review_text.slice(0, 150)}${r.review_text.length > 150 ? '...' : ''}</td>
                    `;
                    sentimentSamplesBody.appendChild(tr);
                });

                sentimentResults.classList.remove('hidden');
            } else {
                alert('Analysis failed: ' + (data.detail || 'Unknown error'));
            }
        } catch(err) {
            alert('Error during upload: ' + err.message);
        }

        sentimentLoading.classList.add('hidden');
        runSentimentBtn.disabled = false;
    });

    function renderStandaloneSentimentChart(dist) {
        const ctx = document.getElementById('standalone-sentiment-chart').getContext('2d');
        if (standaloneSentimentChart) standaloneSentimentChart.destroy();

        standaloneSentimentChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    data: [dist.Positive, dist.Neutral, dist.Negative],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderColor: 'var(--bg-card)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#e5e7eb' } }
                }
            }
        });
    }

    function renderCategoryChart(catDist) {
        const ctx = document.getElementById('category-bar-chart').getContext('2d');
        if (categoryBarChart) categoryBarChart.destroy();

        const labels = Object.keys(catDist);
        const data = Object.values(catDist);

        categoryBarChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Number of Reviews',
                    data: data,
                    backgroundColor: 'rgba(99, 102, 241, 0.7)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#a0a0b0', stepSize: 1 } },
                    x: { grid: { display: false }, ticks: { color: '#a0a0b0' } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // ── Flipkart Scraper Logic ────────────────────────────────
    function loadScraperTab(tabId) {
        const config = tabConfigs[tabId];
        formTitle.textContent = config.title;
        formDesc.textContent = config.desc;
        dynamicInputs.innerHTML = config.inputs;
        statusContainer.classList.add('hidden');
        lucide.createIcons();
    }

    scraperForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const config = tabConfigs[currentTab];
        if (!config) return;

        let payload = {};
        if (currentTab === 'flipkart-price') {
            payload = { url: document.getElementById('url-input').value };
        } else if (currentTab === 'flipkart-reviews') {
            payload = { query: document.getElementById('query-input').value };
        }

        showScraperStatus('Initializing scraper...', true);

        try {
            const response = await fetch(config.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (result.success) {
                const count = result.data ? result.data.length : 0;
                showScraperStatus(`✅ Success! Collected ${count} data points.`, false);
                statusText.classList.add('success-text');
                setTimeout(() => {
                    document.querySelector('[data-tab="database"]').click();
                }, 2000);
            } else {
                showScraperStatus(`❌ Error: ${result.error}`, false);
                statusText.classList.add('error-text');
            }
        } catch (error) {
            showScraperStatus(`❌ Server Error: ${error.message}`, false);
            statusText.classList.add('error-text');
        }
    });

    function showScraperStatus(text, isLoading) {
        statusContainer.classList.remove('hidden');
        statusText.textContent = text;
        statusText.className = '';
        if (isLoading) {
            statusSpinner.style.display = 'block';
            document.querySelector('.status-subtext').style.display = 'block';
        } else {
            statusSpinner.style.display = 'none';
            document.querySelector('.status-subtext').style.display = 'none';
        }
    }

    // ── Database / Table Logic ────────────────────────────────
    async function fetchData() {
        dataTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4">Loading data from backend...</td></tr>';
        try {
            const response = await fetch('/api/data');
            const data = await response.json();
            if (data.success && data.data && data.data.length > 0) {
                renderTable(data.data.slice().reverse());
            } else {
                dataTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No data found. Run a scraper first.</td></tr>';
            }
        } catch (error) {
            dataTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 error-text">Error loading data: ${error.message}</td></tr>`;
        }
    }

    function renderTable(dataArray) {
        dataTableBody.innerHTML = '';
        const previewData = dataArray.slice(0, 100);

        previewData.forEach(row => {
            const tr = document.createElement('tr');
            let niceDate = row.timestamp;
            try { if (row.timestamp) niceDate = new Date(row.timestamp).toLocaleString(); } catch {}

            let badgeClass = 'badge-flipkart';
            let sourceLabel = (row.source || 'unknown').replace(/_/g, ' ');

            let ratingPrice = '-';
            if (row.price !== null && row.price !== undefined) {
                ratingPrice = `<span style="color:#10b981; font-weight:600">₹${row.price}</span>`;
            } else if (row.rating) {
                ratingPrice = '★ ' + row.rating;
            }

            let reviewContent = '-';
            if (row.review_text) {
                reviewContent = `<div class="review-cell" title="${row.review_text.replace(/"/g, '&quot;')}">${row.review_text}</div>`;
            } else if (row.url) {
                reviewContent = `<a href="${row.url}" target="_blank" style="color:var(--accent-primary);text-decoration:none" class="truncate d-block" style="max-width:200px">${row.url}</a>`;
            }

            tr.innerHTML = `
                <td>${niceDate}</td>
                <td><span class="badge ${badgeClass}">${sourceLabel}</span></td>
                <td class="truncate" title="${row.product_name}">${row.product_name || 'N/A'}</td>
                <td>${ratingPrice}</td>
                <td>${reviewContent}</td>
            `;
            dataTableBody.appendChild(tr);
        });

        if (dataArray.length > 100) {
            const t = document.createElement('tr');
            t.innerHTML = `<td colspan="5" class="text-center text-muted" style="padding:1rem">+ ${dataArray.length - 100} more rows hidden in preview. Download CSV to export full dataset.</td>`;
            dataTableBody.appendChild(t);
        }
    }

    refreshBtn.addEventListener('click', fetchData);
    downloadBtn.addEventListener('click', () => {
        window.location.href = '/data/raw_data.csv';
    });

    // Init
    currentTab = 'forecast';
    showSection('forecast');
    document.getElementById('nav-forecast').classList.add('active');
    document.getElementById('current-tab-name').textContent = 'Price Forecast';
});
