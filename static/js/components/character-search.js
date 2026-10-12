function applyCharacterSearchDarkMode() {
    const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
    if (!isDarkMode) {
        return;
    }
    $('.select2-container--bootstrap-5').addClass('select2-dark');
    $('.select2-dropdown').addClass('select2-dark');
}

function initCharacterSearch(select) {
    const $select = $(select);
    if ($select.data('characterSearchReady')) {
        return;
    }
    $select.data('characterSearchReady', true);

    const targetSelector = select.dataset.targetInput;
    $select.select2({
        theme: 'bootstrap-5',
        width: '100%',
        allowClear: true,
        placeholder: select.dataset.placeholder || 'Search by character name, user name, or ID',
        minimumInputLength: 2,
        ajax: {
            url: select.dataset.searchUrl,
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return { q: params.term };
            },
            processResults: function(data) {
                return {
                    results: (data.items || []).map(function(item) {
                        return {
                            id: item.player_reference,
                            text: item.text
                        };
                    })
                };
            },
            cache: true
        }
    }).on('select2:select', function(e) {
        const input = document.querySelector(targetSelector);
        if (!input) {
            return;
        }
        input.value = e.params.data.id;
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }).on('select2:clear', function() {
        const input = document.querySelector(targetSelector);
        if (!input) {
            return;
        }
        input.value = '';
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }).on('select2:open', applyCharacterSearchDarkMode);
}

function initVisibleCharacterSearches() {
    document.querySelectorAll('[data-character-search]').forEach(function(select) {
        const section = select.closest('[data-character-search-section]');
        if (!section || section.style.display !== 'none') {
            initCharacterSearch(select);
        }
    });
}

window.initCharacterSearch = initVisibleCharacterSearches;

document.addEventListener('DOMContentLoaded', initVisibleCharacterSearches);
