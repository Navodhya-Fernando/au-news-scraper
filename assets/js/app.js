// Global state
let allArticles = [];
let filteredArticles = [];
let currentCategory = 'all';
let currentSort = 'date-desc';
let lastUpdatedText = null;

document.addEventListener('DOMContentLoaded', () => {
    const feedContainer = document.getElementById('feed-container');
    const searchInput = document.getElementById('search-input');
    const filterGroup = document.getElementById('filter-group');
    const sortSelect = document.getElementById('sort-select');
    const refreshBtn = document.getElementById('refresh-btn');
    const refreshStatus = document.getElementById('refresh-status');

    // Fetch articles
    function loadArticles(showLoading = true) {
        if (showLoading) setLoading(true);

        Promise.all([
            fetch(`data/articles.json?ts=${Date.now()}`),
            fetch(`data/meta.json?ts=${Date.now()}`)
        ])
            .then(response => {
                const [articlesRes, metaRes] = response;
                if (!articlesRes.ok) throw new Error('Network response was not ok');
                return Promise.all([
                    articlesRes.json(),
                    metaRes.ok ? metaRes.json() : Promise.resolve(null)
                ]);
            })
            .then(([articles, meta]) => {
                allArticles = articles;
                filteredArticles = articles;

                if (meta && meta.last_updated) {
                    const updated = new Date(meta.last_updated);
                    const timeString = updated.toLocaleTimeString('en-AU', {
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true
                    });
                    lastUpdatedText = `Last updated: ${timeString}`;
                    document.getElementById('last-updated').textContent = lastUpdatedText;
                }

                if (articles.length === 0) {
                    feedContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📭</div>
                            <h3>No articles found</h3>
                            <p>The scraper may be running. Check back soon!</p>
                        </div>`;
                    setLoading(false);
                    return;
                }

                setupFilters(articles);
                currentSort = sortSelect ? sortSelect.value : currentSort;
                applySortAndRender();
                updateStats();
                setLoading(false);
            })
            .catch(error => {
                console.error('Error loading articles:', error);
                feedContainer.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <h3>Unable to load intelligence feed</h3>
                        <p>Please verify the data source and try again.</p>
                    </div>`;
                setLoading(false);
            });
    }

    function setLoading(isLoading) {
        if (refreshBtn) {
            refreshBtn.disabled = isLoading;
            refreshBtn.classList.toggle('loading', isLoading);
        }
        if (refreshStatus) {
            refreshStatus.textContent = isLoading ? 'Fetching latest articles…' : '';
        }
    }

    // Setup filter buttons
    function setupFilters(articles) {
        const categories = ['all', ...new Set(articles.map(a => a.keyword_category || 'Uncategorized'))];
        
        filterGroup.innerHTML = categories.map(cat => `
            <button class="filter-btn ${cat === 'all' ? 'active' : ''}" data-category="${cat}">
                ${cat === 'all' ? 'All' : cat}
            </button>
        `).join('');
        
        // Add click handlers
        filterGroup.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', handleFilter);
        });
    }

    // Handle search
    function handleSearch(e) {
        const query = e.target.value.toLowerCase().trim();
        
        if (query === '') {
            // If search is empty, apply category filter only
            filteredArticles = currentCategory === 'all' 
                ? allArticles 
                : allArticles.filter(a => (a.keyword_category || 'Uncategorized') === currentCategory);
        } else {
            // Filter by search query AND category
            let articlesToSearch = currentCategory === 'all' 
                ? allArticles 
                : allArticles.filter(a => (a.keyword_category || 'Uncategorized') === currentCategory);
            
            filteredArticles = articlesToSearch.filter(article => {
                const headline = article.headline.toLowerCase();
                const source = article.source.toLowerCase();
                const category = (article.keyword_category || '').toLowerCase();
                
                return headline.includes(query) || source.includes(query) || category.includes(query);
            });
        }
        
        applySortAndRender();
        updateStats();
    }

    // Handle filter
    function handleFilter(e) {
        const btn = e.target;
        const category = btn.dataset.category;
        
        // Update active state
        filterGroup.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        currentCategory = category;
        
        // Apply filter
        const searchQuery = searchInput.value.toLowerCase().trim();
        
        if (category === 'all') {
            filteredArticles = allArticles;
        } else {
            filteredArticles = allArticles.filter(a => (a.keyword_category || 'Uncategorized') === category);
        }
        
        // Re-apply search if active
        if (searchQuery !== '') {
            filteredArticles = filteredArticles.filter(article => {
                const headline = article.headline.toLowerCase();
                const source = article.source.toLowerCase();
                const cat = (article.keyword_category || '').toLowerCase();
                
                return headline.includes(searchQuery) || source.includes(searchQuery) || cat.includes(searchQuery);
            });
        }
        
        applySortAndRender();
        updateStats();
    }

    function applySortAndRender() {
        const sortedArticles = applySort(filteredArticles, currentSort);
        filteredArticles = sortedArticles;
        renderArticles(sortedArticles);
    }

    // Render articles to DOM
    function renderArticles(articles) {
        feedContainer.innerHTML = '';

        if (articles.length === 0) {
            feedContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <h3>No articles match your search</h3>
                    <p>Try adjusting your filters or search query.</p>
                </div>`;
            return;
        }

        articles.forEach(article => {
            const categoryLabel = article.keyword_category || 'Migration Update';
            const iconSvg = getCategoryIcon(categoryLabel);
            const cardLink = document.createElement('a');
            
            // Only add 'no-image' class if there's no preview_image or it's empty
            const hasImage = article.preview_image && article.preview_image.trim() !== '';
            cardLink.className = hasImage ? 'card' : 'card no-image';
            cardLink.href = article.url;
            cardLink.target = '_blank';
            cardLink.rel = 'noopener noreferrer';
            
            // Debug log
            console.log(`Article: ${article.headline.substring(0, 50)}... | Has Image: ${hasImage} | Image: ${article.preview_image ? article.preview_image.substring(0, 60) : 'NONE'}`);
            
            // Build the HTML with or without image
            let imageHTML = '';
            if (hasImage) {
                imageHTML = `
                    <div class="card-image-wrapper">
                        <img src="${article.preview_image}" alt="${article.headline}" class="card-img" onerror="this.style.display='none'">
                        <span class="category-badge">
                            <span class="category-icon">${iconSvg}</span>
                            ${categoryLabel}
                        </span>
                    </div>
                `;
            }
            
            cardLink.innerHTML = `
                ${imageHTML}
                <div class="card-content">
                    ${!hasImage ? `
                        <span class="category-badge inline">
                            <span class="category-icon">${iconSvg}</span>
                            ${categoryLabel}
                        </span>
                    ` : ''}
                    <div class="card-meta">
                        <span>${article.source.replace(' (via Google News)', '')}</span>
                        <span>•</span>
                        <span>${article.date}</span>
                    </div>
                    <h2 class="card-title">${article.headline}</h2>
                    <div class="card-footer">Read Full Briefing</div>
                </div>
            `;
            
            feedContainer.appendChild(cardLink);
        });
    }

    // Update statistics
    function updateStats() {
        document.getElementById('visible-count').textContent = filteredArticles.length;
        document.getElementById('total-count').textContent = allArticles.length;
        
        if (lastUpdatedText) {
            document.getElementById('last-updated').textContent = lastUpdatedText;
        }
    }

    function getSortDate(article) {
        const value = article.date_time || article.date || '';
        const parsed = new Date(value);
        return isNaN(parsed) ? new Date(0) : parsed;
    }

    function applySort(list, sortValue) {
        const sorted = [...list];
        switch(sortValue) {
            case 'date-desc':
                sorted.sort((a, b) => {
                    const diff = getSortDate(b) - getSortDate(a);
                    if (diff !== 0) return diff;
                    return (b.headline || '').localeCompare(a.headline || '');
                });
                break;
            case 'date-asc':
                sorted.sort((a, b) => {
                    const diff = getSortDate(a) - getSortDate(b);
                    if (diff !== 0) return diff;
                    return (a.headline || '').localeCompare(b.headline || '');
                });
                break;
            case 'source':
                sorted.sort((a, b) => (a.source || '').localeCompare(b.source || ''));
                break;
            case 'category':
                sorted.sort((a, b) => (a.keyword_category || '').localeCompare(b.keyword_category || ''));
                break;
        }
        return sorted;
    }

    function getCategoryIcon(category) {
        const key = category.toLowerCase();
        if (key.includes('visa') || key.includes('migration')) {
            return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16v12H4z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 6V4h8v2" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="9" cy="12" r="1.5" fill="currentColor"/><path d="M13 11h5v2h-5z" fill="currentColor"/></svg>`;
        }
        if (key.includes('job') || key.includes('employment')) {
            return `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="7" width="16" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M9 7V5h6v2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M4 11h16" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>`;
        }
        if (key.includes('training') || key.includes('education')) {
            return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8l9-4 9 4-9 4-9-4z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M7 12v4c0 1.1 2.2 2 5 2s5-.9 5-2v-4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>`;
        }
        if (key.includes('policy') || key.includes('government')) {
            return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10h16v9H4z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M3 10l9-6 9 6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M9 19v-5h6v5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>`;
        }
        if (key.includes('industry') || key.includes('economy') || key.includes('market')) {
            return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M4 19h16" fill="none" stroke="currentColor" stroke-width="1.6"/><rect x="7" y="12" width="3" height="5" fill="currentColor"/><rect x="12" y="9" width="3" height="8" fill="currentColor"/><rect x="17" y="6" width="3" height="11" fill="currentColor"/></svg>`;
        }
        return `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 7v6l4 2" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>`;
    }

    function handleSort() {
        currentSort = sortSelect.value;
        applySortAndRender();
    }

    async function handleRefresh() {
        if (refreshBtn.disabled) return;
        
        setLoading(true);
        
        // Show progress bar
        const progressBar = document.getElementById('progress-bar');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const progressEta = document.getElementById('progress-eta');
        
        progressBar.style.display = 'block';
        refreshStatus.textContent = 'Starting scraper...';
        progressFill.style.width = '0%';
        progressText.textContent = '0%';
        progressEta.textContent = '';
        
        let progressInterval = null;
        
        try {
            const response = await fetch('https://web-production-32676.up.railway.app/api/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Start polling for progress
                progressInterval = setInterval(async () => {
                    try {
                        const progressResponse = await fetch('https://web-production-32676.up.railway.app/api/progress');
                        const progress = await progressResponse.json();
                        
                        // Update progress bar
                        progressFill.style.width = `${progress.percentage}%`;
                        progressText.textContent = `${progress.percentage}%`;
                        
                        // Update ETA
                        if (progress.eta_seconds > 0) {
                            const minutes = Math.floor(progress.eta_seconds / 60);
                            const seconds = progress.eta_seconds % 60;
                            if (minutes > 0) {
                                progressEta.textContent = `ETA: ${minutes}m ${seconds}s`;
                            } else {
                                progressEta.textContent = `ETA: ${seconds}s`;
                            }
                        } else {
                            progressEta.textContent = '';
                        }
                        
                        // Update status message
                        if (progress.message) {
                            refreshStatus.textContent = progress.message;
                        }
                        
                        // Check if completed
                        if (!progress.running && progress.current >= progress.total) {
                            clearInterval(progressInterval);
                            progressInterval = null;
                            
                            refreshStatus.textContent = `✓ Completed! Found ${progress.articles_found} new articles`;
                            progressFill.style.width = '100%';
                            progressText.textContent = '100%';
                            progressEta.textContent = '';
                            
                            // Reload articles after a short delay
                            setTimeout(() => {
                                loadArticles(false);
                                setLoading(false);
                                
                                // Hide progress bar after another delay
                                setTimeout(() => {
                                    progressBar.style.display = 'none';
                                    refreshStatus.textContent = '';
                                }, 3000);
                            }, 1000);
                            return;
                        }
                    } catch (pollError) {
                        console.error('Progress poll error:', pollError);
                    }
                }, 500); // Poll every 500ms
                
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('Scraper error:', error);
            refreshStatus.textContent = '✗ Failed to connect to scraper API.';
            setLoading(false);
            progressBar.style.display = 'none';
            
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
            
            setTimeout(() => {
                refreshStatus.textContent = '';
            }, 10000);
        }
    }

    // Wire up listeners
    searchInput.addEventListener('input', handleSearch);
    sortSelect.addEventListener('change', handleSort);
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleRefresh);
    }

    // Initial load
    loadArticles(false);
});