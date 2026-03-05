document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const grid = document.getElementById('news-grid');
    const loader = document.getElementById('loader');
    const errorContainer = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const statusBar = document.getElementById('status-bar');
    const navItems = document.querySelectorAll('.nav-item');
    const datePicker = document.getElementById('date-picker');
    const clearDateBtn = document.getElementById('clear-date');

    // State
    let allNews = [];
    let currentCategory = 'All';
    let currentDate = null;

    // Set Max Date for Datepicker
    const today = new Date().toISOString().split('T')[0];
    datePicker.max = today;

    // Initialize
    fetchNews();

    // Event Listeners
    navItems.forEach(btn => {
        btn.addEventListener('click', (e) => {
            navItems.forEach(n => n.classList.remove('active'));
            e.target.classList.add('active');
            currentCategory = e.target.getAttribute('data-category');
            renderNews();
        });
    });

    datePicker.addEventListener('change', (e) => {
        currentDate = e.target.value; // YYYY-MM-DD
        renderNews();
    });

    clearDateBtn.addEventListener('click', () => {
        datePicker.value = '';
        currentDate = null;
        renderNews();
    });

    // API Fetch
    async function fetchNews() {
        showLoader();
        try {
            // Note: In development with a local server, adjust URL if needed
            // But if running locally via Vercel CLI or deployed to Vercel, relative path works
            const response = await fetch('/api/news');
            if (!response.ok) {
                const errJson = await response.json();
                throw new Error(errJson.detail || 'Network response was not ok');
            }
            const data = await response.json();
            
            if (data.status === 'success') {
                allNews = data.data;
                renderNews();
            } else {
                throw new Error("Unexpected API response structure.");
            }
        } catch (error) {
            console.error("Fetch error: ", error);
            showError(`Failed to fetch news. Please ensure Google Sheets credentials are correct. (${error.message})`);
        }
    }

    // Render Logic
    function renderNews() {
        if (!allNews || allNews.length === 0) {
            showError("No news data available.");
            updateStatus(0);
            return;
        }

        // Apply filters
        let filtered = [...allNews];

        // 1. Filter by Category
        if (currentCategory !== 'All') {
            filtered = filtered.filter(news => {
                if (!news.Source) return false;
                return news.Source.toLowerCase().includes(currentCategory.toLowerCase());
            });
        }

        // 2. Filter by Date (Soft fallback to nearest date like Streamlit app)
        if (currentDate) {
            // First, try exact match
            const exactMatches = filtered.filter(news => {
                if (!news.Date) return false;
                return news.Date.startsWith(currentDate);
            });

            if (exactMatches.length > 0) {
                filtered = exactMatches;
            } else {
                // If no exact match, find nearest available date in the dataset
                const allAvailableDates = [...new Set(filtered.map(n => n.Date ? n.Date.split(' ')[0] : null).filter(Boolean))];
                
                if (allAvailableDates.length > 0) {
                    const targetTime = new Date(currentDate).getTime();
                    let closestDate = allAvailableDates[0];
                    let minDiff = Math.abs(new Date(closestDate).getTime() - targetTime);

                    for (let i = 1; i < allAvailableDates.length; i++) {
                        const diff = Math.abs(new Date(allAvailableDates[i]).getTime() - targetTime);
                        if (diff < minDiff) {
                            minDiff = diff;
                            closestDate = allAvailableDates[i];
                        }
                    }

                    filtered = filtered.filter(news => news.Date && news.Date.startsWith(closestDate));
                    
                    // Show warning that we matched to a different date
                    const daysAway = Math.floor(minDiff / (1000 * 3600 * 24));
                    statusBar.innerHTML = `<span style="color:var(--accent-primary)"><i class="ph ph-info"></i> No news for <b>${currentDate}</b>. Showing nearest available date: <b>${closestDate}</b> (${daysAway} days away).</span> <br/>`;
                } else {
                    filtered = [];
                }
            }
        }

        // Display results
        hideLoader();
        grid.innerHTML = '';
        
        if (filtered.length === 0) {
            grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-tertiary); padding: 40px 0;">No articles match your current filters.</div>`;
        } else {
            filtered.forEach((news, index) => {
                const card = createNewsCard(news, index);
                grid.appendChild(card);
            });
        }

        if(!statusBar.innerHTML.includes("info")) {
            updateStatus(filtered.length);
        } else {
            // retain warning and add status
            statusBar.innerHTML += `<br/>Showing <strong>${filtered.length}</strong> articles`;
        }
    }

    // Creating HTML Card
    function createNewsCard(news, index) {
        const div = document.createElement('div');
        div.className = 'news-card';
        div.style.animationDelay = `${(index % 10) * 0.05}s`;

        // Clean source tag
        const safeSource = news.Source || 'Unknown Source';
        let categoryTag = safeSource;
        if (safeSource.includes('(')) {
            categoryTag = safeSource.split('(')[1].replace(')', '');
        }

        const dateStr = news.Date ? news.Date.split(' ')[0] : 'Unknown Date';
        const formattedDate = new Date(dateStr).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });

        div.innerHTML = `
            <div class="news-card-category">${categoryTag}</div>
            <h3 class="news-card-title">
                <a href="${news.URL}" target="_blank" rel="noopener noreferrer">${news.Title || 'Untitled'}</a>
            </h3>
            <div class="news-card-meta">
                <i class="ph ph-clock"></i>
                <span>${safeSource.split('(')[0]} &nbsp;&bull;&nbsp; ${formattedDate}</span>
            </div>
            <p class="news-card-desc">${news.Description || 'No description available for this article.'}</p>
            <div class="news-card-footer">
                <a href="${news.URL}" class="read-more" target="_blank" rel="noopener noreferrer">
                    Read Story <i class="ph ph-arrow-right"></i>
                </a>
            </div>
        `;
        return div;
    }

    // UI Helpers
    function showLoader() {
        loader.style.display = 'flex';
        grid.style.display = 'none';
        errorContainer.style.display = 'none';
        statusBar.innerHTML = 'Loading news...';
    }

    function hideLoader() {
        loader.style.display = 'none';
        grid.style.display = 'grid';
    }

    function showError(msg) {
        hideLoader();
        grid.style.display = 'none';
        errorContainer.style.display = 'block';
        errorText.innerText = msg;
        statusBar.innerHTML = 'Error loading news.';
    }

    function updateStatus(count) {
        const catLabel = currentCategory === 'All' ? 'All Categories' : currentCategory;
        const dateLabel = currentDate ? new Date(currentDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : 'All Dates';
        
        statusBar.innerHTML = `Showing <strong>${count}</strong> articles &bull; <strong>${catLabel}</strong> &bull; ${dateLabel}`;
    }
});
