$(function() {
    $('#wiki-tags').select2({
        tags: true,
        tokenSeparators: [','],
        ajax: {
            url: '/wiki/tags',
            dataType: 'json',
            delay: 200,
            data: function(params) {
                return { q: params.term };
            },
            processResults: function(data) {
                return { results: data.results };
            },
            cache: true
        },
        createTag: function(params) {
            return {
                id: params.term,
                text: params.term,
                newTag: true
            };
        },
        placeholder: 'Select or create tags',
        width: '100%'
    });
});
