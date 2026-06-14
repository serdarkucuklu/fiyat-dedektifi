// State Variables
let allDeals = [];
let searchQuery = '';
let currentStore = 'all';

// DOM Elements
const lastUpdatedBadge = document.getElementById('last-updated');
const searchInput = document.getElementById('search-input');
const filterBtns = document.querySelectorAll('.store-filters .filter-btn');
const dealsFeed = document.getElementById('deals-feed');

// Lightbox Modal Elements
const imageModal = document.getElementById('image-modal');
const modalImg = document.getElementById('modal-img');
const modalCaption = document.getElementById('modal-caption');
const modalClose = document.getElementById('modal-close');

// Fetch and load database
async function loadData() {
    try {
        const response = await fetch('data.json');
        const data = await response.json();
        allDeals = data.deals || [];
        
        // Format last updated timestamp
        if (data.last_updated) {
            const date = new Date(data.last_updated);
            const formattedDate = date.toLocaleString('tr-TR', {
                day: 'numeric',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit'
            });
            lastUpdatedBadge.textContent = `Güncellendi: ${formattedDate}`;
        }
        
        render();
    } catch (err) {
        console.error('Error loading data.json:', err);
        lastUpdatedBadge.textContent = 'Veri Yüklenemedi';
    }
}

// Render filtered deals list
function render() {
    dealsFeed.innerHTML = '';
    
    const filtered = allDeals.filter(deal => {
        // 1. Text Search Filter
        const matchesSearch = 
            deal.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
            deal.description.toLowerCase().includes(searchQuery.toLowerCase());
            
        // 2. Store Source Filter
        const matchesStore = currentStore === 'all' || deal.source === currentStore;
        
        return matchesSearch && matchesStore;
    });
    
    if (filtered.length === 0) {
        dealsFeed.innerHTML = `
            <div class="no-deals-card">
                <i class="fa-solid fa-face-frown no-deals-icon"></i>
                <p>Aradığınız kriterlere uygun güncel fırsat bulunamadı.</p>
            </div>
        `;
        return;
    }
    
    filtered.forEach(deal => {
        const row = document.createElement('div');
        row.className = 'deal-row';
        
        // Sanitize and resolve empty / relative / 'N/A' affiliate links on the fly
        let link = (deal.affiliate_link || '').trim();
        if (!link || link.toUpperCase() === 'N/A' || link.toUpperCase() === 'NONE' || link.toUpperCase() === 'NULL') {
            const query = encodeURIComponent(deal.title);
            if (deal.source === 'Trendyol') {
                link = `https://www.trendyol.com/sr?q=${query}`;
            } else if (deal.source === 'Hepsiburada') {
                link = `https://www.hepsiburada.com/ara?q=${query}`;
            } else {
                link = `https://www.amazon.com.tr/s?k=${query}&tag=aurafocus-21`;
            }
        }
        
        const votes = getDealVotes(deal.title);
        const userVote = votes.userVote;

        row.innerHTML = `
            <div class="deal-img-container">
                <img src="${deal.image_url}" alt="${deal.title}" class="deal-img" loading="lazy" onerror="this.onerror=null; this.src=getFallbackProductImage('${deal.title}')">
                <span class="discount-badge">${deal.discount_rate}</span>
            </div>
            <div class="deal-info-col">
                <div class="deal-meta">
                    <span class="source-badge" data-source="${deal.source}">${deal.source}</span>
                </div>
                <h3 class="deal-title">${deal.title}</h3>
                <p class="deal-description">${deal.description}</p>
                <div class="deal-actions-row">
                    <div class="vote-group">
                        <button class="vote-btn hot-btn ${userVote === 'hot' ? 'active' : ''}" onclick="voteDeal('${escapeHtml(deal.title)}', 'hot')">
                            <i class="fa-solid fa-fire"></i> Sıcak <span class="hot-count">${votes.hot}</span>
                        </button>
                        <button class="vote-btn cold-btn ${userVote === 'cold' ? 'active' : ''}" onclick="voteDeal('${escapeHtml(deal.title)}', 'cold')">
                            <i class="fa-regular fa-snowflake"></i> Soğuk <span class="cold-count">${votes.cold}</span>
                        </button>
                    </div>
                    <button class="history-btn" onclick="showPriceHistory('${escapeHtml(deal.title)}')">
                        <i class="fa-solid fa-chart-line"></i> Fiyat Geçmişi
                    </button>
                </div>
            </div>
            <div class="deal-action-col">
                <div class="pricing-info">
                    <span class="orig-price">${deal.original_price}</span>
                    <span class="disc-price">${deal.discount_price}</span>
                </div>
                <a href="${link}" target="_blank" class="deal-btn">
                    Fırsatı Yakala <i class="fa-solid fa-arrow-up-right-from-square"></i>
                </a>
            </div>
        `;
        dealsFeed.appendChild(row);
    });
}

