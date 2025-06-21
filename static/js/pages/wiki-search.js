$(function() {
    var $input = $('#wiki-search-input');
    var $dropdown = $('#wiki-search-dropdown');
    var typingTimer;
    var lastResults = [];
    var highlightedIndex = -1;

    function renderDropdown(results) {
        $dropdown.empty();
        if (!results.length) {
            $dropdown.hide();
            highlightedIndex = -1;
            return;
        }
        results.forEach(function(result, i) {
            var tags = result.tags && result.tags.length ?
                ' <span style="font-size:0.9em; color:#888;">[' + result.tags.join(', ') + ']</span>' : '';
            var item = $('<a class="dropdown-item" href="/wiki/' + result.slug + '">' +
                $('<div>').text(result.title).html() + tags + '</a>');
            if (i === highlightedIndex) item.addClass('active');
            $dropdown.append(item);
        });
        $dropdown.show();
    }

    $input.on('input', function() {
        clearTimeout(typingTimer);
        var val = $input.val();
        highlightedIndex = -1;
        if (!val) {
            $dropdown.hide();
            return;
        }
        typingTimer = setTimeout(function() {
            $.getJSON('/wiki/live_search', {q: val}, function(results) {
                lastResults = results;
                renderDropdown(results);
            });
        }, 200);
    });

    $input.on('focus', function() {
        if (lastResults.length) $dropdown.show();
    });
    $input.on('blur', function() {
        setTimeout(function() { $dropdown.hide(); }, 200);
    });

    $dropdown.on('mousedown', 'a', function(e) {
        window.location.href = $(this).attr('href');
        e.preventDefault();
    });

    $input.on('keydown', function(e) {
        if (!$dropdown.is(':visible') || !lastResults.length) return;
        if (e.key === 'ArrowDown') {
            highlightedIndex = (highlightedIndex + 1) % lastResults.length;
            renderDropdown(lastResults);
            e.preventDefault();
        } else if (e.key === 'ArrowUp') {
            highlightedIndex = (highlightedIndex - 1 + lastResults.length) % lastResults.length;
            renderDropdown(lastResults);
            e.preventDefault();
        } else if (e.key === 'Enter') {
            if (highlightedIndex >= 0 && highlightedIndex < lastResults.length) {
                window.location.href = '/wiki/' + lastResults[highlightedIndex].slug;
                e.preventDefault();
            }
        }
    });

    // On form submit, just let the form submit as normal (for full search)
}); 