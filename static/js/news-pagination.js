(function () {
    function setLoading(section, loading) {
        section.classList.toggle('is-loading', loading);
    }

    function getSectionParts(section) {
        return {
            cards: section.querySelector('[data-category-cards], [data-latest-cards]'),
            pagination: section.querySelector('[data-category-pagination], [data-latest-pagination]'),
        };
    }

    async function loadPage(section, page) {
        const endpoint = section.dataset.endpoint;
        const { cards, pagination } = getSectionParts(section);
        if (!endpoint || !cards || !pagination) return;

        setLoading(section, true);
        try {
            const response = await fetch(`${endpoint}?page=${encodeURIComponent(page)}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!response.ok) throw new Error('Pagination request failed');
            const data = await response.json();
            cards.innerHTML = data.cards_html;
            pagination.innerHTML = data.pagination_html;
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(section, false);
        }
    }

    document.addEventListener('click', function (event) {
        const button = event.target.closest('[data-category-section] .pager-btn, [data-latest-section] .pager-btn');
        if (!button || button.disabled) return;
        const section = button.closest('[data-category-section], [data-latest-section]');
        if (!section) return;
        event.preventDefault();
        loadPage(section, button.dataset.page);
    });
})();
