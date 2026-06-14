// State Variables
let allDeals = [];
let searchQuery = '';
let currentStore = 'all';

// DOM Elements
const lastUpdatedBadge = document.getElementById('last-updated');
const searchInput = document.getElementById('search-input');
const filterBtns = document.querySelectorAll('.store-filters .filter-btn');
const dealsFeed = document.getElementById('deals-feed');

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
        
        row.innerHTML = `
            <div class="deal-img-container">
                <img src="${deal.image_url}" alt="${deal.title}" class="deal-img" loading="lazy">
                <span class="discount-badge">${deal.discount_rate}</span>
            </div>
            <div class="deal-info-col">
                <div class="deal-meta">
                    <span class="source-badge" data-source="${deal.source}">${deal.source}</span>
                </div>
                <h3 class="deal-title">${deal.title}</h3>
                <p class="deal-description">${deal.description}</p>
            </div>
            <div class="deal-action-col">
                <div class="pricing-info">
                    <span class="orig-price">${deal.original_price}</span>
                    <span class="disc-price">${deal.discount_price}</span>
                </div>
                <a href="${deal.affiliate_link}" target="_blank" class="deal-btn">
                    Fırsatı Yakala <i class="fa-solid fa-arrow-up-right-from-square"></i>
                </a>
            </div>
        `;
        dealsFeed.appendChild(row);
    });
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

// Initialize
loadData();
