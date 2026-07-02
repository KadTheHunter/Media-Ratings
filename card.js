/**
 * @typedef {Object} MediaItem
 * @property {string} [title]
 * @property {string} [rating]
 * @property {string} [review]
 * @property {string} [poster]
 * @property {string} [tier]
 * @property {boolean} [count]
 * @property {number} [weight]
 * @property {string} [watched]
 * @property {string} [artist]
 * @property {string} [series]
 * @property {number} [series_order]
 */

/**
 * Converts a YYYY-MM-DD string into a localized date string.
 * @param {string} dateStr - The date string to format (e.g., "2023-10-25")
 * @returns {string} The formatted date (e.g., "Oct 25, 2023")
 */
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

/**
 * Creates a DOM element for a media card.
 * @param {MediaItem} item - The media data object
 * @param {number} [index=0] - The global index of the card (used for eager/lazy loading)
 * @param {number} [eagerThreshold=8] - Number of cards to load eagerly
 * @returns {HTMLElement} The constructed article element
 */
function createCard(item, index = 0, eagerThreshold = 8) {
    const card = document.createElement('article');

    const isMusic = window.currentCategory === 'music';
    const isBooks = window.currentCategory === 'books';
    if (isMusic) {
        card.className = 'card music';
    } else if (isBooks) {
        card.className = 'card books';
    } else {
        card.className = 'card';
    }

    let metadataHTML = '';
    if (isMusic && item.artist) {
        metadataHTML = `<p class="card-date">Artist: ${item.artist}</p>`;
    } else if (isBooks && item.series) {
        metadataHTML = `<p class="card-date">${item.series} #${item.series_order}</p>`;
    } else if (!isMusic && !isBooks && item.watched) {
        metadataHTML = `<p class="card-date">Finished Watching:<br>${formatDate(item.watched)}</p>`;
    }

    const loadingAttr = index < eagerThreshold ? 'eager' : 'lazy';
    const imgWidth = 200;
    const imgHeight = isMusic ? 200 : 300;

    card.innerHTML = `
        <div class="poster-container">
            <img src="${item.poster}" 
                 loading="${loadingAttr}" 
                 width="${imgWidth}" 
                 height="${imgHeight}"
                 alt="${item.title} Poster">
        </div>
        <div class="card-content">
            <h3 class="card-title">${item.title}</h3>
            <p class="card-rating">${item.rating}</p>
            ${metadataHTML}
        </div>
    `;

    card.onclick = () => openModal(item.title, item.review);
    return card;
}

// ==================== SORTING LOGIC ====================

/**
 * Extracts the numerical score from a rating string.
 * @param {string} ratingStr - The rating string (e.g., "☆☆☆☆☆ (9/10)")
 * @returns {number} The numerical score (e.g., 9)
 */
function extractRatingScore(ratingStr) {
    const match = ratingStr.match(/\((\d+(\.\d+)?)\/10\)/);
    return match ? parseFloat(match[1]) : 0;
}

/**
 * Sorts the category data by Rating (desc), Weight (asc), and Watch Date (desc).
 * @param {MediaItem[]} data - The array of media items
 * @returns {MediaItem[]} A new, sorted array of media items
 */
