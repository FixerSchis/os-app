$(document).ready(function() {
    // Initialize select2 for all select elements
    $('.select2').select2({
        width: '100%'
    });

    // Initialize select2 for cybernetics
    $('.select2-cybernetics').select2({
        width: '100%',
        placeholder: 'Select cybernetics...',
        allowClear: true
    });

    // Initialize samples Select2
    $('#samples').select2({
        width: '100%',
        placeholder: 'Select samples...',
        allowClear: true
    });

    // Initialize sample tags Select2
    let currentTagInput = '';
    $('#sample_tags').select2({
        width: '100%',
        placeholder: 'Select or type tags...',
        allowClear: true,
        tags: true,
        createTag: function(params) {
            currentTagInput = params.term;
            return {
                id: params.term,
                text: params.term,
                newTag: true
            };
        }
    }).on('select2:select', function(e) {
        if (e.params.data.newTag) {
            currentTagInput = '';
        }
    }).on('select2:unselecting', function(e) {
        if (currentTagInput && currentTagInput.trim()) {
            e.preventDefault();
            const $select = $(this);
            const currentTags = $select.val() || [];
            if (!currentTags.includes(currentTagInput.trim())) {
                currentTags.push(currentTagInput.trim());
                $select.val(currentTags).trigger('change');
            }
            currentTagInput = '';
        }
    }).on('select2:close', function(e) {
        if (currentTagInput && currentTagInput.trim()) {
            const $select = $(this);
            const currentTags = $select.val() || [];
            if (!currentTags.includes(currentTagInput.trim())) {
                currentTags.push(currentTagInput.trim());
                $select.val(currentTags).trigger('change');
            }
            currentTagInput = '';
        }
    }).on('select2:search', function(e) {
        currentTagInput = e.target.value;
    });

    // Handle exotic substance selection
    $('#exotics').on('change', function() {
        const selectedIds = $(this).val() || [];
        $('.exotic-amount').hide();
        selectedIds.forEach(function(id) {
            $(`.exotic-amount[data-exotic-id="${id}"]`).show();
        });
    }).trigger('change');

    // Handle condition selection
    $('#conditions').on('change', function() {
        const selectedIds = $(this).val() || [];
        $('.condition-duration').hide();
        selectedIds.forEach(function(id) {
            $(`.condition-duration[data-condition-id="${id}"]`).show();
        });
    }).trigger('change');

    // Handle new sample option
    $('#samples').on('change', function() {
        const selected = $(this).val() || [];
        if (selected.includes('new')) {
            $('#newSampleModal').modal('show');
            // Remove 'new' from selection
            $(this).val(selected.filter(val => val !== 'new'));
        }
    });

    // Handle new sample form submission
    $('#saveNewSample').on('click', function() {
        const name = $('#sample_name').val();
        const type = $('#sample_type').val();
        const description = $('#sample_description').val();
        const tags = $('#sample_tags').val() || [];

        if (!name || !type) {
            alert('Name and type are required');
            return;
        }

        // Create new sample via AJAX
        $.ajax({
            url: '/samples/create',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                name: name,
                type: type,
                description: description,
                tags: tags
            }),
            success: function(response) {
                // Add new sample to select
                const option = new Option(response.name, response.id, true, true);
                $('#samples').append(option).trigger('change');
                $('#newSampleModal').modal('hide');
                $('#newSampleForm')[0].reset();
                $('#sample_tags').val(null).trigger('change');
            },
            error: function(xhr) {
                console.error('Failed to create sample:', xhr.responseText);
                alert('Failed to create new sample: ' + (xhr.responseJSON?.error || 'Unknown error'));
            }
        });
    });

    // Initialize with any pre-selected values
    if ($('#exotics').val()) {
        $('#exotics').trigger('change');
    }
    if ($('#conditions').val()) {
        $('#conditions').trigger('change');
    }
});