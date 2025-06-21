function initializeWikiPageSelect(inputId, placeholder) {
    console.log('Initializing Select2 for', '#' + inputId);
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
                console.log('Select2 wiki AJAX data:', data);
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