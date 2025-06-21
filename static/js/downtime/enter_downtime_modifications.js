$(document).ready(function() {
    // Initialize Select2 for all modification selects
    $('.mod-select').select2({
        width: '100%',
        placeholder: 'Select a modification',
        allowClear: true,
        theme: 'bootstrap4'
    });

    // On form submit, ensure all .mod-select values are included
    $('#downtime-form').on('submit', function(e) {
        // Remove any previous modifications[] hidden inputs
        $('input[name="modifications[]"]').remove();

        // Gather all selected mod_learning[]
        $('.mod-select').each(function() {
            const val = $(this).val();
            if (val) {
                const jsonValue = JSON.stringify({ mod_id: val, type: 'learning' });
                const htmlSafeValue = jsonValue.replace(/"/g, '&quot;');
                $('#downtime-form').append(`<input type="hidden" name="modifications[]" value="${htmlSafeValue}">`);
            }
            // Disable original select so only modifications[] is submitted
            $(this).prop('disabled', true);
        });

        // Gather all checked forget_mods[]
        $('input[type="checkbox"][name="forget_mods[]"]:checked').each(function() {
            const val = $(this).val();
            if (val) {
                const jsonValue = JSON.stringify({ mod_id: val, type: 'forgetting' });
                const htmlSafeValue = jsonValue.replace(/"/g, '&quot;');
                $('#downtime-form').append(`<input type="hidden" name="modifications[]" value="${htmlSafeValue}">`);
            }
            // Disable original checkbox so only modifications[] is submitted
            $(this).prop('disabled', true);
        });
    });
});