// Helper to provide beautiful fallback images if Unsplash URL fails to load
function getFallbackProductImage(title) {
    const lowercaseTitle = title.toLowerCase();
    
    // Guaranteed high-quality Unsplash product images
    if (lowercaseTitle.includes('kulaklık') || lowercaseTitle.includes('headphone') || lowercaseTitle.includes('ses') || lowercaseTitle.includes('hoparlör') || lowercaseTitle.includes('speaker')) {
        return 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=600&auto=format&fit=crop';
    }
    if (lowercaseTitle.includes('saat') || lowercaseTitle.includes('watch') || lowercaseTitle.includes('band') || lowercaseTitle.includes('bileklik')) {
        return 'https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?q=80&w=600&auto=format&fit=crop';
    }
    if (lowercaseTitle.includes('mutfak') || lowercaseTitle.includes('airfryer') || lowercaseTitle.includes('kahve') || lowercaseTitle.includes('tencere') || lowercaseTitle.includes('tava') || lowercaseTitle.includes('bardak') || lowercaseTitle.includes('termos')) {
        return 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?q=80&w=600&auto=format&fit=crop';
    }
    if (lowercaseTitle.includes('mouse') || lowercaseTitle.includes('klavye') || lowercaseTitle.includes('keyboard') || lowercaseTitle.includes('oyuncu') || lowercaseTitle.includes('gaming')) {
        return 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?q=80&w=600&auto=format&fit=crop';
    }
    if (lowercaseTitle.includes('süpürge') || lowercaseTitle.includes('dyson') || lowercaseTitle.includes('robot') || lowercaseTitle.includes('temizlik')) {
        return 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?q=80&w=600&auto=format&fit=crop';
    }
    // Default product image
    return 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=600&auto=format&fit=crop';
}


// Event Listener for Search Input
searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.trim();
    render();
});

// Event Listeners for Store Filters
filterBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        filterBtns.forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        currentStore = e.currentTarget.dataset.store;
        render();
    });
});

// Lightbox Modal Event Handlers
dealsFeed.addEventListener('click', (e) => {
    if (e.target.classList.contains('deal-img')) {
        const imgSrc = e.target.src;
        const imgAlt = e.target.alt;
        
        modalImg.src = imgSrc;
        modalImg.alt = imgAlt;
        modalCaption.textContent = imgAlt;
        
        imageModal.classList.add('active');
        document.body.style.overflow = 'hidden'; // Disable background scrolling
    }
});

function closeModal() {
    imageModal.classList.remove('active');
    document.body.style.overflow = ''; // Re-enable background scrolling
}

modalClose.addEventListener('click', closeModal);
imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal) {
        closeModal();
    }
});
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && imageModal.classList.contains('active')) {
        closeModal();
    }
});

// Voting helper methods
function getDealVotes(title) {
    const storageKey = `deal_votes_${title}`;
    let data = localStorage.getItem(storageKey);
    if (!data) {
        // Generate baseline votes
        const baseHot = Math.floor(Math.random() * 80) + 15;
        const baseCold = Math.floor(Math.random() * 10) + 1;
        const votesObj = { hot: baseHot, cold: baseCold, userVote: null };
        localStorage.setItem(storageKey, JSON.stringify(votesObj));
        return votesObj;
    }
    return JSON.parse(data);
}

function voteDeal(title, type) {
    const storageKey = `deal_votes_${title}`;
    const votesObj = getDealVotes(title);
    
    if (votesObj.userVote === type) {
        votesObj[type]--;
        votesObj.userVote = null;
    } else {
        if (votesObj.userVote) {
            votesObj[votesObj.userVote]--;
        }
        votesObj[type]++;
        votesObj.userVote = type;
    }
    localStorage.setItem(storageKey, JSON.stringify(votesObj));
    render();
}
window.voteDeal = voteDeal;

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

let priceChartInstance = null;

function showPriceHistory(title) {
    const deal = allDeals.find(d => d.title === title);
    if (!deal) return;
    
    const cleanPriceStr = (str) => {
        if (!str) return 0;
        let clean = str.replace(/[^\d]/g, '');
        if (str.includes(',')) {
            const parts = str.split(',');
            if (parts[1] && parts[1].replace(/[^\d]/g, '').length === 2) {
                return parseFloat(clean) / 100;
            }
        }
        return parseFloat(clean);
    };

    const discVal = cleanPriceStr(deal.discount_price) || 200;
    const origVal = cleanPriceStr(deal.original_price) || (discVal * 1.4);
    
    const labels = [];
    const dataPoints = [];
    const now = new Date();
    
    for (let i = 30; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(now.getDate() - i);
        labels.push(d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' }));
        
        let price = origVal;
        if (i === 0) {
            price = discVal;
        } else if (i <= 3) {
            const step = (origVal - discVal) / 3;
            price = origVal - (step * (4 - i)) + (Math.random() * (discVal * 0.03));
        } else {
            price = origVal * (0.95 + Math.random() * 0.08);
        }
        
        if (price < discVal) price = discVal;
        dataPoints.push(Math.round(price));
    }
    
    const chartModal = document.getElementById('chart-modal');
    document.getElementById('chart-modal-title').textContent = `${deal.title} — Fiyat Değişim Grafiği`;
    chartModal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    const ctx = document.getElementById('priceHistoryChart').getContext('2d');
    if (priceChartInstance) {
        priceChartInstance.destroy();
    }
    
    priceChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Fiyat (TL)',
                data: dataPoints,
                borderColor: '#d46a53',
                backgroundColor: 'rgba(212, 106, 83, 0.1)',
                borderWidth: 3,
                tension: 0.3,
                fill: true,
                pointRadius: function(context) {
                    const idx = context.dataIndex;
                    return (idx === labels.length - 1 || idx === labels.length - 4) ? 5 : 0;
                },
                pointBackgroundColor: '#d46a53'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(212, 106, 83, 0.05)' },
                    ticks: {
                        color: '#7c655d',
                        callback: function(value) { return value + ' TL'; }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#7c655d',
                        maxTicksLimit: 7
                    }
                }
            }
        }
    });
}
window.showPriceHistory = showPriceHistory;

function closeChartModal() {
    document.getElementById('chart-modal').classList.remove('active');
    document.body.style.overflow = '';
}
document.getElementById('chart-modal-close').addEventListener('click', closeChartModal);
document.getElementById('chart-modal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('chart-modal')) {
        closeChartModal();
    }
});

// Initialize
loadData();

