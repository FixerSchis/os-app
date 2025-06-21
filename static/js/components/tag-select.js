$(document).ready(function() {
    // Tags select2 with AJAX and tag creation
    $('.select2-tags').select2({
        ajax: {
            url: '/character-tags/search',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(function(item) {
                        return {
                            id: item.id,
                            text: item.name
                        };
                    })
                };
            },
            cache: true
        },
        placeholder: 'Search for character tags...',
        minimumInputLength: 1,
        allowClear: true,
        width: '100%',
        theme: 'default',
        tags: true,
        tokenSeparators: [',', ' '],
        createTag: function(params) {
            return {
                id: params.term,
                text: params.term,
                newTag: true
            };
        }
    });

    // Cybernetics select2 as a plain multi-select
    $('.select2-cybernetics').select2({
        placeholder: 'Select cybernetics...',
        allowClear: true,
        width: '100%',
        theme: 'default',
        tags: false // No tag creation
    });
});
