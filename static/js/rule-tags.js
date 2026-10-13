function initRuleTagSelect(element) {
    var $el = $(element);
    if ($el.hasClass('select2-hidden-accessible')) {
        return;
    }
    $el.select2({
        theme: 'bootstrap-5',
        width: '100%',
        tags: true,
        placeholder: 'Select or add a tag',
        allowClear: true,
        ajax: {
            url: '/db/conditions/tags',
            dataType: 'json',
            delay: 200,
            data: function(params) {
                return { q: params.term || '' };
            },
            processResults: function(data) {
                return { results: data.results };
            }
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

function initRuleTagSelects(root) {
    var scope = root ? $(root) : $(document);
    scope.find('.rule-tag-select').each(function() {
        initRuleTagSelect(this);
    });
}
