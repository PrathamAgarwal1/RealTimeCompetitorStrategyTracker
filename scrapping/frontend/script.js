document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentTab = 'amazon-price';

    // DOM Elements
    const navItems = document.querySelectorAll('.nav-item');
    const scraperSection = document.getElementById('scraper-section');
    const dataSection = document.getElementById('data-section');
    
    const formTitle = document.getElementById('form-title');
    const formDesc = document.getElementById('form-desc');
    const dynamicInputs = document.getElementById('dynamic-inputs');
    const scraperForm = document.getElementById('scraper-form');
    
    const statusContainer = document.getElementById('status-container');
    const statusText = document.getElementById('status-text');
    const statusSpinner = document.querySelector('.spinner');
    
    const dataTableBody = document.getElementById('data-table-body');
    const refreshBtn = document.getElementById('refresh-db-btn');
    const downloadBtn = document.getElementById('download-csv-btn');
    const currentTabName = document.getElementById('current-tab-name');

    // Tab Configuration
    const tabConfigs = {
        'amazon-price': {
            title: 'Amazon Price History Scraper',
            desc: 'Enter a PriceHistoryApp URL for an Amazon product to scrape historical pricing data.',
            endpoint: '/api/scrape/amazon-price',
            inputs: `
                <label for="url-input">PriceHistoryApp URL</label>
                <input type="url" id="url-input" placeholder="https://pricehistoryapp.com/product/..." required>
                <a href="https://pricehistoryapp.com/" target="_blank" style="color: var(--accent-primary); font-size: 0.8rem; text-decoration: none; display: inline-block; margin-top: 0.25rem;">
                    <i data-lucide="external-link" style="width: 12px; height: 12px; vertical-align: middle;"></i> Find Amazon products on PriceHistoryApp
                </a>
            `
        },
        'flipkart-price': {
            title: 'Flipkart Price History Scraper',
            desc: 'Enter a PriceHistory.app URL for a Flipkart product to decipher and extract JSON pricing data.',
            endpoint: '/api/scrape/flipkart-price',
            inputs: `
                <label for="url-input">PriceHistory.app URL</label>
                <input type="url" id="url-input" placeholder="https://pricehistory.app/p/..." required>
                <a href="https://pricehistory.app/" target="_blank" style="color: var(--accent-primary); font-size: 0.8rem; text-decoration: none; display: inline-block; margin-top: 0.25rem;">
                    <i data-lucide="external-link" style="width: 12px; height: 12px; vertical-align: middle;"></i> Find Flipkart products on PriceHistory.app
                </a>
            `
        },
        'amazon-reviews': {
            title: 'Amazon Reviews Scraper',
            desc: 'Enter a 10-character Amazon ASIN to scrape up to 100 reviews.',
            endpoint: '/api/scrape/amazon-reviews',
            inputs: `
                <div class="auth-box" style="margin-bottom: 1.5rem; padding: 1.25rem; background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 8px;">
                    <p style="font-size: 0.95rem; color: var(--text-main); margin-bottom: 0.5rem; font-weight: 600;">
                        <i data-lucide="shield-alert" style="width:16px;height:16px;vertical-align:text-bottom;color:var(--accent-primary);"></i> Amazon Authentication Required
                    </p>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem; line-height: 1.4;">Amazon blocks automated review scrapers. You must establish a logged-in session first. Click "Open Login Browser" below, manually log into your Amazon account in the new window, and then click "Save Cookies".</p>
                    <div style="display: flex; gap: 0.75rem; align-items: center;">
                        <button type="button" id="auth-start-btn" class="btn btn-outline" style="font-size: 0.85rem; padding: 0.6rem 1rem;">1. Open Login Browser</button>
                        <button type="button" id="auth-save-btn" class="btn btn-primary" style="font-size: 0.85rem; padding: 0.6rem 1rem;" disabled>2. Save Cookies & Close</button>
                    </div>
                    <span id="auth-msg" style="font-size: 0.85rem; display: block; margin-top: 0.75rem; font-weight: 500;"></span>
                </div>

                <label for="asin-input">Amazon ASIN</label>
                <input type="text" id="asin-input" placeholder="e.g. B0CHX2F5QT" minlength="10" maxlength="10" required>
                <a href="https://www.amazon.in/" target="_blank" style="color: var(--accent-primary); font-size: 0.8rem; text-decoration: none; display: inline-block; margin-top: 0.25rem;">
                    <i data-lucide="external-link" style="width: 12px; height: 12px; vertical-align: middle;"></i> Find ASIN on Amazon.in (look in the URL for /dp/ASIN)
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

    // Navigation Logic
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            currentTabName.textContent = item.textContent.trim();

            if (tabId === 'database') {
                scraperSection.classList.add('hidden');
                dataSection.classList.remove('hidden');
                fetchData();
            } else {
                currentTab = tabId;
                scraperSection.classList.remove('hidden');
                dataSection.classList.add('hidden');
                loadTabConfig(tabId);
            }
        });
    });

    function loadTabConfig(tabId) {
        const config = tabConfigs[tabId];
        formTitle.textContent = config.title;
        formDesc.textContent = config.desc;
        dynamicInputs.innerHTML = config.inputs;
        hideStatus();

        if (tabId === 'amazon-reviews') {
            setupAmazonAuth();
        }
    }

    function setupAmazonAuth() {
        const startBtn = document.getElementById('auth-start-btn');
        const saveBtn = document.getElementById('auth-save-btn');
        const msg = document.getElementById('auth-msg');

        if (!startBtn || !saveBtn) return;

        startBtn.addEventListener('click', async () => {
             startBtn.disabled = true;
             msg.textContent = 'Launching browser...';
             msg.style.color = 'var(--text-main)';
             try {
                 const res = await fetch('/api/amazon-auth/start');
                 const data = await res.json();
                 if (data.success) {
                      msg.textContent = 'Browser opened! Please log in, then click Save Cookies & Close.';
                      msg.style.color = '#10b981'; 
                      startBtn.disabled = false;
                      saveBtn.disabled = false;
                 } else {
                      msg.textContent = 'Error: ' + data.error;
                      msg.style.color = '#ef4444'; 
                      startBtn.disabled = false;
                 }
             } catch (err) {
                 msg.textContent = 'Network error: ' + err.message;
                 msg.style.color = '#ef4444';
                 startBtn.disabled = false;
             }
        });

        saveBtn.addEventListener('click', async () => {
             saveBtn.disabled = true;
             msg.textContent = 'Saving cookies...';
             msg.style.color = 'var(--text-main)';
             try {
                 const res = await fetch('/api/amazon-auth/save', { method: 'POST' });
                 const data = await res.json();
                 if (data.success) {
                      msg.textContent = '✅ Cookies saved! You can now run the scraper.';
                      msg.style.color = '#10b981';
                      saveBtn.disabled = true;
                 } else {
                      msg.textContent = 'Error: ' + data.error;
                      msg.style.color = '#ef4444';
                      saveBtn.disabled = false;
                 }
             } catch (err) {
                 msg.textContent = 'Network error: ' + err.message;
                 msg.style.color = '#ef4444';
                 saveBtn.disabled = false;
             }
        });
    }

    // Form Submission Logic
    scraperForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const config = tabConfigs[currentTab];
        let payload = {};

        // Build Payload
        if (currentTab === 'amazon-price' || currentTab === 'flipkart-price') {
            payload = { url: document.getElementById('url-input').value };
        } else if (currentTab === 'amazon-reviews') {
            payload = { asin: document.getElementById('asin-input').value };
        } else if (currentTab === 'flipkart-reviews') {
            payload = { query: document.getElementById('query-input').value };
        }

        showStatus('Initializing targeted scraper...', true);

        try {
            const response = await fetch(config.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success) {
                const count = result.data ? result.data.length : 0;
                showStatus(`✅ Success! Collected and saved ${count} data points.`, false);
                statusText.classList.add('success-text');
                statusText.classList.remove('error-text');
                
                // Switch to Database View after 2 seconds
                setTimeout(() => {
                    const dbTab = document.querySelector('[data-tab="database"]');
                    dbTab.click();
                }, 2000);
            } else {
                showStatus(`❌ Error: ${result.error}`, false);
                statusText.classList.add('error-text');
                statusText.classList.remove('success-text');
            }
        } catch (error) {
            showStatus(`❌ Server Error: ${error.message}`, false);
            statusText.classList.add('error-text');
            statusText.classList.remove('success-text');
        }
    });

    // UI Helpers
    function showStatus(text, isLoading) {
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

    function hideStatus() {
        statusContainer.classList.add('hidden');
    }

    // Database / Table Logic
    async function fetchData() {
        dataTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4">Loading data from backend...</td></tr>';
        
        try {
            const response = await fetch('/api/data');
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                renderTable(data.data.slice().reverse()); // Show newest first
            } else {
                dataTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No data found. Run a scraper first.</td></tr>';
            }
        } catch (error) {
            dataTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 error-text">Error loading data: ${error.message}</td></tr>`;
        }
    }

    function renderTable(dataArray) {
        dataTableBody.innerHTML = '';
        
        // Show max 100 rows in preview for performance
        const previewData = dataArray.slice(0, 100);

        previewData.forEach(row => {
            const tr = document.createElement('tr');
            
            // Format nice date if possible
            let niceDate = row.timestamp;
            try {
                if (row.timestamp) niceDate = new Date(row.timestamp).toLocaleString();
            } catch(e) {}

            // Format Badge 
            let badgeClass = 'badge-amazon';
            if (row.source && row.source.includes('flipkart')) badgeClass = 'badge-flipkart';
            let sourceLabel = (row.source || 'unknown').replace(/_/g, ' ');

            // Secondary column info logic
            let ratingPrice = '-';
            if (row.price !== null && row.price !== undefined) {
                ratingPrice = '<span style="color:#10b981; font-weight:600">₹' + row.price + '</span>';
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

    // Init first tab view
    loadTabConfig('amazon-price');
});
