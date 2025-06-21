function initializeWikiPageSelect(inputId, placeholder) {
    $('#' + inputId).select2({
        tags: true,
        placeholder: placeholder,
        allowClear: true,
        width: '100%',
        theme: 'bootstrap-5',
        ajax: {
            url: '/wiki/_internal_pages',
            dataType: 'json',
            delay: 250,
            processResults: function (data) {
                return { results: data };
            },
            cache: true
        },
        createTag: function(params) {
            var term = $.trim(params.term);
            if (term === '') {
                return null;
            }
            return {
                id: term,
                text: term,
                newTag: true
            };
        }
    });
}