function sortCategoryData(data) {
    return [...data].sort((a, b) => {
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

// ==================== COLLAPSIBLE TIERS ====================

/**
 * Initializes click listeners for all tier headers to toggle their grid visibility.
 * @returns {void}
 */
function setupCollapsibleTiers() {
    const tierHeaders = document.querySelectorAll('.tier-header');

    tierHeaders.forEach(header => {
        header.addEventListener('click', function(e) {
            if (e.target.closest('a, button')) return;

            const gridId = this.id.replace('-header', '');
            const grid = document.getElementById(gridId);

            if (!grid) return;

            const isCollapsed = grid.classList.contains('collapsed');

            if (isCollapsed) {
                grid.classList.remove('collapsed');
                this.classList.remove('collapsed');
                setTimeout(() => {
                    grid.style.display = 'grid';
                }, 10);
            } else {
                grid.classList.add('collapsed');
                this.classList.add('collapsed');
                setTimeout(() => {
                    if (grid.classList.contains('collapsed')) {
                        grid.style.display = 'none';
                    }
                }, 300);
            }
        });
    });
}

// ==================== SEARCH BAR ====================

/**
 * Initializes the search input listener to filter cards and auto-expand unranked tiers.
 * @returns {void}
 */
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    const unrankedHeader = document.getElementById('unranked-header');
    const unrankedGrid = document.getElementById('unranked-tier');
    let wasCollapsed = false;
    let userManuallyOpened = false;

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase().trim();
        let totalVisible = 0;
        let unrankedHasMatches = false;

        document.querySelectorAll('.card').forEach(card => {
            const title = card.querySelector('.card-title').textContent.toLowerCase();
            const matches = searchTerm === '' || title.includes(searchTerm);
            card.style.display = matches ? '' : 'none';
            if (matches) totalVisible++;
        });

        if (unrankedGrid && unrankedHeader) {
            const unrankedCards = unrankedGrid.querySelectorAll('.card');
            const visibleUnranked = Array.from(unrankedCards).filter(card =>
                card.style.display !== 'none'
            ).length;

            unrankedHasMatches = visibleUnranked > 0;
            const isCollapsed = unrankedGrid.classList.contains('collapsed');

            if (searchTerm !== '' && unrankedHasMatches && isCollapsed && !userManuallyOpened) {
                wasCollapsed = true;
                unrankedGrid.style.display = 'grid';
                unrankedGrid.classList.remove('collapsed');
                unrankedHeader.textContent = unrankedHeader.textContent.replace('▶', '▼');
            } else if (searchTerm === '' && wasCollapsed && !userManuallyOpened) {
                unrankedGrid.classList.add('collapsed');
                unrankedHeader.textContent = unrankedHeader.textContent.replace('▼', '▶');
                setTimeout(() => {
                    if (unrankedGrid.classList.contains('collapsed')) {
                        unrankedGrid.style.display = 'none';
                    }
                }, 400);
            }
        }

        const totalCount = document.getElementById('total-count');
        if (totalCount) {
            if (searchTerm === '') {
                totalCount.textContent = window.categoryData.length;
            } else {
                totalCount.textContent = totalVisible;
            }
        }
    });

    if (unrankedHeader && unrankedGrid) {
        unrankedHeader.addEventListener('click', () => {
            const isCollapsed = unrankedGrid.classList.contains('collapsed');
            if (isCollapsed) {
                userManuallyOpened = true;
                wasCollapsed = false;
            } else {
                userManuallyOpened = false;
            }
        });
    }
}

// ==================== POPULATE CARDS ====================

/**
 * Calculates how many cards are currently visible in the viewport.
 * @returns {number} The estimated number of visible cards
 */
function getVisibleCardCount() {
    const grid = document.querySelector('.grid');
    if (!grid) return 8;

    const gridStyle = getComputedStyle(grid);
    const columns = gridStyle.gridTemplateColumns.split(' ').length;
    const viewportHeight = window.innerHeight;
    const gridTop = grid.getBoundingClientRect().top;
    const availableHeight = viewportHeight - gridTop;

    const cardHeight = 300;
    const visibleRows = Math.ceil(availableHeight / cardHeight);

    return columns * visibleRows;
}

/**
 * Loads data, sorts it, and populates the DOM with cards.
 * @returns {void}
 */
function populateCards() {
    if (!window.categoryData) {
        console.error('Failed to load category data. Check that data.yml exists and is valid.');
        return;
    }

    const totalCount = document.getElementById('total-count');
    const libraryCount = document.getElementById('library-count');

    if (totalCount) {
        const ratedItems = window.categoryData.filter(item => item.tier !== 'unranked');
        totalCount.textContent = ratedItems.length;
    }

    if (libraryCount) {
        const libraryItems = window.categoryData.filter(item => item.count !== false);
        libraryCount.textContent = libraryItems.length;
    }

    const sortedData = sortCategoryData(window.categoryData);
    const eagerLoadCount = getVisibleCardCount();

    let globalIndex = 0;
    sortedData.forEach(item => {
        const tierGrid = document.getElementById(`${item.tier}-tier`);
        if (tierGrid) {
            tierGrid.appendChild(createCard(item, globalIndex, eagerLoadCount));
            globalIndex++;
        }
    });

    setupCollapsibleTiers();
    setupSearch();
}

// ==================== MODAL ====================
const modal = document.getElementById('reviewModal');
const modalTitle = document.getElementById('modalTitle');
const modalReview = document.getElementById('modalReview');
const closeBtn = document.querySelector('.close');

/**
 * Opens the review modal and populates it with data.
 * @param {string} title - The title of the media
 * @param {string} review - The review text
 * @returns {void}
 */
function openModal(title, review) {
    modalTitle.textContent = title + ' Review';
    modalReview.innerHTML = review.replace(/\n/g, '<br>');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

/**
 * Closes the review modal and restores body scrolling.
 * @returns {void}
 */
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