function formatDate(dateStr) {
    if (!dateStr) return '';

    const [year, month, day] = dateStr.split('-').map(Number);

    const date = new Date(year, month - 1, day);

    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function createCard(item) {
    const card = document.createElement('div');
    card.className = 'card';

    const watchedHTML = item.watched
        ? `<p class="card-date">Finished Watching:<br>${formatDate(item.watched)}</p>`
        : '';

    card.innerHTML = `
        <div class="poster-container">
            <img src="${item.poster}" loading=lazy alt="${item.title} Poster">
        </div>
        <div class="card-content">
            <h3 class="card-title">${item.title}</h3>
            <p class="card-rating">${item.rating}</p>
            ${watchedHTML}
        </div>
    `;

    card.onclick = () => openModal(item.title, item.review);
    return card;
}

// ==================== SORTING LOGIC ====================
function extractRatingScore(ratingStr) {
    const match = ratingStr.match(/\((\d+(\.\d+)?)\/10\)/);
    return match ? parseFloat(match[1]) : 0;
}

function sortCategoryData(data) {
    return data.sort((a, b) => {
        // Highest rating first
        const scoreA = extractRatingScore(a.rating);
        const scoreB = extractRatingScore(b.rating);
        if (scoreA !== scoreB) return scoreB - scoreA;

        // Then lowest weight
        const weightA = a.weight ?? 9999;
        const weightB = b.weight ?? 9999;
        if (weightA !== weightB) return weightA - weightB;

        // Then newest watch date
        const dateA = a.watched ? new Date(a.watched) : new Date(0);
        const dateB = b.watched ? new Date(b.watched) : new Date(0);
        return dateB - dateA;   // newest on top
    });
}

// ==================== COLLAPSIBLE UNRANKED ====================
function setupUnrankedToggle() {
    const header = document.getElementById('unranked-header');
    const grid = document.getElementById('unranked-tier');

    if (!header || !grid) return;

    header.addEventListener('click', function() {
        const isCollapsed = grid.classList.contains('collapsed');

        if (isCollapsed) {
            // --- OPENING ---
            grid.style.display = 'grid';
            grid.classList.remove('collapsed');
            header.textContent = header.textContent.replace('▶', '▼');
        } else {
            // --- CLOSING ---
            grid.classList.add('collapsed');
            header.textContent = header.textContent.replace('▼', '▶');

            setTimeout(() => {
                if (grid.classList.contains('collapsed')) {
                    grid.style.display = 'none';
                }
            }, 400);
        }
    });
}

// ==================== SEARCH BAR ====================
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        document.querySelectorAll('.card').forEach(card => {
            const title = card.querySelector('.card-title').textContent.toLowerCase();
            card.style.display = title.includes(searchTerm) ? '' : 'none';
        });
    });
}

// ==================== POPULATE CARDS ====================
function populateCards() {
    if (!window.categoryData) {
        console.error('Failed to load category data. Check that data.yml exists and is valid.');
        return;
    }

    const totalCount = document.getElementById('total-count');
    const libraryCount = document.getElementById('library-count');

    if (totalCount) {
        totalCount.textContent = window.categoryData.length;
    }

    if (libraryCount) {
        const countableItems = window.categoryData.filter(item => item.count !== false);
        libraryCount.textContent = countableItems.length;
    }

    const sortedData = sortCategoryData(window.categoryData);

    sortedData.forEach(item => {
        const tierGrid = document.getElementById(`${item.tier}-tier`);
        if (tierGrid) tierGrid.appendChild(createCard(item));
    });

    setupUnrankedToggle();
    setupSearch();
}

// ==================== MODAL ====================
const modal = document.getElementById('reviewModal');
const modalTitle = document.getElementById('modalTitle');
const modalReview = document.getElementById('modalReview');
const closeBtn = document.querySelector('.close');

function openModal(title, review) {
    modalTitle.textContent = title + ' Review';
    modalReview.innerHTML = review.replace(/\n/g, '<br>');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

function closeModal() {
    modal.classList.remove('show');

    // Wait for animation to finish before hiding
    setTimeout(() => {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }, 300);
}

closeBtn.onclick = closeModal;

window.onclick = (event) => {
    if (event.target === modal) closeModal();
};

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal.classList.contains('show')) {
        closeModal();
    }
});

// ==================== BACK TO TOP BUTTON ====================
const backToTopBtn = document.getElementById('backToTop');
if (backToTopBtn) {
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });

    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}